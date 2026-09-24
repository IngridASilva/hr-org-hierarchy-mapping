# 02 — O algoritmo de desdobramento

## O conceito

Para cada colaborador, o script faz uma **travessia ascendente**: olha o líder imediato, depois o líder do líder, e assim por diante até chegar ao topo. Cada líder encontrado é classificado pelo cargo e vai para a coluna do seu nível.

```
para cada colaborador:
    atual = colaborador
    enquanto atual tiver líder:
        se o líder já foi visitado      -> ciclo, para
        se o líder não existe na base   -> cadeia quebrada, para
        guarda o líder
        atual = líder
    distribui os líderes guardados nas colunas de nível
```

## Por que importa no RH

A base de RH nunca é perfeita: há líderes desligados que continuam no cadastro de alguém, erros de digitação, transferências registradas pela metade. Um algoritmo que só funciona com dados limpos trava (ou pior, entra em loop infinito) justamente no dia do fechamento. A travessia foi desenhada para **parar com segurança e registrar o motivo** em vez de falhar.

## Como foi feito

Três escolhas técnicas valem o estudo:

1. **Dicionários para as consultas.** Antes da travessia, a base vira dicionários (`matricula -> lider`, `matricula -> nivel`). Cada consulta é O(1); filtrar o DataFrame a cada passo seria ordens de grandeza mais lento.
2. **Laço `while`, não recursão.** Recursão é elegante, mas o Python tem limite de profundidade (por padrão, cerca de 1000 chamadas) e o erro aparece de forma pouco clara quando há ciclo.
3. **Conjunto de visitados.** Se A lidera B e B lidera A, a subida nunca terminaria. Guardar quem já foi visto detecta o ciclo no primeiro retorno a um nó.

**Complexidade:** O(n × h), onde n é o número de colaboradores e h a altura da árvore. Em uma empresa com 50 mil pessoas e 10 níveis, são cerca de 500 mil passos, o que roda em segundos.

## Alternativas (e quando usar)

| Abordagem | Quando faz sentido |
|---|---|
| **Memoização** (guardar a cadeia de cada líder já calculada) | Bases muito grandes; evita recalcular o mesmo trecho da árvore para toda a equipe. |
| **Self-merge iterativo no pandas** (juntar a tabela com ela mesma k vezes) | Quando a equipe prefere tudo vetorizado; exige tratar ciclos à parte. |
| **networkx** (`DiGraph`, `find_cycle`, `ancestors`) | Quando vierem outras análises de grafo, como amplitude de controle ou redes de colaboração. |
| **CTE recursiva em SQL** | Quando a hierarquia deve ser montada direto no data warehouse. |

A travessia simples foi escolhida pela legibilidade: é fácil de explicar, testar e auditar.

## Armadilhas

- **Auto-referência:** alguns sistemas marcam o presidente como líder de si mesmo. O script trata `lider == matricula` como topo.
- **Base desordenada:** a travessia não depende da ordem das linhas; o gerador de dados embaralha a base de propósito para garantir isso.
- **Nível repetido na cadeia:** quando dois gerentes aparecem em sequência, a coluna recebe o **mais próximo**. Essa é uma decisão de negócio, e o caso é sinalizado (ver doc 03).

## Para aprofundar

- Busca em profundidade (DFS) e detecção de ciclos em grafos direcionados.
- Notação Big-O aplicada a laços aninhados.
- networkx: https://networkx.org/documentation/stable/
