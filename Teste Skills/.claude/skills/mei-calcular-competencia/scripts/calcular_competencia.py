#!/usr/bin/env python3
import datetime
import sys

MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def calcular(hoje: datetime.date) -> dict:
    ano_comp = hoje.year
    mes_comp = hoje.month - 1
    if mes_comp == 0:
        mes_comp = 12
        ano_comp -= 1

    return {
        "competencia": f"{mes_comp:02d}/{ano_comp}",
        "competencia_extenso": f"{MESES[mes_comp - 1]}/{ano_comp}",
        "vencimento_mes_extenso": f"{MESES[hoje.month - 1]}/{hoje.year}",
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        hoje = datetime.date.fromisoformat(sys.argv[1])
    else:
        hoje = datetime.date.today()

    resultado = calcular(hoje)
    for chave, valor in resultado.items():
        print(f"{chave}={valor}")
