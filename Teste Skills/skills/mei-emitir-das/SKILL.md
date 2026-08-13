---
name: mei-emitir-das
description: Gera e baixa o PDF da guia de pagamento do MEI (DAS — Documento de Arrecadação do Simples Nacional) para um CNPJ e uma competência (mês/ano) específicos, usando o portal oficial PGMEI da Receita Federal via automação de navegador. Use sempre que já tiver um CNPJ validado e uma competência definida — isoladamente, ou como terceiro passo do fluxo orquestrado pela skill mei-guia-pipeline.
---

# mei-emitir-das

Gera a guia DAS do MEI no PGMEI (Programa Gerador do DAS para o MEI) —
não existe API pública para isso, então esta skill depende da skill
`claude-in-chrome` para navegar e preencher o formulário como um humano
faria.

## Entrada esperada

- `cnpj`: 14 dígitos, já normalizado/validado (produto da skill
  `mei-validar-cnpj` — não valide de novo aqui, apenas confie na entrada).
- `competencia`: mês/ano de apuração no formato `MM/AAAA` (produto da skill
  `mei-calcular-competencia`, ou informado diretamente se o usuário já sabe
  qual competência quer).

Se qualquer uma faltar, pare e peça — não adivinhe competência nem tente
extrair CNPJ de outra fonte.

## Passo a passo

1. **Invoque a skill `claude-in-chrome`** (não tente chamar
   `mcp__claude-in-chrome__*` diretamente antes disso) para abrir uma aba em:
   `https://www8.receita.fazenda.gov.br/SimplesNacional/Aplicacoes/ATSPO/pgmei.app/Identificacao`

   **Se a aba já estiver aberta com a sessão de um CNPJ anterior** (chamada
   repetida dentro de um lote — ver skill `mei-guia-pipeline`), o PGMEI
   mantém o CNPJ identificado na sessão mesmo que você navegue de volta
   para essa URL. Nesse caso, **clique primeiro em "Sair"** no menu
   superior do portal para encerrar a sessão do CNPJ anterior, e só depois
   navegue novamente para a URL de identificação acima. Nunca reaproveite
   uma sessão já identificada para emitir a guia de um CNPJ diferente.

2. **Preencha o campo de CNPJ** com os 14 dígitos e avance (botão
   "Continuar"/"Avançar"). Se houver checkbox de declaração/ciência
   obrigatório para prosseguir, marque-o normalmente — não é um desafio
   anti-robô, é apenas um termo de uso do próprio PGMEI.

3. **Trate desafios anti-robô com cuidado**, caso apareçam:
   - Checkbox simples tipo "Não sou um robô" sem puzzle visual: pode
     marcar e prosseguir normalmente.
   - Qualquer CAPTCHA de imagem, quebra-cabeça ou reCAPTCHA visual: **pare**,
     avise o usuário que a aba está aberta no navegador dele e peça para
     resolver manualmente o desafio; só continue depois que ele confirmar.
     Nunca tente automatizar a resolução desse tipo de desafio.

3.1. **Capture o nome da empresa** (`nome_empresa`) assim que o portal
   confirmar o CNPJ — a tela inicial após o avanço mostra uma linha "Nome:"
   com a razão social (ex.: `64.262.737 NICOLAS MINATO BELLVER`). Esse
   valor é usado depois para nomear o arquivo final na skill
   `mei-salvar-guia`, então sempre capture o texto exato exibido, sem
   reformatar ou abreviar.

4. **Selecione "Emitir Guia de Pagamento (DAS)"** no menu de opções do
   PGMEI (em vez de "Consultar Débitos", "Declarar" ou outras opções que
   também aparecem ali).

5. **Escolha o ano-calendário e o mês de apuração** correspondentes à
   `competencia` recebida (ex.: `06/2026` → ano `2026`, mês `06`/junho). O
   portal costuma listar os períodos em aberto como checkboxes ou uma
   tabela selecionável — marque exatamente o período pedido, nenhum outro
   período extra, mesmo que existam outros em aberto.

6. **Gere a guia** (botão "Emitir Guia"/"Gerar DAS"). O portal deve abrir
   ou oferecer o download de um PDF.

7. **Leia o resultado antes de considerar sucesso**:
   - Guia gerada normalmente: a tela de confirmação ("DAS gerados") traz
     uma tabela com Período de Apuração, Número da Apuração, Número do DAS
     e Data de Vencimento — capture a **Data de Vencimento** dali
     (`data_vencimento`) e o **valor total** mostrado na etapa anterior de
     seleção do período (`valor_das`). Ambos são sempre exibidos pelo
     portal nesse fluxo, não são opcionais.
   - **CNPJ não encontrado / não é MEI / não optante do Simples**: reporte
     como indisponível com esse motivo — não é um MEI válido para esse
     CNPJ.
   - **Competência não disponível para emissão** (ex.: período futuro,
     empresa aberta depois daquele mês, ou já baixada/desenquadrada):
     reporte como indisponível com o motivo exato mostrado pelo portal.

8. **Baixe o PDF**: clique em "Imprimir/Visualizar PDF". O portal costuma
   baixar o arquivo diretamente para a pasta de downloads padrão do
   navegador (sem abrir nova aba) — confira o arquivo mais recente nessa
   pasta (nome tipicamente `DAS-PGMEI-<cnpj>-AC<ano>*.pdf`) para obter o
   caminho exato. **Não o mova ainda** — apenas reporte o caminho onde ele
   ficou; mover para o destino final é responsabilidade da skill
   `mei-salvar-guia`, chamada em seguida. Se estiver processando vários
   CNPJs em lote, tome cuidado para associar o arquivo baixado certo a cada
   CNPJ (confira o CNPJ no próprio nome do arquivo antes de prosseguir).

9. **Se o portal estiver fora do ar, em manutenção, ou não for possível
   concluir a emissão por qualquer motivo técnico** (timeout, erro 500,
   captcha que o usuário não conseguiu resolver, etc.), não insista
   indefinidamente — tente no máximo uma segunda vez e, se falhar de novo,
   reporte como indisponível com o motivo observado.

10. **Encerre a sessão deste CNPJ antes de finalizar esta invocação**,
    sempre — tanto em caso de sucesso quanto de indisponibilidade. Clique
    em "Sair" no menu superior do portal (e, se o clique não estiver
    disponível ou não funcionar, navegue novamente para a URL de
    identificação do passo 1). Isso garante que a aba fique limpa, sem
    CNPJ identificado, pronta para a próxima chamada desta skill começar
    do zero — essencial quando esta skill é chamada várias vezes em
    sequência pela skill `mei-guia-pipeline` para processar um lote de
    CNPJs. Nunca deixe a sessão de um CNPJ aberta ao encerrar.

## O que reportar ao final

Sempre devolva, mesmo quando chamado dentro do pipeline:

- `status`: `"sucesso"` ou `"indisponivel"`.
- Se sucesso: `nome_empresa`, `arquivo_baixado` (caminho onde o PDF ficou
  após o download), `valor_das` e `data_vencimento` exibidos pelo portal.
  Os quatro são obrigatórios em caso de sucesso — `nome_empresa` e
  `data_vencimento` em especial são usados pela skill `mei-salvar-guia`
  para nomear o arquivo final.
- Se indisponível: o motivo (CNPJ não é MEI, competência indisponível,
  portal fora do ar, captcha não resolvido, etc.).
