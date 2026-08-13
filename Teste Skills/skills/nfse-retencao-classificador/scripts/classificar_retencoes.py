#!/usr/bin/env python3
"""
Classifica, para cada nota de NFS-e já identificada (JSON do
nfse-retencao-identificador), o tipo e o valor de cada retenção presente.

Uso:
    python classificar_retencoes.py --input notas_identificadas.json --output notas_classificadas.json
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

# (chave aninhada do valor, rótulo de classificação, base legal/observação,
#  chave aninhada do município a que a retenção se refere - só faz sentido
#  para ISSQN, que é um tributo municipal; retenções federais usam None)
CLASSIFICATION_RULES = [
    (("tributacao_federal", "irrf"), "IRRF",
     "Imposto de Renda Retido na Fonte (federal)", None),
    (("tributacao_federal", "inss_retido"), "INSS (Contribuição Previdenciária Retida)",
     "Retenção previdenciária sobre serviços com cessão de mão de obra (federal)", None),
    (("tributacao_federal", "contrib_sociais_retidas"), "PIS/COFINS/CSLL (Contribuições Sociais Retidas)",
     "Retenção unificada de PIS, COFINS e CSLL - Lei 10.833/2003 (federal)", None),
    (("valor_total", "issqn_retido"), "ISSQN Retido",
     "ISS retido na fonte pelo tomador (municipal)",
     ("tributacao_municipal", "municipio_incidencia_issqn")),
]


def get_nested(record, path):
    v = record
    for key in path:
        if not isinstance(v, dict):
            return None
        v = v.get(key)
    return v


def main():
    parser = argparse.ArgumentParser(description="Classifica o tipo de retenção de cada nota de NFS-e")
    parser.add_argument("--input", required=True, help="JSON gerado pelo nfse-retencao-identificador")
    parser.add_argument("--output", required=True, help="Caminho do JSON de saída")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERRO: arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    tipo_counter = Counter()
    tipo_totais = Counter()

    for record in records:
        retencoes = []
        if record.get("tem_retencao"):
            for path, tipo, observacao, municipio_path in CLASSIFICATION_RULES:
                valor = get_nested(record, path)
                if isinstance(valor, (int, float)) and valor > 0:
                    municipio = get_nested(record, municipio_path) if municipio_path else None
                    retencoes.append({
                        "tipo": tipo,
                        "valor": valor,
                        "observacao": observacao,
                        "municipio": municipio,
                    })
                    tipo_counter[tipo] += 1
                    tipo_totais[tipo] += valor
        record["retencoes"] = retencoes

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print("Resumo por tipo de retenção:")
    if not tipo_counter:
        print("  Nenhuma retenção encontrada no lote.")
    for tipo, count in tipo_counter.most_common():
        print(f"  - {tipo}: {count} nota(s), total R$ {tipo_totais[tipo]:,.2f}")
    print(f"JSON salvo em: {output_path.resolve()}")


if __name__ == "__main__":
    main()
