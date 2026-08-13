---
name: cnd-municipal
description: Emite a Certidão Negativa de Débitos Municipais (tributos municipais / ISSQN) de uma empresa, dado o CNPJ, o município e a UF, localizando o portal oficial da prefeitura daquele município e navegando nele via automação de navegador para baixar o PDF. Use sempre que o usuário pedir a "CND municipal", "certidão negativa da prefeitura", "certidão negativa de ISS" ou a situação fiscal municipal de um CNPJ — isoladamente ou como parte do fluxo completo orquestrado pela skill cnd-pipeline.
---

# cnd-municipal

Emite a Certidão Negativa de Débitos Municipais para um CNPJ. É a etapa
mais heterogênea das três: o Brasil tem mais de 5.500 municípios, cada um
com seu próprio sistema (ou, em muitos casos, **nenhum sistema online** —
só atendimento presencial). Por isso é normal e esperado que esta skill
termine em "indisponível" com mais frequência que as outras duas — isso
não é um erro da skill, é uma característica real do serviço.

## Entrada esperada

- `cnpj`: 14 dígitos (normalize removendo máscara).
- `municipio`: nome do município.
- `uf`: sigla do estado do município (necessária para desambiguar — vários
  municípios brasileiros têm o mesmo nome em estados diferentes; se não
  vier, pergunte antes de continuar).
- `output_path`: caminho do `.pdf` de destino (ex.:
  `CND/<cnpj>/municipal.pdf`). Pergunte se não vier definido.

## Passo a passo

1. **Localize o portal oficial da prefeitura** com a skill/tool de busca
   web: procure algo como `prefeitura de <municipio> <uf> certidão negativa
   débitos municipais emissão online` ou `<municipio> <uf> emissão CND ISS
   online`. Priorize domínios `.gov.br` (ex.: `<municipio>.<uf>.gov.br`) ou
   subdomínios institucionais claramente da prefeitura/secretaria de
   finanças. Se os resultados só mostrarem informação de "compareça
   presencialmente" ou não houver nenhum portal claramente oficial, não
   force — trate como indisponível (seção final).

2. **Invoque a skill `claude-in-chrome`** para abrir a URL localizada no
   passo 1 e procure a opção de emissão de certidão negativa (às vezes
   está dentro de um portal maior de "Nota Fiscal Eletrônica" ou "Portal do
   Contribuinte" da prefeitura, não numa página isolada).

3. **Preencha o formulário**. Muitas prefeituras pedem **Inscrição
   Municipal/Mobiliária** em vez de CNPJ puro:
   - Se aceitar consulta por CNPJ, siga normalmente.
   - Se exigir Inscrição Municipal e ela não tiver sido fornecida, pare e
     informe ao usuário que este município exige esse dado; se ele não
     tiver, reporte como indisponível por esse motivo.

4. **Trate desafios anti-robô com cuidado** — mesma regra das outras
   skills: checkbox simples pode ser marcado; qualquer CAPTCHA
   visual/reCAPTCHA exige pausar e pedir para o usuário resolver
   manualmente na aba aberta.

5. **Leia o resultado** e **baixe o PDF** pela opção de emissão/impressão
   do próprio portal. Copie o arquivo baixado para `output_path`.

6. **Se o município não tiver emissão online**, exigir cadastro/login
   prévio no portal do contribuinte (não só a consulta pública), ou não
   for possível concluir por qualquer motivo técnico após uma segunda
   tentativa, pare e reporte como indisponível — não tente criar cadastro
   ou contornar exigências de autenticação em nome do usuário.

## O que reportar ao final

- `status`: `"sucesso"` ou `"indisponivel"`.
- Se sucesso: resultado da certidão, município/UF, URL do portal usado e
  caminho do PDF salvo.
- Se indisponível: motivo específico (sem portal online encontrado, exige
  Inscrição Municipal não fornecida, exige login/cadastro prévio, portal
  fora do ar, captcha não resolvido, etc.) — este motivo é o que a skill
  `cnd-pipeline` vai repassar ao usuário no aviso final.

Uma certidão **Positiva** (com débito) não é falha desta skill — é o
resultado real. Só marque `indisponivel` quando o PDF de fato não pôde ser
gerado.
