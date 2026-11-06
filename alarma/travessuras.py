"""O que o rato apronta. Nunca digita em janela alheia nem mata processo."""

import random
import subprocess
from pathlib import Path

from alarma import hypr

URL_QUEIJO = "https://www.youtube.com/watch?v=WRlCEiGFEFM"
TEXTO_NOTAS = (
    "querido diário,\n\n"
    "fugi da gaiola de novo.\n"
    "você ainda não bateu o ponto.\n"
    "enquanto isso, vou procurar queijo.\n\n"
    "queijo queijo queijo queijo queijo\n\n"
    "assinado: o rato\n"
)
SAIDA_DE_SOM = "@DEFAULT_AUDIO_SINK@"
MAX_JANELAS = 2
DESLOCAMENTO = 120
DIRECOES = ("l", "r", "u", "d")


def _rodar(*comando: str) -> None:
    """Falha de um programa externo não pode derrubar o alarme."""
    try:
        subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def abrir_youtube() -> None:
    _rodar("xdg-open", URL_QUEIJO)


def esta_mudo() -> bool:
    try:
        saida = subprocess.run(
            ["wpctl", "get-volume", SAIDA_DE_SOM],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return "[MUTED]" in saida.stdout


def mutar(marca: Path) -> None:
    """Muta e deixa a marca. Sem marca o som não voltaria, então sem ela não muta."""
    if not marca.exists() and not esta_mudo():
        try:
            marca.parent.mkdir(parents=True, exist_ok=True)
            marca.touch()
        except OSError:
            return
    _rodar("wpctl", "set-mute", SAIDA_DE_SOM, "1")


def restaurar_som(marca: Path) -> None:
    """Desfaz só o mudo do rato: o que a pessoa mutou continua mudo."""
    if not marca.exists():
        return
    _rodar("wpctl", "set-mute", SAIDA_DE_SOM, "0")
    marca.unlink(missing_ok=True)


def _alvos(clientes: list[dict], workspace: int | None, meu_pid: int) -> list[dict]:
    """Janelas alheias e visíveis do workspace atual, fora as de tela cheia."""
    return [
        c
        for c in clientes
        if c.get("pid") != meu_pid
        and c.get("workspace", {}).get("id") == workspace
        and c.get("mapped", True)
        and not c.get("fullscreen")
    ]


def comandos_janelas(
    clientes: list[dict],
    workspace: int | None,
    meu_pid: int,
    acaso: random.Random,
) -> list[str]:
    """Monta os comandos que bagunçam até MAX_JANELAS do workspace atual."""
    alvos = _alvos(clientes, workspace, meu_pid)
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


def comando_fechar(
    clientes: list[dict],
    workspace: int | None,
    meu_pid: int,
    acaso: random.Random,
) -> str | None:
    """Sorteia uma janela do workspace atual. Pede para fechar, sem matar o processo."""
    alvos = _alvos(clientes, workspace, meu_pid)
    if not alvos:
        return None
    alvo = acaso.choice(alvos)
    return f"hl.dsp.window.close({{ window = 'address:{alvo['address']}' }})"


def fechar_janela(meu_pid: int, acaso: random.Random) -> None:
    comando = comando_fechar(hypr.clientes(), hypr.workspace_ativo(), meu_pid, acaso)
    if comando is not None:
        hypr.despachar(comando)
