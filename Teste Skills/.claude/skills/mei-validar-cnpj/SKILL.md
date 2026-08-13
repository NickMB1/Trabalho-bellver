---
name: mei-validar-cnpj
description: Valida o formato e o dígito verificador de um CNPJ de MEI antes de qualquer consulta ou emissão de guia. Use sempre que precisar confirmar que um CNPJ é válido antes de prosseguir — isoladamente ou como primeiro passo do fluxo orquestrado pela skill mei-guia-pipeline.
---

# mei-validar-cnpj

Valida um CNPJ (formato de 14 dígitos e dígito verificador) sem acessar
nenhum portal externo. É um passo puramente local e determinístico — não
depende de rede nem de automação de navegador.

## Entrada esperada

- `cnpj`: string com o CNPJ, com ou sem máscara (`.`, `/`, `-`).

## Passo a passo

1. Rode:
   ```
   python <diretório-desta-skill>/scripts/validar_cnpj.py <cnpj>
   ```
2. Se o script sair com código 0: o CNPJ é válido. A saída (stdout) é o
   CNPJ normalizado, só com os 14 dígitos — use essa forma normalizada nos
   próximos passos/skills, nunca a string original com máscara.
3. Se o script sair com código 1 (stderr traz o motivo — quantidade errada
   de dígitos, todos os dígitos iguais, ou dígito verificador não confere):
   pare e avise o usuário do motivo. Não prossiga para nenhuma outra etapa
   com um CNPJ inválido.

## O que reportar ao final

- `status`: `"valido"` ou `"invalido"`.
- Se válido: `cnpj_normalizado` (14 dígitos, sem máscara).
- Se inválido: o motivo exato reportado pelo script.

Esta skill não confirma que o CNPJ existe na base da Receita Federal nem
que a empresa é de fato um MEI — apenas que o número está bem formado. A
existência/enquadramento real só é confirmada no portal, na etapa de
emissão do DAS (skill `mei-emitir-das`).
