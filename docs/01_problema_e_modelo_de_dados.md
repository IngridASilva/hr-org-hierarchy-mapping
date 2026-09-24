# 01 — O problema e o modelo de dados

## O conceito

Uma estrutura organizacional é uma **árvore**: cada pessoa tem no máximo um líder imediato e existe uma raiz (a presidência). No RH, a forma mais comum de guardar essa árvore é a **lista de adjacência**: uma linha por colaborador com a matrícula do líder.

| matricula | cargo | matricula_lider |
|---|---|---|
| M001 | Diretora Comercial | |
| M002 | Gerente de Vendas | M001 |
| M003 | Coordenadora de Vendas | M002 |
| M004 | Analista de Vendas | M003 |

É compacta e fácil de manter (mudou o líder, muda uma célula), mas ruim de consumir: para saber quem é o gerente do M004 é preciso "subir" a árvore passo a passo. O desdobramento converte isso para o **formato largo (wide)**, com uma coluna por nível:

| matricula | Diretor | Gerente | Coordenador | Supervisor |
|---|---|---|---|---|
| M004 | M001 | M002 | M003 | — |

## Por que importa no RH

Com uma coluna por nível, perguntas que exigiam lógica recursiva viram um filtro simples. "Quem está abaixo da Gerente X?" em um dashboard, envio de relatórios por liderança, pesquisas de clima por gestor, fluxos de aprovação, calibração de desempenho e indicadores como turnover por gerente passam a depender só de um `groupby` na coluna certa. Ferramentas de organograma também consomem essa estrutura diretamente.

## Decisão central: nível pelo cargo, não pela profundidade

Uma abordagem ingênua seria dizer "o 1º acima é o supervisor, o 2º é o coordenador, o 3º é o gerente". Isso quebra assim que um nível é pulado, o que é comum: um analista sênior pode responder direto ao gerente. Pela profundidade, o gerente dele seria colocado na coluna Supervisor.

Por isso o script **classifica cada líder pelo cargo** e coloca a matrícula na coluna do nível correspondente. Níveis que a cadeia não atravessa ficam nulos, que é exatamente a informação correta.

## Como foi feito

A régua de níveis fica em um dicionário, do topo para a base:

```python
NIVEIS_PADRAO = {
    "Presidente": ["presidente", "ceo"],
    "Diretor": ["diretor", "diretora"],
    "Gerente": ["gerente"],
    "Coordenador": ["coordenador", "coordenadora"],
    "Supervisor": ["supervisor", "supervisora"],
}
```

O cargo é normalizado (minúsculas, sem acento) e comparado com uma regex com limite de palavra (`\b`). Sem o `\b`, "Analista de Gerenciamento" poderia ser confundido com liderança em regras mal escritas. A ordem do dicionário resolve cargos com duas palavras-chave: "Diretor e Gerente Geral" vira Diretor.

## Armadilhas

- **Títulos ambíguos** como "Head", "Líder de Squad" ou "Especialista Líder" não se encaixam sozinhos. A decisão é de negócio (valide com a área de Cargos e Salários) e depois vira configuração no dicionário.
- **Se existir um campo oficial de nível** (grade, nível de carreira), prefira ele ao texto do cargo. Basta passá-lo como `col_cargo` e usar os próprios nomes dos níveis como palavras-chave.
- **Matrícula é texto, não número.** Lida como número, perde zeros à esquerda; e com nulos na coluna de líder, o pandas transforma `1001` em `1001.0`, e o cruzamento falha silenciosamente. O script lê com `dtype=str` e normaliza os IDs.

## Para aprofundar

- Modelagem de hierarquias em banco de dados: lista de adjacência, *nested sets*, *materialized path* e *closure table*.
- Em SQL, o mesmo problema se resolve com CTE recursiva (`WITH RECURSIVE`).
- Módulo `re` do Python: https://docs.python.org/3/library/re.html
