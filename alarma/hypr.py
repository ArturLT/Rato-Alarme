"""Conversa com o Hyprland. Falhas viram None: o alarme não pode cair por isso."""

import json
import subprocess

PROPRIEDADES = (
    ("no_anim", "true"),
    ("border_size", "0"),
    ("no_shadow", "true"),
    ("no_blur", "true"),
    ("rounding", "0"),
    ("opaque", "false"),
)


def _rodar(*argumentos: str) -> str | None:
    try:
        saida = subprocess.run(
            ["hyprctl", *argumentos],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return saida.stdout if saida.returncode == 0 else None


def _json(*argumentos: str) -> object:
    saida = _rodar(*argumentos, "-j")
    if saida is None:
        return None
    try:
        return json.loads(saida)
    except ValueError:
        return None


def despachar(comando: str) -> bool:
    return (_rodar("dispatch", comando) or "").strip() == "ok"


def cursor() -> tuple[int, int] | None:
    dados = _json("cursorpos")
    if not isinstance(dados, dict):
        return None
    return int(dados["x"]), int(dados["y"])


def clientes() -> list[dict]:
    dados = _json("clients")
    return dados if isinstance(dados, list) else []


def workspace_ativo() -> int | None:
    dados = _json("activeworkspace")
    return dados.get("id") if isinstance(dados, dict) else None


def area_do_cursor(posicao: tuple[int, int] | None) -> tuple[int, int, int, int] | None:
    monitores = _json("monitors")
    if not isinstance(monitores, list) or not monitores:
        return None
    for monitor in monitores:
        x0, y0 = monitor["x"], monitor["y"]
        x1 = x0 + int(monitor["width"] / monitor["scale"])
        y1 = y0 + int(monitor["height"] / monitor["scale"])
        if posicao is None and monitor.get("focused"):
            return x0, y0, x1, y1
        if posicao is not None and x0 <= posicao[0] < x1 and y0 <= posicao[1] < y1:
            return x0, y0, x1, y1
    return None


def monitores() -> list[tuple[int, int, int, int]]:
    dados = _json("monitors")
    if not isinstance(dados, list):
        return []
    saida = []
    for m in dados:
        try:
            x0, y0 = int(m["x"]), int(m["y"])
            saida.append((x0, y0, x0 + int(m["width"] / m["scale"]), y0 + int(m["height"] / m["scale"])))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
    return saida


def endereco(pid: int, titulo: str) -> str | None:
    for cliente in clientes():
        if cliente.get("pid") == pid and cliente.get("title") == titulo:
            return cliente["address"]
    return None


def preparar(janela: str) -> None:
    """Fixa o rato em todos os workspaces, sem moldura nem animação de janela."""
    alvo = f"window = 'address:{janela}'"
    despachar(f"hl.dsp.window.pin({{ action = 'on', {alvo} }})")
    for propriedade, valor in PROPRIEDADES:
        despachar(
            f"hl.dsp.window.set_prop({{ prop = '{propriedade}', value = '{valor}', {alvo} }})"
        )


def mover(janela: str, x: int, y: int) -> bool:
    return despachar(
        f"hl.dsp.window.move({{ x = {x}, y = {y}, relative = false, "
        f"window = 'address:{janela}' }})"
    )
