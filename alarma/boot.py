"""Lê a hora em que o computador ligou, a partir de /proc/stat."""

from datetime import datetime


def ler_boot() -> datetime:
    with open("/proc/stat", encoding="ascii") as registro:
        for linha in registro:
            if linha.startswith("btime "):
                instante = int(linha.split()[1])
                return datetime.fromtimestamp(instante).astimezone()
    raise RuntimeError("btime ausente em /proc/stat")
