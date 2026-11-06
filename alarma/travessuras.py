"""O que o rato apronta. Só abre e mexe: nunca fecha nem digita em janela alheia."""

import random
import subprocess
from urllib.parse import urlencode

from alarma import hypr

BUSCA = "vídeos de queijo"
TEXTO_NOTAS = (
    "querido diário,\n\n"
    "fugi da gaiola de novo.\n"
    "você ainda não bateu o ponto.\n"
    "enquanto isso, vou procurar queijo.\n\n"
    "queijo queijo queijo queijo queijo\n\n"
    "assinado: o rato\n"
)
MAX_JANELAS = 2
DESLOCAMENTO = 120
DIRECOES = ("l", "r", "u", "d")


def url_youtube() -> str:
    return "https://www.youtube.com/results?" + urlencode({"search_query": BUSCA})


def abrir_youtube() -> None:
    subprocess.Popen(
        ["xdg-open", url_youtube()],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def comandos_janelas(
    clientes: list[dict],
    workspace: int | None,
    meu_pid: int,
    acaso: random.Random,
) -> list[str]:
    """Monta os comandos que bagunçam até MAX_JANELAS do workspace atual."""
    alvos = [
        c
        for c in clientes
        if c.get("pid") != meu_pid
        and c.get("workspace", {}).get("id") == workspace
        and c.get("mapped", True)
        and not c.get("fullscreen")
    ]
    acaso.shuffle(alvos)
    comandos = []
    for cliente in alvos[:MAX_JANELAS]:
        janela = f"window = 'address:{cliente['address']}'"
        if cliente.get("floating"):
            x = acaso.randint(-DESLOCAMENTO, DESLOCAMENTO)
            y = acaso.randint(-DESLOCAMENTO, DESLOCAMENTO)
            comandos.append(
                f"hl.dsp.window.move({{ x = {x}, y = {y}, relative = true, {janela} }})"
            )
        else:
            direcao = acaso.choice(DIRECOES)
            comandos.append(f"hl.dsp.window.move({{ direction = '{direcao}', {janela} }})")
    return comandos


def mexer_janelas(meu_pid: int, acaso: random.Random) -> None:
    for comando in comandos_janelas(
        hypr.clientes(), hypr.workspace_ativo(), meu_pid, acaso
    ):
        hypr.despachar(comando)
