---
name: mei-salvar-guia
description: Move/copia o PDF da guia do MEI já baixado do navegador para a pasta de destino escolhida pelo usuário, renomeando o arquivo com o nome da empresa, a competência e a data de vencimento da guia. Use depois que a skill mei-emitir-das já tiver gerado e baixado o PDF — isoladamente, ou como último passo do fluxo orquestrado pela skill mei-guia-pipeline.
---

# mei-salvar-guia

É um passo puramente local de sistema de arquivos, sem rede nem
automação de navegador. Existe para separar "gerar o PDF" (skill
`mei-emitir-das`) de "colocar o PDF onde o usuário quer" — assim o usuário
pode redirecionar o destino sem precisar gerar a guia de novo.

## Entrada esperada

- `arquivo_origem`: caminho do PDF baixado (produto da skill
  `mei-emitir-das`).
- `pasta_destino`: pasta onde o usuário quer o arquivo final. **Sempre
  pergunte se não vier definida explicitamente** — nunca escolha uma pasta
  por conta própria (nem a pasta de downloads, nem o diretório atual).
- `nome_empresa`: razão social capturada pela skill `mei-emitir-das`
  (obrigatório — é a base do nome do arquivo).
- `competencia`: `MM/AAAA` usada para gerar a guia.
- `data_vencimento`: data de vencimento exibida pelo portal
  (`DD/MM/AAAA`, produto da skill `mei-emitir-das`).
- `cnpj`: usado só como reserva, se `nome_empresa` não vier preenchido.

## Passo a passo

1. **Confirme `pasta_destino` com o usuário** se ela não tiver sido
   informada de forma explícita e inequívoca.

2. **Sanitize `nome_empresa`** antes de usar em um nome de arquivo:
   remova os caracteres inválidos em caminhos do Windows (`\ / : * ? " < >
   |`), colapse espaços repetidos em um só, e retire espaços/pontos no
   início ou fim do resultado. Não abrevie nem reformate o nome além
   disso.

3. **Monte o nome do arquivo final**:
   `<nome_empresa sanitizado> - DAS <competencia com traço em vez de
   barra> - vencimento <data_vencimento com traço em vez de barra>.pdf`
   (ex.: nome_empresa `64.262.737 NICOLAS MINATO BELLVER`, competência
   `07/2026`, vencimento `20/08/2026` →
   `64.262.737 NICOLAS MINATO BELLVER - DAS 07-2026 - vencimento
   20-08-2026.pdf`). Se o usuário já pediu um padrão de nome específico,
   use o padrão pedido em vez deste. Se `nome_empresa` não tiver vindo
   preenchido (falha upstream), use `cnpj` no lugar dele e avise que o
   nome da empresa não estava disponível.

4. **Crie `pasta_destino` se ela ainda não existir** (operação reversível
   e de baixo risco — não precisa confirmar antes de criar a pasta em si,
   só o caminho, que já foi confirmado no passo 1).

5. **Copie** (não mova) `arquivo_origem` para `pasta_destino/<nome do
   arquivo>`. Preferir copiar em vez de mover evita perder o arquivo
   original caso o caminho de destino esteja errado ou inacessível. Se já
   existir um arquivo com exatamente esse nome no destino (ex.: reprocessou
   a mesma empresa/competência), sobrescreva — é a mesma guia, não uma
   nova.

6. **Confirme que o arquivo final existe** no destino antes de reportar
   sucesso — não assuma que a cópia funcionou só porque o comando não
   retornou erro visível.

## O que reportar ao final

- `status`: `"sucesso"` ou `"falha"`.
- Se sucesso: caminho completo do arquivo final salvo.
- Se falha: motivo (pasta sem permissão de escrita, caminho inválido,
  disco cheio, arquivo de origem não encontrado, etc.).
