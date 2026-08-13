---
name: cnd-federal
description: Emite a Certidão Negativa de Débitos Federais (Certidão Conjunta RFB/PGFN — tributos federais e Dívida Ativa da União) de uma empresa, dado o CNPJ, acessando o portal oficial da Receita Federal via automação de navegador e salvando o PDF gerado. Use sempre que o usuário pedir a "CND federal", "certidão negativa da Receita Federal", "certidão conjunta PGFN/RFB" ou a situação fiscal federal de um CNPJ — isoladamente ou como parte do fluxo completo orquestrado pela skill cnd-pipeline.
---

# cnd-federal

Emite a Certidão Conjunta Negativa de Débitos relativos aos Tributos
Federais e à Dívida Ativa da União, para um CNPJ, usando o portal oficial da
Receita Federal — não existe API pública para isso, então esta skill
depende da skill `claude-in-chrome` para navegar e preencher o formulário
como um humano faria.

## Entrada esperada

- `cnpj`: 14 dígitos (com ou sem máscara — normalize removendo `.`, `/`, `-`
  antes de preencher o campo).
- `output_path`: caminho do arquivo `.pdf` onde a certidão deve ser salva
  (ex.: `CND/<cnpj>/federal.pdf`). Se não for informado, pergunte ao usuário.

Antes de acessar o portal, confira que o CNPJ tem exatamente 14 dígitos.
Se tiver menos/mais, ou for obviamente inválido (todos os dígitos iguais),
avise o usuário e não prossiga.

## Passo a passo

1. **Invoque a skill `claude-in-chrome`** (não tente chamar
   `mcp__claude-in-chrome__*` diretamente antes disso) para abrir uma aba em:
   `https://solucoes.receita.fazenda.gov.br/Servicos/certidaointernet/PJ/Emitir`

2. **Preencha o campo de CNPJ** com os 14 dígitos (sem máscara, a maioria
   dos formulários aceita ou aplica a máscara sozinho) e envie o formulário
   (botão "Consultar").

3. **Trate desafios anti-robô com cuidado**:
   - Checkbox simples tipo "Não sou um robô" sem puzzle visual: pode
     marcar e prosseguir normalmente.
   - Qualquer CAPTCHA de imagem, quebra-cabeça ou reCAPTCHA visual: **pare**,
     avise o usuário que a aba está aberta no navegador dele e peça para
     resolver manualmente o desafio; só continue depois que o usuário
     confirmar que resolveu. Nunca tente automatizar a resolução desse tipo
     de desafio.

4. **Leia o resultado da consulta**. O portal retorna um destes estados —
   capture o texto exato exibido:
   - **Negativa** — "Certidão Negativa de Débitos..." (situação regular).
   - **Positiva com efeito de Negativa** — há débitos, mas
     suspensos/parcelados/garantidos; ainda é uma certidão válida para fins
     práticos.
   - **Positiva** — há débitos exigíveis, sem efeito de negativa.
   - **Erro/CNPJ não encontrado** — CNPJ inexistente na base da Receita, ou
     inválido.

5. **Baixe o PDF**: use a opção de salvar/baixar a certidão em PDF que o
   próprio portal oferece após a consulta (normalmente um botão "Salvar
   Certidão" ou ícone de PDF/impressora). Depois que o arquivo cair na pasta
   de downloads do navegador, copie/mova para `output_path`.

6. **Se o portal estiver fora do ar, em manutenção, ou não for possível
   concluir a emissão por qualquer motivo técnico** (timeout, erro 500,
   captcha que o usuário não conseguiu resolver, etc.), não insista
   indefinidamente — tente no máximo uma segunda vez e, se falhar de novo,
   reporte como indisponível com o motivo observado.

## O que reportar ao final

Sempre devolva, mesmo quando chamado dentro do pipeline:

- `status`: `"sucesso"` ou `"indisponivel"`.
- Se sucesso: o resultado da certidão (negativa / positiva com efeito de
  negativa / positiva) e o caminho do PDF salvo.
- Se indisponível: o motivo (CNPJ não encontrado, portal fora do ar,
  captcha não resolvido, etc.).

Uma certidão **Positiva** (com débito) não é uma falha desta skill — é o
resultado real da consulta. Só marque como `indisponivel` quando o PDF não
pôde ser gerado/baixado de fato.
