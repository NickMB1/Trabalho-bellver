---
name: cnd-estadual
description: Emite a Certidão Negativa de Débitos Tributários Estaduais de uma empresa, dado o CNPJ e a UF (estado), localizando o portal oficial da Secretaria da Fazenda (SEFAZ) daquele estado e navegando nele via automação de navegador para baixar o PDF. Use sempre que o usuário pedir a "CND estadual", "certidão negativa da SEFAZ", "certidão negativa de débitos do ICMS" ou a situação fiscal estadual de um CNPJ — isoladamente ou como parte do fluxo completo orquestrado pela skill cnd-pipeline.
---

# cnd-estadual

Emite a Certidão Negativa de Débitos Tributários Estaduais para um CNPJ.
Diferente da federal, **não existe um portal único**: cada um dos 27
estados (26 + DF) tem seu próprio site de SEFAZ/Fazenda, com URL, layout e
regras próprias. Por isso esta skill sempre localiza o portal certo antes
de tentar emitir a certidão — nunca assuma ou reaproveite uma URL de
memória sem confirmar.

## Entrada esperada

- `cnpj`: 14 dígitos (normalize removendo máscara).
- `uf`: sigla do estado (ex.: `SP`, `RJ`, `MG`) ou nome por extenso — se
  vier só o nome do município, você precisa perguntar a UF antes de
  continuar, pois o portal estadual depende do estado, não da cidade.
- `output_path`: caminho do `.pdf` de destino (ex.:
  `CND/<cnpj>/estadual_<UF>.pdf`). Pergunte se não vier definido.

## Passo a passo

1. **Localize o portal oficial** com a skill/tool de busca web: procure
   algo como `"certidão negativa de débitos tributários" SEFAZ <estado>
   emissão online site oficial`. Priorize resultados em domínio `.gov.br`
   ou subdomínios oficiais de fazenda/sefaz do próprio estado (ex.:
   `fazenda.sp.gov.br`, `sefaz.rj.gov.br`). Nunca use um domínio que não
   pareça claramente institucional — se não achar nada confiável, trate
   como indisponível (veja seção final) em vez de arriscar um site errado.

2. **Invoque a skill `claude-in-chrome`** para abrir a URL localizada no
   passo 1.

3. **Preencha o formulário de emissão** com o CNPJ. Alguns estados pedem
   **Inscrição Estadual** em vez de (ou além do) CNPJ:
   - Se o portal aceitar consulta só por CNPJ, siga normalmente.
   - Se exigir Inscrição Estadual e ela não tiver sido fornecida, não
     tente adivinhar — pare e informe ao usuário que este estado exige
     Inscrição Estadual para emitir a certidão, e pergunte se ele tem esse
     dado. Se não tiver, reporte como indisponível por esse motivo.

4. **Trate desafios anti-robô com cuidado** — mesma regra da skill
   `cnd-federal`: checkbox simples pode ser marcado; qualquer CAPTCHA
   visual/reCAPTCHA exige pausar e pedir para o usuário resolver
   manualmente na aba aberta.

5. **Leia o resultado** (negativa / positiva com efeito de negativa /
   positiva / CNPJ ou IE não encontrado) e **baixe o PDF** pela opção de
   salvar/emitir certidão do próprio portal. Copie o arquivo baixado para
   `output_path`.

6. **Se o estado não tiver emissão online** (alguns ainda exigem
   atendimento presencial ou têm sistemas fora do ar com frequência), ou
   se não for possível concluir por qualquer motivo técnico após uma
   segunda tentativa, reporte como indisponível com o motivo.

## O que reportar ao final

- `status`: `"sucesso"` ou `"indisponivel"`.
- Se sucesso: resultado da certidão, UF, URL do portal usado e caminho do
  PDF salvo.
- Se indisponível: motivo (exige Inscrição Estadual não fornecida, portal
  não encontrado/fora do ar, captcha não resolvido, sem emissão online
  neste estado, etc.).

Assim como na federal, uma certidão **Positiva** (com débito) não é falha
desta skill — é o resultado real. Só marque `indisponivel` quando o PDF de
fato não pôde ser gerado.
