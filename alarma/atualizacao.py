"""Procura versão nova nos Releases do GitHub. Sem internet, fica tudo como está."""

import json
import ssl
import urllib.request
from dataclasses import dataclass

from alarma.versao import VERSAO

REPOSITORIO = "ArturLT/Rato-Alarme"
URL_ULTIMA = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
ESPERA_S = 10


@dataclass(frozen=True)
class Lancamento:
    versao: str
    pagina: str
    download: str | None


def numeros(versao: object) -> tuple[int, ...] | None:
    if not isinstance(versao, str):
        return None
    try:
        return tuple(int(parte) for parte in versao.removeprefix("v").split("."))
    except ValueError:
        return None


def mais_nova(versao: object, atual: str) -> bool:
    nova, instalada = numeros(versao), numeros(atual)
    return nova is not None and instalada is not None and nova > instalada


def nome_do_instalador(sistema: str, maquina: str) -> str | None:
    if sistema == "win32":
        return "Rato-Alarme-Windows.exe"
    if sistema == "darwin":
        chip = "AppleSilicon" if maquina == "arm64" else "Intel"
        return f"Rato-Alarme-macOS-{chip}.dmg"
    return None


def interpretar(dados: object, atual: str, sistema: str, maquina: str) -> Lancamento | None:
    """Devolve o lançamento só se ele for mais novo que a versão instalada."""
    if not isinstance(dados, dict) or dados.get("prerelease") or dados.get("draft"):
        return None
    tag = dados.get("tag_name")
    pagina = dados.get("html_url")
    if not mais_nova(tag, atual) or not isinstance(pagina, str):
        return None
    instalador = nome_do_instalador(sistema, maquina)
    ativos = dados.get("assets")
    download = next(
        (
            ativo.get("browser_download_url")
            for ativo in (ativos if isinstance(ativos, list) else [])
            if isinstance(ativo, dict) and ativo.get("name") == instalador
        ),
        None,
    )
    return Lancamento(tag.removeprefix("v"), pagina, download)


def _contexto_tls() -> ssl.SSLContext:
    """O Python empacotado no Mac não enxerga os certificados do sistema."""
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def buscar(sistema: str, maquina: str) -> Lancamento | None:
    pedido = urllib.request.Request(
        URL_ULTIMA,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"Rato-Alarme/{VERSAO}",
        },
    )
    try:
        with urllib.request.urlopen(pedido, timeout=ESPERA_S, context=_contexto_tls()) as resposta:
            dados = json.load(resposta)
    except (OSError, ValueError):
        return None
    return interpretar(dados, VERSAO, sistema, maquina)
