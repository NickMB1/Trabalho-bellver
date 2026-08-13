---
name: onvio-ler-pasta
description: Lista os arquivos de uma pasta local e os agrupa em lotes que respeitam o limite de tamanho combinado do upload no navegador (~10 MB por lote), para envio posterior ao Onvio Express. Use como primeiro passo sempre que o usuário apontar uma pasta de arquivos para mandar ao Onvio — nunca como etapa isolada fora do fluxo orquestrado pela skill onvio-express-pipeline.
---

# onvio-ler-pasta

Etapa 100% local (sem navegador) que prepara a lista de arquivos a enviar ao
Onvio Express, dividida em lotes dentro do limite de upload.

## Entrada esperada

- `pasta`: caminho local da pasta com os arquivos. Pergunte ao usuário se
  não foi informado.

## Passo a passo

1. **Liste os arquivos diretamente dentro da pasta** (não recursivo).
   Ignore subpastas, mas **conte quantas existem** — se houver alguma, isso
   vai para o relatório de saída para o orquestrador decidir se pergunta ao
   usuário.

2. **Pegue o tamanho de cada arquivo** (em bytes).

3. **Monte os lotes**: agrupe os arquivos, na ordem em que aparecem, de
   forma que a soma de tamanhos de cada lote fique **abaixo de 10 MB**
   (deixe uma margem, ex.: limite prático de 9 MB por lote, já que o limite
   real da ferramenta de upload é "menor que 10 MB combinados"). Um único
   arquivo maior que o limite sozinho não pode ser enviado por esta via —
   marque-o separadamente como `arquivos_grandes_demais` em vez de incluí-lo
   em um lote.

4. **Não abra navegador nem tente enviar nada** — esta skill só lê o
   sistema de arquivos local e devolve a lista organizada.

## O que reportar ao final

- `total_arquivos`: quantidade total encontrada na pasta (nível raiz).
- `lotes`: lista de lotes, cada um com a lista de caminhos absolutos dos
  arquivos que o compõem.
- `arquivos_grandes_demais`: arquivos individuais que sozinhos já
  ultrapassam o limite de upload (nome e tamanho).
- `subpastas_ignoradas`: quantas subpastas existem na pasta informada e
  foram ignoradas (para o orquestrador avisar o usuário, se for o caso).

Se a pasta não existir ou estiver vazia, reporte isso claramente em vez de
prosseguir como se houvesse arquivos.
