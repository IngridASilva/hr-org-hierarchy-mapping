"""Testes da rotina de desdobramento. Rode com: pytest"""

import pandas as pd
import pytest

from src.hierarquia import (NIVEIS_PADRAO, classificar_nivel, compilar_padroes,
                            desdobrar_hierarquia)

COLUNAS = ["matricula", "nome", "cargo", "matricula_lider"]


def base(linhas):
    return pd.DataFrame(linhas, columns=COLUNAS)


def linha(resultado, matricula):
    return resultado.set_index("matricula").loc[matricula]


@pytest.fixture
def exemplo():
    return base([
        ("M001", "Ana", "Diretora Comercial", None),
        ("M002", "Bruno", "Gerente de Vendas", "M001"),
        ("M003", "Carla", "Coordenadora de Vendas", "M002"),
        ("M004", "Diego", "Analista de Vendas", "M003"),
        ("M005", "Elisa", "Analista de Pricing", "M002"),
    ])


# --- Casos normais ---------------------------------------------------------

def test_cadeia_completa(exemplo):
    d = linha(desdobrar_hierarquia(exemplo), "M004")
    assert (d["Diretor_nome"], d["Gerente_nome"], d["Coordenador_nome"]) == ("Ana", "Bruno", "Carla")
    assert pd.isna(d["Supervisor_id"])
    assert pd.isna(d["alertas"])
    assert d["caminho_hierarquico"] == "M001 > M002 > M003 > M004"


def test_nivel_pulado_fica_nulo(exemplo):
    e = linha(desdobrar_hierarquia(exemplo), "M005")
    assert e["Gerente_nome"] == "Bruno"
    assert pd.isna(e["Coordenador_id"])


def test_topo_sem_lideres(exemplo):
    topo = linha(desdobrar_hierarquia(exemplo), "M001")
    assert topo["qtd_niveis_acima"] == 0
    assert pd.isna(topo["Diretor_id"])


def test_incluir_proprio(exemplo):
    c = linha(desdobrar_hierarquia(exemplo, incluir_proprio=True), "M003")
    assert c["Coordenador_nome"] == "Carla"


def test_matriculas_numericas_com_nulo():
    df = pd.DataFrame({"matricula": [1001, 1002], "nome": ["A", "B"],
                       "cargo": ["Gerente", "Analista"], "matricula_lider": [None, 1001]})
    assert desdobrar_hierarquia(df).loc[1, "Gerente_id"] == "1001"


# --- Alertas de qualidade --------------------------------------------------

def test_ciclo():
    df = base([("A", "a", "Gerente X", "B"), ("B", "b", "Gerente Y", "A"),
               ("C", "c", "Analista", "A")])
    assert "CICLO" in linha(desdobrar_hierarquia(df), "C")["alertas"]


def test_lider_fora_da_base():
    df = base([("A", "a", "Analista", "ZZZ")])
    assert linha(desdobrar_hierarquia(df), "A")["alertas"] == "LIDER_FORA_DA_BASE"


def test_nivel_repetido_mantem_mais_proximo():
    df = base([("G1", "g1", "Gerente Sênior", None), ("G2", "g2", "Gerente", "G1"),
               ("X", "x", "Analista", "G2")])
    x = linha(desdobrar_hierarquia(df), "X")
    assert x["Gerente_id"] == "G2"
    assert "NIVEL_REPETIDO" in x["alertas"]


def test_hierarquia_invertida():
    df = base([("C", "c", "Coordenador", None), ("G", "g", "Gerente", "C")])
    assert "HIERARQUIA_INVERTIDA" in linha(desdobrar_hierarquia(df), "G")["alertas"]


def test_lider_sem_nivel():
    df = base([("H", "h", "Head de Dados", None), ("A", "a", "Analista", "H")])
    assert linha(desdobrar_hierarquia(df), "A")["alertas"] == "LIDER_SEM_NIVEL"


def test_matricula_duplicada_falha():
    df = base([("A", "a", "Analista", None), ("A", "a2", "Analista", None)])
    with pytest.raises(ValueError, match="duplicadas"):
        desdobrar_hierarquia(df)


# --- Classificação de cargos -----------------------------------------------

@pytest.mark.parametrize("cargo, esperado", [
    ("SUPERVISORA DE LOJA", "Supervisor"),
    ("Diretor e Gerente Geral", "Diretor"),
    ("CEO", "Presidente"),
    ("Analista de Gerenciamento de Projetos", None),
    ("Assistente de Coordenação", None),
    (None, None),
])
def test_classificar_nivel(cargo, esperado):
    assert classificar_nivel(cargo, compilar_padroes(NIVEIS_PADRAO)) == esperado
