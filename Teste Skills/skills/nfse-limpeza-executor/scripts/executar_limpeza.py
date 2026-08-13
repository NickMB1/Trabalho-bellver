#!/usr/bin/env python3
"""
Move ou remove os XMLs de nota marcados como "Cancelada"/"Substituída" no
JSON produzido pela skill nfse-evento-identificador.

Uso:
    python executar_limpeza.py --input situacao_notas.json --acao mover --destino <pasta>
    python executar_limpeza.py --input situacao_notas.json --acao remover --confirmar
    python executar_limpeza.py --input situacao_notas.json --acao mover --destino <pasta> --dry-run

--acao mover (recomendado, reversível): move cada XML para
    <destino>/Cancelada/<arquivo> ou <destino>/Substituida/<arquivo>,
    preservando o arquivo original intacto (só muda de lugar).
--acao remover (irreversível): apaga o arquivo do disco. Exige --confirmar
    (sem essa flag, o script só lista o que apagaria e não faz nada) --
    dando ao usuário uma chance explícita de revisar a lista antes do
    apagamento definitivo.
--dry-run: em qualquer ação, só imprime o que seria feito, sem tocar em
    nenhum arquivo.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

SITUACOES_ALVO = {"Cancelada", "Substituída"}


def main():
    parser = argparse.ArgumentParser(
        description="Move ou remove XMLs de notas Canceladas/Substituídas (JSON do nfse-evento-identificador)"
    )
    parser.add_argument("--input", required=True, help="JSON gerado pelo nfse-evento-identificador")
    parser.add_argument("--acao", required=True, choices=["mover", "remover"], help="mover (reversível) ou remover (definitivo)")
    parser.add_argument("--destino", help="Pasta de destino (obrigatório se --acao mover)")
    parser.add_argument("--confirmar", action="store_true", help="Obrigatório para --acao remover realmente apagar arquivos")
    parser.add_argument("--dry-run", action="store_true", help="Só lista o que seria feito, sem alterar nada")
    args = parser.parse_args()

    if args.acao == "mover" and not args.destino:
        print("ERRO: --destino é obrigatório quando --acao mover", file=sys.stderr)
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERRO: arquivo não encontrado: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    notas = data.get("notas", data if isinstance(data, list) else [])

    alvo = [n for n in notas if n.get("situacao") in SITUACOES_ALVO]
    if not alvo:
        print("Nenhuma nota Cancelada/Substituída encontrada no JSON de entrada -- nada a fazer.")
        return

    if args.acao == "remover" and not args.confirmar and not args.dry_run:
        print(f"{len(alvo)} arquivo(s) seriam APAGADOS DEFINITIVAMENTE (nenhuma cópia é mantida):")
        for n in alvo:
            print(f"  - {n['arquivo']} ({n['situacao']}) -> {n.get('arquivo_caminho')}")
        print("\nNenhum arquivo foi tocado. Rode de novo com --confirmar para executar,")
        print("ou use --acao mover para uma alternativa reversível.")
        return

    processados, faltando = [], []
    for nota in alvo:
        origem = Path(nota["arquivo_caminho"])
        if not origem.exists():
            faltando.append(nota["arquivo"])
            continue

        if args.acao == "mover":
            subpasta = "Cancelada" if nota["situacao"] == "Cancelada" else "Substituida"
            destino_dir = Path(args.destino) / subpasta
            destino_path = destino_dir / origem.name
            if args.dry_run:
                print(f"[dry-run] moveria {origem} -> {destino_path}")
            else:
                destino_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(origem), str(destino_path))
            processados.append((nota["arquivo"], nota["situacao"], str(destino_path)))
        else:  # remover
            if args.dry_run:
                print(f"[dry-run] apagaria {origem}")
            else:
                origem.unlink()
            processados.append((nota["arquivo"], nota["situacao"], None))

    verbo = "movido(s)" if args.acao == "mover" else "apagado(s)"
    prefixo = "[dry-run] seriam " if args.dry_run else ""
    print(f"{prefixo}{len(processados)} XML(s) {verbo}:")
    for arquivo, situacao, destino in processados:
        if destino:
            print(f"  - {arquivo} ({situacao}) -> {destino}")
        else:
            print(f"  - {arquivo} ({situacao})")
    if faltando:
        print(f"Não encontrados no caminho original (já movidos/apagados antes?): {len(faltando)}")
        for arquivo in faltando:
            print(f"  - {arquivo}")


if __name__ == "__main__":
    main()
