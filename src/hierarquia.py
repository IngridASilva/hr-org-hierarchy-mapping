"""
Desdobramento da cadeia de liderança em colunas por nível hierárquico.

Recebe uma base no formato "colaborador -> líder imediato" (lista de adjacência)
e devolve, para cada colaborador, quem ocupa cada nível de liderança acima dele
(Presidente, Diretor, Gerente, Coordenador, Supervisor). Quando a cadeia não
passa por um nível, a coluna correspondente fica nula.

Uso via linha de comando (a partir da raiz do projeto):
    python -m src.hierarquia --entrada data/colaboradores.csv --saida saida/hierarquia.csv
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

# Níveis do TOPO para a BASE. A ordem importa: define a ordem das colunas de
# saída e é usada para detectar hierarquias invertidas.
# Cada nível lista as palavras-chave que o identificam no nome do cargo.
NIVEIS_PADRAO: dict[str, list[str]] = {
    "Presidente": ["presidente", "ceo"],
    "Diretor": ["diretor", "diretora"],
    "Gerente": ["gerente"],
    "Coordenador": ["coordenador", "coordenadora"],
    "Supervisor": ["supervisor", "supervisora"],
}

# Códigos de alerta de qualidade da cadeia (detalhes em docs/03_qualidade_de_dados.md)
ALERTA_CICLO = "CICLO"
ALERTA_LIDER_FORA = "LIDER_FORA_DA_BASE"
ALERTA_LIDER_SEM_NIVEL = "LIDER_SEM_NIVEL"
ALERTA_NIVEL_REPETIDO = "NIVEL_REPETIDO"
ALERTA_INVERTIDA = "HIERARQUIA_INVERTIDA"


# ---------------------------------------------------------------------------
# Padronização
# ---------------------------------------------------------------------------

def normalizar_texto(texto) -> str:
    """Minúsculas, sem acentos e sem espaços nas pontas."""
    if texto is None or pd.isna(texto):
        return ""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return sem_acento.lower().strip()


def normalizar_id(valor) -> str | None:
    """Padroniza matrículas como texto e trata vazios como None.

    Evita o problema clássico de '1001' vs '1001.0', que acontece quando a
    coluna de líder tem nulos e o pandas a converte para float.
    """
    if valor is None or pd.isna(valor):
        return None
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    texto = str(valor).strip()
    return texto or None


# ---------------------------------------------------------------------------
# Classificação de cargos
# ---------------------------------------------------------------------------

def compilar_padroes(niveis: dict[str, list[str]]) -> dict[str, re.Pattern]:
    r"""Transforma as palavras-chave de cada nível em uma regex.

    O limite de palavra (\b) evita falsos positivos, como 'Gerenciamento'
    casando com 'gerente'.
    """
    padroes = {}
    for nivel, palavras in niveis.items():
        alternativas = "|".join(re.escape(normalizar_texto(p)) for p in palavras)
        padroes[nivel] = re.compile(rf"\b(?:{alternativas})\b")
    return padroes


def classificar_nivel(cargo, padroes: dict[str, re.Pattern]) -> str | None:
    """Retorna o nível de liderança do cargo, ou None se não for um nível mapeado.

    Se o cargo casar com mais de um nível, vence o primeiro na ordem (o mais
    alto). Ex.: 'Diretor e Gerente Geral' -> 'Diretor'.
    """
    texto = normalizar_texto(cargo)
    for nivel, padrao in padroes.items():
        if padrao.search(texto):
            return nivel
    return None


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def validar_entrada(df: pd.DataFrame, col_id: str, col_lider: str, col_cargo: str) -> None:
    """Falha cedo quando a base não permite montar a hierarquia com segurança."""
    faltantes = [c for c in (col_id, col_lider, col_cargo) if c not in df.columns]
    if faltantes:
        raise KeyError(f"Colunas obrigatórias ausentes: {faltantes}")

    ids = df[col_id].map(normalizar_id)
    if ids.isna().any():
        raise ValueError(f"{int(ids.isna().sum())} linha(s) sem matrícula.")

    duplicadas = ids[ids.duplicated()].unique()
    if len(duplicadas) > 0:
        raise ValueError(
            f"Matrículas duplicadas (ex.: {list(duplicadas[:5])}). "
            "Garanta uma linha por colaborador antes de rodar (ex.: filtre o vínculo ativo)."
        )


# ---------------------------------------------------------------------------
# Travessia da árvore
# ---------------------------------------------------------------------------

def subir_cadeia(id_: str, mapa_lider: dict[str, str | None]) -> tuple[list[str], str | None]:
    """Sobe da pessoa até o topo da estrutura.

    Retorna:
        ancestrais: matrículas dos líderes, do imediato ao mais alto.
        problema:   None se chegou ao topo normalmente; ou o código de alerta
                    (CICLO / LIDER_FORA_DA_BASE) que interrompeu a subida.

    Usa um laço (e não recursão) para não esbarrar no limite de recursão do
    Python, e um conjunto de visitados para não entrar em loop infinito.
    """
    ancestrais: list[str] = []
    visitados = {id_}
    atual = id_

    while True:
        lider = mapa_lider[atual]
        if lider is None or lider == atual:  # topo: sem líder ou auto-referência
            return ancestrais, None
        if lider in visitados:               # A -> B -> A
            return ancestrais, ALERTA_CICLO
        if lider not in mapa_lider:          # líder desligado, terceiro, erro de digitação...
            return ancestrais, ALERTA_LIDER_FORA
        ancestrais.append(lider)
        visitados.add(lider)
        atual = lider


def _adicionar(alertas: list[str], codigo: str) -> None:
    if codigo not in alertas:
        alertas.append(codigo)


def _montar_linha(
    id_: str,
    mapa_lider: dict,
    nivel_por_id: dict,
    nome_por_id: dict | None,
    ordem: dict[str, int],
    incluir_proprio: bool,
) -> dict:
    """Monta as colunas de saída de um colaborador."""
    ancestrais, problema = subir_cadeia(id_, mapa_lider)
    alertas: list[str] = [problema] if problema else []

    # Estrutura vazia: todos os níveis começam nulos
    linha: dict = {}
    for nivel in ordem:
        linha[f"{nivel}_id"] = None
        if nome_por_id is not None:
            linha[f"{nivel}_nome"] = None

    # 1) Checagens de consistência ao longo da cadeia de líderes
    rank_anterior = ordem.get(nivel_por_id.get(id_))  # 0 = topo
    niveis_vistos: set[str] = set()
    for lider in ancestrais:
        nivel = nivel_por_id[lider]
        if nivel is None:
            _adicionar(alertas, ALERTA_LIDER_SEM_NIVEL)
            continue
        if nivel in niveis_vistos:
            _adicionar(alertas, ALERTA_NIVEL_REPETIDO)
        niveis_vistos.add(nivel)
        rank = ordem[nivel]
        if rank_anterior is not None and rank > rank_anterior:  # subiu e o nível "desceu"
            _adicionar(alertas, ALERTA_INVERTIDA)
        rank_anterior = rank

    # 2) Preenchimento: em caso de nível repetido, vence o MAIS PRÓXIMO
    candidatos = ([id_] if incluir_proprio else []) + ancestrais
    for pessoa in candidatos:
        nivel = nivel_por_id.get(pessoa)
        if nivel is None or linha[f"{nivel}_id"] is not None:
            continue
        linha[f"{nivel}_id"] = pessoa
        if nome_por_id is not None:
            linha[f"{nivel}_nome"] = nome_por_id.get(pessoa)

    # 3) Colunas auxiliares para organogramas e auditoria
    linha["qtd_niveis_acima"] = len(ancestrais)
    linha["caminho_hierarquico"] = " > ".join(list(reversed(ancestrais)) + [id_])
    linha["alertas"] = "; ".join(alertas) if alertas else None
    return linha


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def desdobrar_hierarquia(
    df: pd.DataFrame,
    col_id: str = "matricula",
    col_lider: str = "matricula_lider",
    col_cargo: str = "cargo",
    col_nome: str | None = "nome",
    niveis: dict[str, list[str]] | None = None,
    incluir_proprio: bool = False,
) -> pd.DataFrame:
    """Desdobra a cadeia de liderança em colunas por nível.

    Args:
        df: uma linha por colaborador, com matrícula, cargo e matrícula do líder imediato.
        col_id, col_lider, col_cargo: nomes das colunas de entrada.
        col_nome: coluna de nome (gera colunas '<Nivel>_nome'). Use None para omitir.
        niveis: dicionário {nível: [palavras-chave]} do topo para a base.
        incluir_proprio: se True, a própria pessoa ocupa a coluna do seu nível
            (útil em BI para filtrar "a gerente X e toda a equipe dela").

    Returns:
        O DataFrame original acrescido de '<Nivel>_id', '<Nivel>_nome',
        'qtd_niveis_acima', 'caminho_hierarquico' e 'alertas'.
    """
    niveis = niveis or NIVEIS_PADRAO
    validar_entrada(df, col_id, col_lider, col_cargo)
    if col_nome is not None and col_nome not in df.columns:
        col_nome = None

    padroes = compilar_padroes(niveis)
    ordem = {nivel: i for i, nivel in enumerate(niveis)}

    # Dicionários = consultas O(1) durante a travessia.
    # Compreensões de lista (e não Series.map) garantem None de verdade:
    # o pandas pode converter None em NaN, e NaN quebra as comparações.
    ids = [normalizar_id(v) for v in df[col_id]]
    mapa_lider = dict(zip(ids, [normalizar_id(v) for v in df[col_lider]]))
    nivel_por_id = dict(zip(ids, [classificar_nivel(c, padroes) for c in df[col_cargo]]))
    nome_por_id = dict(zip(ids, df[col_nome])) if col_nome else None

    registros = [
        _montar_linha(id_, mapa_lider, nivel_por_id, nome_por_id, ordem, incluir_proprio)
        for id_ in ids
    ]
    resultado = pd.DataFrame(registros, index=df.index)
    return pd.concat([df, resultado], axis=1)


def resumo_alertas(resultado: pd.DataFrame) -> pd.DataFrame:
    """Conta quantos colaboradores têm cada tipo de alerta."""
    serie = resultado["alertas"].dropna().str.split("; ").explode()
    return serie.value_counts().rename_axis("alerta").reset_index(name="qtd_colaboradores")


# ---------------------------------------------------------------------------
# Linha de comando
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Desdobra a hierarquia em colunas por nível.")
    parser.add_argument("--entrada", default="data/colaboradores.csv")
    parser.add_argument("--saida", default="saida/hierarquia.csv")
    parser.add_argument("--incluir-proprio", action="store_true",
                        help="A própria pessoa ocupa a coluna do seu nível.")
    args = parser.parse_args()

    # dtype=str: matrícula é identificador, não número (preserva zeros à esquerda)
    df = pd.read_csv(args.entrada, dtype=str)
    resultado = desdobrar_hierarquia(df, incluir_proprio=args.incluir_proprio)

    Path(args.saida).parent.mkdir(parents=True, exist_ok=True)
    # utf-8-sig: acentos abrem corretamente no Excel
    resultado.to_csv(args.saida, index=False, encoding="utf-8-sig")

    print(f"{len(resultado)} colaboradores processados -> {args.saida}")
    resumo = resumo_alertas(resultado)
    if resumo.empty:
        print("Nenhum alerta de qualidade.")
    else:
        print("\nAlertas de qualidade:")
        print(resumo.to_string(index=False))


if __name__ == "__main__":
    main()
