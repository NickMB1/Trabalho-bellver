---
name: nfse-limpeza-executor
description: Move (para uma pasta de backup, reversível) ou remove definitivamente do disco os XMLs de NFS-e do Ambiente Nacional já marcados como "Cancelada" ou "Substituída" pela skill nfse-evento-identificador. Use depois de rodar a nfse-evento-identificador e de o usuário CONFIRMAR a lista de arquivos afetados — isoladamente, ou como último passo do fluxo orquestrado pela skill nfse-limpeza-pipeline. É uma ação destrutiva/difícil de reverter (--acao remover apaga o arquivo do disco); nunca rode sem antes mostrar a lista ao usuário e obter aprovação explícita.
---

# nfse-limpeza-executor

Move ou apaga do disco os XMLs de nota que a skill `nfse-evento-identificador`
já classificou como `situacao: "Cancelada"` ou `situacao: "Substituída"`, usando
o script `scripts/executar_limpeza.py`.

## Antes de rodar: confirme com o usuário

Esta skill só deve ser chamada depois que o usuário **já viu a lista** de
arquivos que serão afetados (arquivo, situação, evento responsável — o
resumo que `nfse-evento-identificador` imprime) e confirmou explicitamente
que quer prosseguir. Apagar/mover XMLs fiscais é uma operação sensível — não
rode esta skill de forma proativa só porque o identificador achou notas
canceladas.

Se o usuário não deixou claro se prefere **mover** (reversível, recomendado
por padrão) ou **remover definitivamente**, pergunte antes de escolher —
não assuma remoção definitiva sem confirmação, mesmo que o usuário tenha
dito "remove os XMLs" de forma genérica no início da conversa: confirme se
ele quer dizer "tirar da pasta" (mover) ou "apagar de vez".

## Como usar

Mover para uma pasta de backup (padrão recomendado — reversível, nada é
perdido):

```
python <diretório-desta-skill>/scripts/executar_limpeza.py --input situacao_notas.json --acao mover --destino <pasta-de-backup>
```

Cada arquivo vai para `<destino>/Cancelada/<arquivo>` ou
`<destino>/Substituida/<arquivo>`, saindo do lugar original mas continuando
íntegro e recuperável.

Remover definitivamente (irreversível):

```
python <diretório-desta-skill>/scripts/executar_limpeza.py --input situacao_notas.json --acao remover --confirmar
```

Rodar `--acao remover` **sem** `--confirmar` é seguro por design: o script
só lista o que apagaria e não toca em nenhum arquivo — use isso como uma
prévia para mostrar ao usuário antes de rodar com `--confirmar` de verdade.
Qualquer ação também aceita `--dry-run`, que nunca altera nada e serve para
conferir os caminhos de destino antes de mexer em arquivos de verdade.

- `--input`: o JSON gerado pela skill `nfse-evento-identificador`.
- `--acao`: `mover` (exige `--destino`) ou `remover`.
- `--destino`: pasta-raiz de backup, só para `--acao mover`.
- `--confirmar`: obrigatório para `--acao remover` executar de fato.
- `--dry-run`: só imprime o que seria feito, em qualquer ação.

## O que NÃO é afetado

Notas com `situacao: "Ativa"` nunca são tocadas, mesmo que estejam no mesmo
JSON de entrada — só `Cancelada` e `Substituída` são elegíveis. Os XMLs de
**evento** em si (pasta "Eventos") também não são movidos/apagados por esta
skill — eles documentam o histórico de cancelamento e não fazem parte do
alvo da limpeza.

## Depois de rodar

Repasse ao usuário o resumo que o script já imprime (quantos arquivos foram
movidos/apagados, para onde, e quais não foram encontrados no caminho
original — sinal de que já tinham sido processados antes). Se algum arquivo
constar como "não encontrado", não trate como erro fatal do lote: avise e
siga em frente com o restante.
