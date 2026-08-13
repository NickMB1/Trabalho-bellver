---
name: simplificador-simples
description: Gera o documento visual de apuração do Simples Nacional a partir do relatório bruto em PDF salvo em doc-original/, convertendo-o primeiro para .md em transcricoes/, aplicando o template aprovado e exportando o resultado final em PDF para clientes/. Use quando o usuário pedir para "simplificar" um arquivo (ex: "simplifique o arquivo 'zaffari-julho2026.pdf'").
---

# Simplificador - Simples Nacional

## Objetivo
Transformar o relatório bruto de apuração do Simples Nacional (extrato gerado por sistema contábil, em PDF) em um documento visual compacto, de uma tela só, seguindo o template aprovado pelo usuário.

## Gatilho
O usuário aciona esse fluxo enviando uma mensagem pedindo para simplificar um arquivo, indicando o nome do PDF (ex: "simplifique o arquivo 'zaffari-julho2026.pdf'"). O arquivo referenciado deve ser localizado na pasta `doc-original/`.

## Fluxo

1. **Converter o PDF para .md**
   - Localizar o arquivo `.pdf` indicado pelo usuário dentro de `doc-original/`.
   - Ler o PDF e transcrever seu conteúdo integralmente para um arquivo `.md` na pasta `transcricoes/` (irmã de `doc-original/` e `clientes/`; criar se não existir), com o mesmo nome base do PDF (ex: `zaffari-julho2026.pdf` → `transcricoes/zaffari-julho2026.md`).
   - `doc-original/` guarda só os PDFs de origem, nunca tocados; `transcricoes/` é o estágio intermediário/auditoria; `clientes/` é a entrega final em PDF.
   - Essa conversão é sempre feita antes de qualquer extração de dados — nunca extrair campos direto do PDF sem passar por essa etapa.
   - Se o PDF não for encontrado ou não puder ser lido/convertido, parar aqui e informar o usuário (ver "Regras absolutas").

2. **Ler o relatório de origem**
   - Ler o `.md` gerado no passo 1.
   - Extrair os campos:
     - Empresa, CNPJ, Período (mês/ano)
     - Anexo (ex: "Anexo III - Prestação de Serviços")
     - RPA — Receita Bruta do Período de Apuração (faturamento do mês)
     - RBT12 — Receita bruta acumulada nos 12 meses anteriores (faturamento últ. 12 meses)
     - Faixa de Enquadramento
     - Alíquota efetiva
     - Simples Nacional Total / Simples Nacional a recolher (valor do DAS)
     - Partilha por tributo: INSS/CPP, IRPJ, CSLL, ISS, COFINS, PIS (valores) - (apenas os que não estiverem zerados)
     - Outros acréscimos, outras deduções, valor diferido, valor fixo ICMS, valor fixo ISS (apenas os que não estiverem zerados)

3. **Aplicar o template visual aprovado**
   - O modelo visual é o arquivo literal `.claude/skills/modelo-visual/template.html` — copiar esse arquivo e substituir os placeholders `{{...}}` pelos dados reais. Não redesenhar a página do zero nem reinterpretar a partir de descrição em texto (isso já causou divergência visual entre documentos).
   - Regras de preenchimento, lista de placeholders e como embutir a fonte estão em `.claude/skills/modelo-visual/simples-template.md`.
   - Não usar a versão antiga longa/multi-seção.

4. **Gerar o artifact e revisar com o usuário**
   - Mostrar o artifact para aprovação antes de salvar o arquivo final (a menos que o usuário já tenha pedido explicitamente para salvar direto).

5. **Gerar o HTML temporário**
   - Nome: `_tmp_<slug>.html`, salvo dentro da própria pasta `clientes/` (evita depender de um diretório de scratch específico de sessão).
   - Estrutura: envolver o `<title>/<style>/<div class="page">` do artifact num `<!doctype html><html><head>...</head><body>...</body></html>` completo, com `<meta charset="utf-8">` e viewport.
   - Se precisar editar um HTML grande com fonte embutida via PowerShell, nunca usar `Get-Content`/`Set-Content` sem UTF-8 explícito (corrompe acentos) — usar `[System.IO.File]::ReadAllText/WriteAllText` com `UTF8Encoding`.
   - Este arquivo é descartável — só existe para servir de origem para a conversão em PDF do passo 6, nunca é a entrega final.

6. **Converter para PDF e salvar o arquivo final**
   - Rodar o Edge headless para converter o HTML temporário em PDF:
     `"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu --no-pdf-header-footer --print-to-pdf="<caminho absoluto do .pdf final>" "file:///<caminho absoluto do .html temporário, barras normais>"`
   - Importante sobre a URL: montar sempre como `file:///` + caminho absoluto. Passar só o nome do arquivo (sem `file://`) faz o Edge tentar resolver como hostname/DNS e falha. Caracteres acentuados no caminho precisam ser percent-encoded (ex: `ç` → `%C3%A7`); espaços podem ficar literais.
   - Nome final: `Empresa - Período.pdf` (ex: `BN3 Contabilidade - Junho 2026.pdf`)
   - Local: pasta `clientes/`
   - Depois que o PDF for gerado com sucesso, apagar o `.html` temporário — a pasta `clientes/` deve conter só PDFs.
   - **Otimização de custo:** se houver mais de um arquivo para simplificar na mesma solicitação/sessão, gerar todos os HTMLs temporários primeiro e rodar todas as conversões num único comando (loop/lista de comandos em sequência), em vez de um comando separado por arquivo.

## Regras absolutas
- Proibido inventar, complementar, colocar ou "adivinhar" informações que não estejam explicitamente no documento.
- Fidelidade absoluta aos dados: nunca alterar, arredondar ou excluir valores dos campos que devem estar presentes no arquivo (fluxo 2).
- Se o relatório trouxer os campos de ajuste (Outros Acréscimos, Outras Deduções, Valor Diferido, Valor Fixo ICMS, Valor Fixo ISS) não zerados, usar o card opcional "Ajustes no valor a recolher" documentado em `.claude/skills/modelo-visual/simples-template.md` — não é mais necessário perguntar ao usuário, esse caso já tem tratamento padrão.
- Se o relatório trouxer outros campos adicionais fora do padrão (ex: substituição tributária) que não se encaixem no card de ajustes acima, perguntar ao usuário se devem ser destacados, ignorados ou tratados como caso especial antes de aplicar o template padrão.
- Em caso de dúvida, sempre consultar/perguntar para o usuário antes de fazer qualquer coisa.
- Sempre seguir o modelo visual literal em `.claude/skills/modelo-visual/template.html` (ver `.claude/skills/modelo-visual/simples-template.md` para as regras de preenchimento).
- Se você não conseguir gerar o arquivo .md, o HTML temporário ou o .pdf final por qualquer motivo, informe ao usuário que não conseguiu e diga o motivo. Se a conversão para PDF falhar, não apagar o HTML temporário — deixe-o em `clientes/` como fallback e avise o usuário.
