#!/usr/bin/env python3
import re
import sys


def validar_cnpj(cnpj: str) -> tuple[bool, str]:
    digitos = re.sub(r"\D", "", cnpj)

    if len(digitos) != 14:
        return False, f"CNPJ tem {len(digitos)} dígitos, deveria ter 14."

    if digitos == digitos[0] * 14:
        return False, "CNPJ inválido (todos os dígitos iguais)."

    def calcular_dv(base: str) -> str:
        ciclo = [2, 3, 4, 5, 6, 7, 8, 9]
        pesos = [ciclo[i % 8] for i in range(len(base))][::-1]
        soma = sum(int(d) * p for d, p in zip(base, pesos))
        resto = soma % 11
        return "0" if resto < 2 else str(11 - resto)

    dv1 = calcular_dv(digitos[:12])
    dv2 = calcular_dv(digitos[:12] + dv1)

    if digitos[-2:] != dv1 + dv2:
        return False, "CNPJ inválido (dígito verificador não confere)."

    return True, digitos


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: validar_cnpj.py <cnpj>", file=sys.stderr)
        sys.exit(2)

    ok, resultado = validar_cnpj(sys.argv[1])
    if ok:
        print(resultado)
        sys.exit(0)
    else:
        print(resultado, file=sys.stderr)
        sys.exit(1)
