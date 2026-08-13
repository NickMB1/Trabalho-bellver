---
name: onvio-enviar-lote
description: Seleciona todos os arquivos já identificados pelo Onvio Express e clica no botão de envio (ícone de joinha/like para cima), confirmando que o lote foi enviado. Use como quarto passo, depois que onvio-subir-lote já identificou os arquivos do lote e o usuário (via orquestrador onvio-express-pipeline) já resolveu o que fazer com eventuais pendentes — nunca envie um lote que ainda tenha arquivos pendentes sem essa decisão explícita.
---

# onvio-enviar-lote

Confirma o envio de um lote já identificado no Onvio Express: seleciona
todos e clica no botão de "joinha" (👍).

## Entrada esperada

- `tabId`: aba já aberta e posicionada no Onvio Express, com o lote já
  carregado por `onvio-subir-lote`.

## Passo a passo

1. **Clique em "Selecionar todos"** na lista de arquivos do Onvio Express
   (localize com `find`, ex.: "selecionar todos" ou checkbox de cabeçalho da
   lista).

2. **Confira visualmente** (via `get_page_text`/`find`) que a seleção
   cobriu os arquivos esperados — se "selecionar todos" também marcar algum
   arquivo pendente/não identificado que não deveria ir junto, avise e pare
   em vez de enviar mesmo assim, a menos que o orquestrador já tenha
   confirmado explicitamente que é para enviar tudo.

3. **Clique no botão de envio** — o ícone de **joinha/like (👍) apontando
   para cima** — que é a ação de "enviar" no Onvio Express.

4. **Confirme o resultado** com `get_page_text`/`find`: mensagem de sucesso,
   itens enviados somem da lista de pendentes, contador de arquivos
   enviados, etc.

## O que reportar ao final

- `status`: `"enviado"` ou `"falha"`.
- Se enviado: quantos arquivos foram confirmados como enviados.
- Se falha: o que foi observado na tela (mensagem de erro, nada aconteceu
  após o clique, etc.) — não insista mais de uma segunda tentativa; reporte
  como indisponível se falhar de novo.

Esta é uma ação **difícil de reverter** (uma vez enviado, o arquivo entra no
fluxo do processo do cliente no Onvio) — só a execute quando o orquestrador
confirmar que é para prosseguir com o envio daquele lote.
