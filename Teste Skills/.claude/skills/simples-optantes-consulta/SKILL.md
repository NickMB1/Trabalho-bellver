---
name: simples-optantes-consulta
description: Consulta um único CNPJ na "Consulta Optantes" pelo Simples Nacional (portal oficial da Receita Federal), via automação de navegador, e retorna a situação atual (optante ou não, SIMEI) e a lista de eventos futuros agendados (ex.: exclusão de ofício, data de efeito), se houver. Use sempre que o usuário pedir para "verificar se um CNPJ tem evento futuro no Simples Nacional", "consultar a situação de um CNPJ no Simples" — isoladamente para um CNPJ, ou repetidamente como passo do fluxo em lote orquestrado pela skill simples-optantes-pipeline.
---

# simples-optantes-consulta

Consulta a situação de um CNPJ no Simples Nacional/SIMEI usando o portal
público "Consulta Optantes" da Receita Federal. Não existe API pública
para isso, então esta skill depende da skill `claude-in-chrome` para
navegar e preencher o formulário como um humano faria.

## Entrada esperada

- `cnpj`: 14 dígitos (com ou sem máscara — normalize removendo `.`, `/`,
  `-` antes de preencher o campo).
- `tabId` (opcional): id de uma aba já aberta nesse portal, de uma
  consulta anterior no mesmo lote. Quando informado, reaproveite a aba em
  vez de abrir uma nova — evita acumular dezenas de abas num lote grande.

## Passo a passo

1. **Abra/reaproveite a aba**:
   - Sem `tabId`: invoque a skill `claude-in-chrome` e navegue para
     `https://www8.receita.fazenda.gov.br/SimplesNacional/aplicacoes.aspx?id=21`.
     Guarde o `tabId` retornado para reaproveitar nas próximas consultas
     do mesmo lote.
   - Com `tabId`: navegue essa mesma aba de volta para a URL acima —
     isso reseta o formulário para a próxima consulta.

   Não tente usar a URL direta `.../ConsultaOptantes.aspx` — ela retorna
   "Página não encontrada"; o caminho válido é `aplicacoes.aspx?id=21`
   (chegado clicando em "Consulta Optantes" no rodapé do portal Simples
   Nacional).

2. **Preencha o campo CNPJ** com os 14 dígitos sem máscara e clique em
   "Consultar".

3. **Trate CNPJ inválido/não encontrado**: se a página não mostrar o
   bloco "Identificação do Contribuinte" (ex.: mensagem de erro/CNPJ
   inexistente), marque esse CNPJ como `nao_encontrado` com o texto do
   erro e siga para o próximo — não pare o lote por causa de um CNPJ
   ruim.

4. **Leia os dados básicos** no bloco "Identificação do Contribuinte" e
   "Situação Atual": `Nome Empresarial`, `Situação no Simples Nacional` e
   `Situação no SIMEI`.

5. **Clique em "+ Mais informações"** para expandir as seções ocultas
   (Períodos Anteriores, Eventos Futuros).

6. **Leia a(s) seção(ões) "Eventos Futuros"** — pode haver uma para
   "Eventos Futuros (Simples Nacional)" e outra para "Eventos Futuros
   (SIMEI)" quando aplicável. Cada uma é uma tabela com colunas
   `Descrição do Evento` e `Data Efeito`. Capture **todas** as linhas de
   ambas as tabelas quando existirem. Se a seção não aparecer na página
   (ou não tiver linhas), não há evento futuro para esse CNPJ.

   Use screenshot (role a página até o final do painel expandido) para
   ler essa tabela — `get_page_text` não é confiável nesse portal
   (retornou conteúdo vazio/incorreto em teste). `read_page` com
   `filter: "all"` também funciona se preferir extrair via árvore de
   acessibilidade em vez de imagem.

## O que reportar ao final (por CNPJ)

Sempre devolva um registro estruturado, mesmo quando chamado dentro do
lote:

```json
{
  "cnpj": "27882761000170",
  "status": "sucesso",
  "razao_social": "IMPERTOLDOS COBERTURAS E IMPERMEABILIZACOES LTDA",
  "situacao_simples": "Optante pelo Simples Nacional desde 01/06/2017",
  "situacao_simei": "NÃO enquadrado no SIMEI",
  "eventos_futuros": [
    {"descricao": "Exclusão de Ofício - Débitos", "data_efeito": "01/01/2027"}
  ],
  "tabId": 669098263
}
```

- `status`: `"sucesso"` ou `"nao_encontrado"`.
- Se `nao_encontrado`: inclua `motivo` com o texto exibido pelo portal.
- `eventos_futuros`: lista vazia (`[]`) quando não houver nenhum evento
  agendado — nunca omita o campo.
- `tabId`: sempre devolva o id da aba usada, para a próxima chamada do
  lote reaproveitar.

## Limitações conhecidas

- O portal não tem CAPTCHA na consulta simples, mas se algum desafio
  anti-robô aparecer, pare e peça para o usuário resolver manualmente —
  nunca tente contornar.
- Se o portal estiver fora do ar ou não responder após uma segunda
  tentativa, marque como `nao_encontrado` com motivo "portal
  indisponível" e siga em frente — não trave o lote inteiro por um CNPJ.
