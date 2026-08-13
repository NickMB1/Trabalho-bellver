---
name: onvio-subir-lote
description: Sobe um lote de arquivos (já dentro do limite de tamanho de upload) para a aba Onvio Express, em uma aba de navegador já aberta e posicionada, e aguarda o próprio Onvio identificar automaticamente a qual cliente/processo cada arquivo pertence. Use como terceiro passo, repetido uma vez por lote, dentro do fluxo orquestrado pela skill onvio-express-pipeline — nunca isoladamente sem antes abrir a aba com onvio-abrir-express.
---

# onvio-subir-lote

Faz o upload de um lote de arquivos no Onvio Express e verifica o resultado
do reconhecimento automático feito pelo próprio sistema.

## Entrada esperada

- `tabId`: aba já aberta e posicionada na tela do Onvio Express (vem de
  `onvio-abrir-express`).
- `arquivos`: lista de caminhos absolutos do lote (já deve estar abaixo do
  limite combinado de upload — essa checagem é responsabilidade de quem
  chama, normalmente `onvio-ler-pasta`).

## Passo a passo

1. **Localize o elemento de upload** na tela do Onvio Express com
   `find`/`read_page` (input de arquivo ou área de arrastar-e-soltar). Nunca
   clique diretamente em botões de "selecionar arquivo" — isso abre um
   seletor nativo do sistema operacional que não pode ser controlado; use
   sempre a ferramenta `file_upload` com o `ref` do elemento encontrado.

2. **Chame `file_upload`** passando `tabId`, o `ref` do input e a lista de
   `arquivos` do lote.
   - Se algum arquivo for rejeitado por não estar acessível à sessão (fora
     de pastas compartilhadas/conectadas), registre-o como falha de upload
     com esse motivo e continue com os demais do lote.

3. **Aguarde o processamento**: o Onvio associa cada arquivo enviado a um
   cliente/processo automaticamente. Use `get_page_text`/`find`
   periodicamente para observar o status de cada arquivo na lista (ex.:
   "identificado", "processando", "não identificado"). Dê um tempo razoável
   antes de checar (evite bater a página em loop apertado).

4. **Classifique cada arquivo do lote** ao final da espera:
   - **Identificado**: o Onvio associou a um cliente/processo com sucesso.
   - **Pendente/não identificado**: o sistema não conseguiu associar
     automaticamente, ou pede seleção manual de cliente. **Não tente
     adivinhar ou selecionar um cliente manualmente** — isso é decisão de
     quem usa o Onvio, não desta skill.
   - **Falha de upload**: nem chegou a ser processado (rejeitado, erro de
     rede etc.).

## O que reportar ao final

- `identificados`: lista de arquivos (nome/caminho) que o Onvio já associou
  a um cliente/processo — prontos para envio.
- `pendentes`: lista de arquivos sem identificação automática, com o texto
  de status exibido na tela, se houver.
- `falhas_upload`: lista de arquivos que nem subiram, com o motivo.

Esta skill **nunca** seleciona "todos" nem clica no botão de enviar — isso é
responsabilidade da skill `onvio-enviar-lote`, chamada em seguida pelo
orquestrador.
