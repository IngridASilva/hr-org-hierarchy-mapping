# Mapeamento Hierárquico de RH

![testes](https://github.com/IngridASilva/hr-org-hierarchy-mapping/actions/workflows/testes.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

Rotina em Python que recebe uma lista de colaboradores com seus líderes imediatos e **desdobra a cadeia de liderança em colunas por nível** (Presidente, Diretor, Gerente, Coordenador, Supervisor). Níveis que a cadeia não atravessa ficam nulos. A saída é a base pronta para organogramas, filtros em BI e análises por liderança.

Além disso, a rotina funciona como uma **auditoria do cadastro**: ciclos, líderes inexistentes e hierarquias invertidas são sinalizados em vez de quebrar a execução.

## Exemplo

**Entrada** ([`examples/exemplo_entrada.csv`](examples/exemplo_entrada.csv))

| matricula | nome | cargo | matricula_lider |
|---|---|---|---|
| M001 | Ana | Diretora Comercial | |
| M002 | Bruno | Gerente de Vendas | M001 |
| M003 | Carla | Coordenadora de Vendas | M002 |
| M004 | Diego | Analista de Vendas | M003 |
| M005 | Elisa | Analista de Pricing | M002 |

**Saída** (colunas `_id` omitidas)

| matricula | Diretor_nome | Gerente_nome | Coordenador_nome | Supervisor_nome | caminho_hierarquico |
|---|---|---|---|---|---|
| M001 | | | | | M001 |
| M002 | Ana | | | | M001 > M002 |
| M003 | Ana | Bruno | | | M001 > M002 > M003 |
| M004 | Ana | Bruno | Carla | | M001 > M002 > M003 > M004 |
| M005 | Ana | Bruno | | | M001 > M002 > M005 |

Repare na Elisa: ela responde direto ao gerente, então a coluna Coordenador fica vazia em vez de receber o nome errado.

## Como rodar

```bash
pip install -r requirements.txt

python data/gerar_dados.py      # gera a base sintética em data/colaboradores.csv
python -m src.hierarquia        # gera saida/hierarquia.csv e mostra o resumo de alertas
pytest                          # roda os testes

# ou com o exemplo do README:
python -m src.hierarquia --entrada examples/exemplo_entrada.csv --saida saida/exemplo.csv
```

Requer Python 3.10 ou superior.

Opções da linha de comando: `--entrada`, `--saida` e `--incluir-proprio` (a própria pessoa ocupa a coluna do seu nível, útil para filtrar "o gerente e toda a equipe dele").

Uso como biblioteca:

```python
from src.hierarquia import desdobrar_hierarquia, resumo_alertas

resultado = desdobrar_hierarquia(df, col_id="matricula", col_lider="matricula_lider",
                                 col_cargo="cargo", col_nome="nome")
resumo_alertas(resultado)
```

## Colunas geradas

| Coluna | Descrição |
|---|---|
| `<Nivel>_id` / `<Nivel>_nome` | Quem ocupa aquele nível na cadeia acima do colaborador. |
| `qtd_niveis_acima` | Quantos líderes foram encontrados até o topo. |
| `caminho_hierarquico` | A cadeia completa, do topo até o colaborador. |
| `alertas` | Problemas de qualidade encontrados na cadeia (ver doc 03). |

## Estrutura

```
hr-org-hierarchy-mapping/
├── .github/workflows/
│   └── testes.yml          # CI: roda testes e pipeline a cada push
├── data/
│   └── gerar_dados.py      # base sintética com anomalias propositais
├── docs/                   # guia de estudos
│   ├── 01_problema_e_modelo_de_dados.md
│   ├── 02_algoritmo_de_desdobramento.md
│   └── 03_qualidade_de_dados.md
├── examples/
│   └── exemplo_entrada.csv # exemplo mínimo usado neste README
├── src/
│   ├── __init__.py
│   └── hierarquia.py       # rotina principal
├── tests/
│   └── test_hierarquia.py  # 17 testes com pytest
├── .gitignore              # bloqueia qualquer .csv/.xlsx fora de examples/
├── LICENSE
├── pytest.ini
├── README.md
└── requirements.txt
```

## Guia de estudos

1. [O problema e o modelo de dados](docs/01_problema_e_modelo_de_dados.md): árvores, lista de adjacência e por que classificar pelo cargo.
2. [O algoritmo de desdobramento](docs/02_algoritmo_de_desdobramento.md): travessia, detecção de ciclos, complexidade e alternativas.
3. [Qualidade de dados e governança](docs/03_qualidade_de_dados.md): os alertas, o que fazer com cada um e cuidados de LGPD.

## Dados

Todos os dados deste repositório são **sintéticos**. Nenhuma informação real de colaboradores é utilizada ou versionada.

## Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE).
