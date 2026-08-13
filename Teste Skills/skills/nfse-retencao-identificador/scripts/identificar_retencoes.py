#!/usr/bin/env python3
"""
Identifica, entre notas de NFS-e já extraídas (JSON do nfse-extrator), quais
têm alguma retenção de tributo.

Uso:
    python identificar_retencoes.py --input notas_extraidas.json --output notas_identificadas.json
"""
import argparse
import json
import sys
from pathlib import Path

# Campos de retenção existentes no schema do nfse-extrator, com o caminho
# (chave aninhada) onde cada valor mora no registro da nota.
RETENTION_FIELDS = [
    ("irrf", ("tributacao_federal", "irrf")),
    ("inss_retido", ("tributacao_federal", "inss_retido")),
    ("contrib_sociais_retidas", ("tributacao_federal", "contrib_sociais_retidas")),
    ("issqn_retido", ("valor_total", "issqn_retido")),
]

# Notas Canceladas/Substituídas não têm obrigação fiscal real -- os valores
# de retenção que ainda aparecem impressos no PDF não entram na contagem nem
# no total (mas a nota continua no relatório, com a situação marcada, para
# rastreabilidade). "Ativa" e None (DANFSe v1.0, que não tem esse campo)
# contam normalmente.
SITUACOES_QUE_CONTAM = {None, "Ativa"}


def get_nested(record, path):
    v = record
    for key in path:
        if not isinstance(v, dict):
            return None
        v = v.get(key)
    return v


def main():
    parser = argparse.ArgumentParser(description="Identifica notas de NFS-e com retenção de tributos")
    parser.add_argument("--input", required=True, help="JSON gerado pelo nfse-extrator")
    parser.add_argument("--output", required=True, help="Caminho do JSON de saída")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERRO: arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    com_retencao = 0
    anuladas_por_situacao = []
    for record in records:
        total = 0.0
        for _, path in RETENTION_FIELDS:
            v = get_nested(record, path)
            if isinstance(v, (int, float)) and v > 0:
                total += v

        conta = record.get("situacao") in SITUACOES_QUE_CONTAM
        record["tem_retencao"] = total > 0 and conta
        record["valor_total_retencoes"] = round(total, 2) if record["tem_retencao"] else None
        if record["tem_retencao"]:
            com_retencao += 1
        elif total > 0 and not conta:
            anuladas_por_situacao.append((record.get("arquivo"), record.get("situacao"), round(total, 2)))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Total de notas: {len(records)}")
    print(f"Notas com retenção: {com_retencao}")
    print(f"Notas sem retenção: {len(records) - com_retencao - len(anuladas_por_situacao)}")
    if anuladas_por_situacao:
        print(f"Notas com retenção no PDF mas excluídas do total (Cancelada/Substituída): {len(anuladas_por_situacao)}")
        for arquivo, situacao, valor in anuladas_por_situacao:
            print(f"  - {arquivo} ({situacao}): R$ {valor:,.2f} não contabilizado")
    print(f"JSON salvo em: {output_path.resolve()}")


if __name__ == "__main__":
    main()
