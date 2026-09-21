"""
Gera uma base SINTÉTICA de colaboradores e líderes para estudo.

Nenhum dado real: nomes e matrículas são fictícios. A base inclui, de
propósito, os problemas de cadastro mais comuns no RH, para que os alertas
do script possam ser observados.

Uso (a partir da raiz do projeto):
    python data/gerar_dados.py
"""

import random
from pathlib import Path

import pandas as pd

SEED = 42
SAIDA = Path(__file__).parent / "colaboradores.csv"

PRIMEIROS_NOMES = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela", "Hugo",
                   "Isabela", "João", "Karen", "Lucas", "Marina", "Nicolas", "Olívia",
                   "Pedro", "Rafaela", "Sérgio", "Tatiane", "Vinícius"]
SOBRENOMES = ["Almeida", "Barbosa", "Cardoso", "Dias", "Esteves", "Ferreira", "Gomes",
              "Lima", "Martins", "Nogueira", "Oliveira", "Pereira", "Rocha", "Souza"]
AREAS = ["Comercial", "Operações", "Tecnologia"]


class GeradorOrganizacao:
    """Cria colaboradores e guarda as linhas da base."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.linhas: list[dict] = []

    def novo(self, cargo: str, area: str, lider: str | None) -> str:
        matricula = f"M{len(self.linhas) + 1:05d}"
        nome = f"{self.rng.choice(PRIMEIROS_NOMES)} {self.rng.choice(SOBRENOMES)}"
        self.linhas.append({"matricula": matricula, "nome": nome, "cargo": cargo,
                            "area": area, "matricula_lider": lider})
        return matricula

    def trocar_lider(self, matricula: str, novo_lider: str) -> None:
        for linha in self.linhas:
            if linha["matricula"] == matricula:
                linha["matricula_lider"] = novo_lider


def montar_estrutura(g: GeradorOrganizacao) -> dict:
    """Estrutura 'saudável', já com níveis pulados (algo normal no mundo real)."""
    rng = g.rng
    ref = {"presidente": g.novo("Presidente", "Presidência", None),
           "diretores": {}, "coordenadores": []}

    for area in AREAS:
        diretor = g.novo(f"Diretor de {area}", area, ref["presidente"])
        ref["diretores"][area] = diretor
        for _ in range(rng.randint(2, 3)):
            gerente = g.novo(f"Gerente de {area}", area, diretor)
            # Analistas sêniores ligados direto ao gerente (sem coordenador)
            for _ in range(rng.randint(1, 2)):
                g.novo(f"Analista Sênior de {area}", area, gerente)
            for _ in range(rng.randint(1, 3)):
                coord = g.novo(f"Coordenador de {area}", area, gerente)
                ref["coordenadores"].append(coord)
                for _ in range(rng.randint(1, 3)):
                    g.novo(f"Analista de {area}", area, coord)
                for _ in range(rng.randint(0, 2)):
                    sup = g.novo(f"Supervisor de {area}", area, coord)
                    for _ in range(rng.randint(3, 6)):
                        cargo = rng.choice(["Assistente", "Operador"])
                        g.novo(f"{cargo} de {area}", area, sup)
    return ref


def injetar_anomalias(g: GeradorOrganizacao, ref: dict) -> None:
    """Problemas típicos de cadastro, um de cada tipo."""
    # 1. Líder fora da base (ex.: líder já desligado)
    g.novo("Analista de Compras", "Operações", "M99999")

    # 2. Ciclo: A lidera B e B lidera A
    a = g.novo("Coordenador de Projetos", "Tecnologia", None)
    b = g.novo("Gerente de Projetos", "Tecnologia", a)
    g.trocar_lider(a, b)
    g.novo("Analista de Projetos", "Tecnologia", a)

    # 3. Líder com cargo fora da régua de níveis
    head = g.novo("Head de Produto", "Tecnologia", ref["presidente"])
    g.novo("Analista de Produto", "Tecnologia", head)

    # 4. Hierarquia invertida: gerente abaixo de coordenador
    g.novo("Gerente de Contas", "Comercial", ref["coordenadores"][0])

    # 5. Nível repetido: gerente abaixo de gerente sênior
    senior = g.novo("Gerente Sênior de Marketing", "Comercial", ref["diretores"]["Comercial"])
    gerente = g.novo("Gerente de Marketing", "Comercial", senior)
    g.novo("Analista de Marketing", "Comercial", gerente)


def main() -> None:
    g = GeradorOrganizacao(SEED)
    ref = montar_estrutura(g)
    injetar_anomalias(g, ref)

    # Embaralha: bases reais não vêm ordenadas da raiz para as folhas
    df = pd.DataFrame(g.linhas).sample(frac=1, random_state=SEED).reset_index(drop=True)
    df.to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(f"{len(df)} colaboradores gerados em {SAIDA}")


if __name__ == "__main__":
    main()
