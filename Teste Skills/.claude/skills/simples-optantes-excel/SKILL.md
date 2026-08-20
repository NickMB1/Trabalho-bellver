---
name: simples-optantes-excel
description: Gera a planilha Excel (.xlsx) final com os CNPJs que têm evento futuro agendado no Simples Nacional (ex.: exclusão de ofício), a partir dos resultados já coletados pela skill simples-optantes-consulta para um lote de CNPJs. Use como último passo, depois de consultar todos os CNPJs do lote, sempre que o usuário pedir para "gerar o excel", "montar a planilha dos eventos" — precisa do JSON com os resultados de cada CNPJ como entrada.
---

# simples-optantes-excel

É um passo puramente local (sem rede/navegador) que consolida em uma
planilha os resultados já coletados pela skill `simples-optantes-consulta`
para cada CNPJ do lote.

## Entrada esperada

- Uma lista JSON de registros, um por CNPJ consultado, no formato
  retornado pela skill `simples-optantes-consulta` (campos `cnpj`,
  `status`, `razao_social`, `situacao_simples`, `situacao_simei`,
  `eventos_futuros`). Salve essa lista num arquivo `.json` temporário
  antes de chamar o script (ex.: `resultados_simples.json`).
- `output_path`: caminho do `.xlsx` de saída. Se o usuário não informar,
  pergunte onde salvar.

## Passo a passo

1. Rode:
   ```
   python <diretório-desta-skill>/scripts/gerar_excel.py --input <json-dos-resultados> --output <output_path>
   ```
2. O script gera duas abas:
   - **Eventos Futuros**: uma linha por evento (um CNPJ com 2 eventos
     futuros gera 2 linhas) — CNPJ, Razão Social, Situação no Simples
     Nacional, Situação no SIMEI, Descrição do Evento, Data Efeito.
     **Só entram nessa planilha os CNPJs que de fato têm evento futuro**
     — é o requisito principal desta skill, não liste CNPJs sem evento
     aqui.
   - **Não Localizados**: só é criada se houver CNPJs com `status`
     diferente de `"sucesso"` (CNPJ inválido, não encontrado, portal
     indisponível) — para o usuário não achar que esses CNPJs foram
     verificados e estão limpos.
3. Leia a saída do script (contagens) e repita para o usuário: quantos
   CNPJs foram consultados, quantos têm evento futuro, e quantos não
   puderam ser processados (se houver) — esse último ponto deve ser
   destacado, não só mencionado de passagem.

## O que reportar ao final

- `status`: `"sucesso"` ou `"falha"`.
- Caminho final do `.xlsx` gerado.
- Contagem de CNPJs com evento futuro vs. total consultado vs. não
  localizados.
