#!/usr/bin/env python3
"""
Localiza, dentro da árvore de uma pasta de origem (tipicamente a pasta de
um mês, ex.: "06-2026"), a(s) subpasta(s) de uma competência específica
(padrão <ano>/<mês>, ex.: ".../XML/<empresa>/2026/07") — que ficaram
estacionadas na pasta de mês errada — e move TODO o conteúdo delas
(XML, PDF, qualquer arquivo, preservando subpastas como "Recebidas"/
"Emitidas") para o mesmo caminho relativo dentro da pasta de destino
(a pasta do mês correto).

Uso:
    python mover_xmls.py --origem <pasta-mes-origem> --destino <pasta-mes-destino> --competencia 07/2026
    python mover_xmls.py --origem <pasta-mes-origem> --destino <pasta-mes-destino> --competencia 07 --ano 2026
    python mover_xmls.py --origem <pasta-mes-origem> --destino <pasta-mes-destino> --competencia 07/2026 --dry-run

--competencia: mês da competência a mover. Aceita "MM", "MM/AAAA" ou
    "AAAA/MM". Se o ano não vier junto, use --ano (ou, na falta dele, o
    script tenta inferir o ano a partir do nome da pasta de origem, ex.:
    "06-2026" -> ano 2026).

O script procura, recursivamente, por qualquer subpasta cujo nome seja o
mês (2 dígitos) e cujo pai seja uma pasta com o nome do ano (4 dígitos) —
o padrão observado nas árvores de XML desta estrutura de pastas
(".../XML/<empresa>/<ano>/<mes>/..."). Cada ocorrência encontrada é
movida inteira (arquivos e subpastas) para o destino, no mesmo caminho
relativo à pasta de origem. Depois de mover, as pastas que ficaram vazias
no lado da origem são removidas.

Se um arquivo de mesmo nome já existir no destino, ele é pulado (não
sobrescreve) e listado em "conflitos" — nesse caso a pasta correspondente
na origem pode não ficar totalmente vazia, e por segurança não é removida.

--dry-run: só lista o que seria movido/removido, sem tocar em nada.
"""
import argparse
import re
import shutil
import sys
from pathlib import Path


def parse_competencia(competencia, ano_arg, origem):
    partes = [p for p in re.split(r"[/-]", competencia) if p]
    mes = ano = None
    for parte in partes:
        if len(parte) == 4 and parte.isdigit():
            ano = parte
        elif parte.isdigit():
            mes = parte.zfill(2)
    if mes is None:
        print(f"ERRO: não consegui identificar o mês em --competencia '{competencia}'", file=sys.stderr)
        sys.exit(1)
    if ano is None and ano_arg:
        ano = str(ano_arg)
    if ano is None:
        m = re.search(r"(20\d{2})", origem.name)
        if m:
            ano = m.group(1)
    if ano is None:
        print("ERRO: não foi possível determinar o ano da competência — informe --ano.", file=sys.stderr)
        sys.exit(1)
    return mes, ano


def encontrar_pastas_competencia(origem, mes, ano):
    encontradas = []
    for caminho in origem.rglob(mes):
        if caminho.is_dir() and caminho.parent.name == ano:
            encontradas.append(caminho)
    return encontradas


def mover_arvore(pasta_origem, pasta_destino, dry_run):
    """Move todo o conteúdo de pasta_origem para pasta_destino, mesclando
    se pasta_destino já existir. Retorna (movidos, conflitos)."""
    movidos, conflitos = [], []
    if not pasta_destino.exists():
        if dry_run:
            print(f"[dry-run] moveria pasta inteira {pasta_origem} -> {pasta_destino}")
            for arquivo in pasta_origem.rglob("*"):
                if arquivo.is_file():
                    movidos.append(arquivo)
            return movidos, conflitos
        pasta_destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(pasta_origem), str(pasta_destino))
        movidos = [p for p in pasta_destino.rglob("*") if p.is_file()]
        return movidos, conflitos

    # destino já existe: mescla arquivo a arquivo
    for arquivo in sorted(pasta_origem.rglob("*")):
        if not arquivo.is_file():
            continue
        rel = arquivo.relative_to(pasta_origem)
        destino_arquivo = pasta_destino / rel
        if destino_arquivo.exists():
            conflitos.append(arquivo)
            continue
        if dry_run:
            print(f"[dry-run] moveria {arquivo} -> {destino_arquivo}")
        else:
            destino_arquivo.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(arquivo), str(destino_arquivo))
        movidos.append(arquivo)
    return movidos, conflitos


def limpar_vazias(pasta, limite):
    """Remove pasta e seus pais (até, mas sem incluir, `limite`) enquanto
    estiverem vazios."""
    removidas = []
    atual = pasta
    while atual != limite and limite in atual.parents:
        if not atual.exists():
            atual = atual.parent
            continue
        if any(atual.iterdir()):
            break
        atual.rmdir()
        removidas.append(atual)
        atual = atual.parent
    return removidas


def main():
    parser = argparse.ArgumentParser(
        description="Move os arquivos de uma competência (ano/mês) estacionada na árvore de XML de uma pasta de mês errada para a pasta de mês correta"
    )
    parser.add_argument("--origem", required=True, help="Pasta do mês de origem (onde os arquivos estão mal posicionados)")
    parser.add_argument("--destino", required=True, help="Pasta do mês de destino (pasta correta para a competência)")
    parser.add_argument("--competencia", required=True, help="Mês da competência a mover: 'MM', 'MM/AAAA' ou 'AAAA/MM'")
    parser.add_argument("--ano", help="Ano da competência, se não vier junto em --competencia")
    parser.add_argument("--dry-run", action="store_true", help="Só lista o que seria feito, sem mover nem remover nada")
    args = parser.parse_args()

    origem = Path(args.origem)
    destino = Path(args.destino)

    if not origem.exists() or not origem.is_dir():
        print(f"ERRO: pasta de origem não encontrada: {origem}", file=sys.stderr)
        sys.exit(1)
    if not destino.exists() or not destino.is_dir():
        print(f"ERRO: pasta de destino não encontrada: {destino}", file=sys.stderr)
        sys.exit(1)

    mes, ano = parse_competencia(args.competencia, args.ano, origem)
    pastas = encontrar_pastas_competencia(origem, mes, ano)

    if not pastas:
        print(f"Nenhuma pasta de competência {mes}/{ano} encontrada dentro de {origem}.")
        return

    total_movidos, total_conflitos = [], []
    for pasta_comp in pastas:
        rel = pasta_comp.relative_to(origem)
        destino_comp = destino / rel
        print(f"\n=== Competência {mes}/{ano} encontrada em: {pasta_comp} ===")
        movidos, conflitos = mover_arvore(pasta_comp, destino_comp, args.dry_run)
        total_movidos.extend(movidos)
        total_conflitos.extend(conflitos)

        if not args.dry_run and not conflitos:
            removidas = limpar_vazias(pasta_comp.parent, origem)
            for p in removidas:
                print(f"  pasta vazia removida: {p}")
        elif not args.dry_run and conflitos:
            print(f"  aviso: pasta de origem não removida por causa de conflitos: {pasta_comp}")

    prefixo = "[dry-run] seriam " if args.dry_run else ""
    print(f"\n{prefixo}{len(total_movidos)} arquivo(s) movido(s) de {origem} para {destino} (competência {mes}/{ano}):")
    for arquivo in total_movidos:
        print(f"  - {arquivo.name}")

    if total_conflitos:
        print(f"\n{len(total_conflitos)} arquivo(s) NÃO movido(s) por já existir arquivo de mesmo nome no destino:")
        for arquivo in total_conflitos:
            print(f"  - {arquivo}")


if __name__ == "__main__":
    main()
