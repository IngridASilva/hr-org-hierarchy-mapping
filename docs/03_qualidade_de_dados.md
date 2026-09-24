# 03 — Qualidade de dados e governança

## O conceito

O script segue um princípio: **sinalizar, não corrigir**. Ele não tenta adivinhar o líder certo de ninguém. Cada problema encontrado vira um código na coluna `alertas`, e a correção acontece na origem (o sistema de folha ou o HRIS), por quem tem autoridade sobre o dado.

## Por que importa no RH

Um organograma errado tem consequência real: avaliação de desempenho enviada ao gestor errado, aprovação de férias travada, relatórios com dados de pessoas chegando a quem não deveria vê-los. Os alertas transformam o script em uma **auditoria do cadastro**, que muitas vezes é mais valiosa que o próprio organograma.

## Os alertas

| Código | O que significa | Causa comum no RH | O que fazer |
|---|---|---|---|
| `CICLO` | A cadeia volta para alguém já visitado (A → B → A). | Troca de liderança registrada nas duas pontas. | Corrigir o líder de uma das pessoas na origem. |
| `LIDER_FORA_DA_BASE` | A matrícula do líder não existe na base. | Líder desligado, afastado, terceiro ou erro de digitação. | Atualizar o líder no cadastro; conferir se a extração filtrou só ativos. |
| `LIDER_SEM_NIVEL` | Há um líder cujo cargo não se encaixa na régua. | Cargos como "Head", "Líder técnico" ou cargo desatualizado. | Decidir o nível com Cargos e Salários e incluir no dicionário. |
| `NIVEL_REPETIDO` | Dois líderes do mesmo nível na cadeia. | Gerente abaixo de gerente sênior; pode ser legítimo. | Validar; a coluna guarda o mais próximo. |
| `HIERARQUIA_INVERTIDA` | Um líder acima tem nível menor que alguém abaixo dele. | Gerente cadastrado sob coordenador; promoção não refletida. | Quase sempre é erro de cadastro: corrigir na origem. |

Duplicidade de matrícula e matrícula vazia **interrompem** a execução, porque não há como montar a árvore de forma confiável. Esses são erros de extração, não de estrutura.

## Como foi feito

Ao final de cada execução, `resumo_alertas()` mostra quantos colaboradores têm cada problema. Um fluxo prático:

1. Rodar a rotina a cada carga da base.
2. Enviar a lista de alertas para quem mantém o cadastro.
3. Acompanhar a quantidade de alertas ao longo do tempo como indicador de qualidade do dado.

## Governança e LGPD

- A saída reúne nome, cargo e cadeia de liderança: são **dados pessoais**. O acesso deve seguir o mesmo controle da base de origem.
- Minimização: se o consumidor final só precisa da estrutura, rode com `col_nome=None` e trabalhe com matrículas.
- Este repositório usa **somente dados sintéticos**. O `.gitignore` bloqueia arquivos `.csv` e a pasta `saida/` para evitar que uma base real seja versionada por engano.

## Para aprofundar

- Dimensões de qualidade de dados: completude, unicidade, consistência, validade.
- LGPD, art. 6º (princípios de finalidade, necessidade e segurança).
- Testes automatizados como documentação de regras de negócio (veja `tests/`).
