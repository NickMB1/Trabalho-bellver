---
name: mei-calcular-competencia
description: Calcula qual competência (mês/ano de apuração) do DAS-MEI deve ser solicitada no PGMEI para que a guia gerada tenha vencimento dentro do mês corrente. Use sempre que o usuário pedir "a guia do MEI deste mês", "a guia com vencimento no mês corrente/atual", ou como segundo passo do fluxo orquestrado pela skill mei-guia-pipeline — nunca assuma que competência e mês de vencimento são o mesmo mês.
---

# mei-calcular-competencia

É um passo puramente local (data do sistema), sem rede nem automação de
navegador. Existe porque **a guia do MEI tem vencimento no mês seguinte ao
mês de referência (competência)**: o DAS vence todo dia 20 (ou próximo dia
útil, se cair em fim de semana/feriado) do mês seguinte ao mês a que se
refere a contribuição.

Ou seja: se hoje é **julho/2026**, a guia cujo vencimento cai **em
julho/2026** é a da competência **junho/2026** — não a de julho. Confundir
essas duas datas é o erro mais comum ao pedir "a guia deste mês", por isso
esta skill isola esse cálculo em vez de deixar cada chamador refazer a
conta.

## Entrada esperada

Nenhuma obrigatória. Opcionalmente:

- `data_referencia`: data ISO (`AAAA-MM-DD`) para calcular a competência
  como se "hoje" fosse essa data — útil só para testes; no uso normal, deixe
  a skill usar a data real do sistema.

## Passo a passo

1. Rode:
   ```
   python <diretório-desta-skill>/scripts/calcular_competencia.py [data_referencia]
   ```
2. Leia a saída (`chave=valor`, uma por linha):
   - `competencia`: mês/ano de apuração a selecionar no PGMEI, formato
     `MM/AAAA` (ex.: `06/2026`).
   - `competencia_extenso`: mesma competência por extenso (ex.:
     `junho/2026`), para usar na comunicação com o usuário.
   - `vencimento_mes_extenso`: o mês/ano corrente por extenso (ex.:
     `julho/2026`) — é o mês em que a guia vence, para deixar explícito na
     resposta que "competência" e "vencimento" são meses diferentes.

## O que reportar ao final

Sempre devolva os três valores (`competencia`, `competencia_extenso`,
`vencimento_mes_extenso`) para quem chamou esta skill. Se for usada
isoladamente (fora do pipeline), explique ao usuário a diferença entre
competência e vencimento antes de seguir, para evitar que ele peça a guia
errada.

## Limitação conhecida

O dia exato do vencimento (20, ou o próximo dia útil caso o dia 20 caia em
fim de semana/feriado nacional) não é calculado aqui — esta skill só
determina o **mês/ano de competência** a informar no PGMEI. O dia exato de
vencimento aparece impresso na própria guia gerada pela skill
`mei-emitir-das`.
