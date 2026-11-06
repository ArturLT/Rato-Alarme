"""Procura versão nova nos Releases do GitHub. Sem internet, fica tudo como está."""

import hashlib
import http.client
import json
import shutil
import ssl
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from alarma.caminhos import pasta_estado
from alarma.versao import VERSAO

REPOSITORIO = "ArturLT/Rato-Alarme"
URL_ULTIMA = f"https://api.github.com/repos/{REPOSITORIO}/releases/latest"
ESPERA_S = 10
BLOCO = 256 * 1024
ERROS_DE_DOWNLOAD = (OSError, ValueError, http.client.HTTPException)


@dataclass(frozen=True)
class Lancamento:
    versao: str
    pagina: str
    download: str | None
    resumo: str | None = None


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
    ativo = next(
        (
            ativo
            for ativo in (ativos if isinstance(ativos, list) else [])
            if isinstance(ativo, dict) and ativo.get("name") == instalador
        ),
        {},
    )
    return Lancamento(
        tag.removeprefix("v"), pagina, ativo.get("browser_download_url"), ativo.get("digest")
    )


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


def pasta_do_instalador() -> Path:
    return pasta_estado() / "instalador"


def limpar() -> None:
    """Apaga o instalador da atualização anterior."""
    shutil.rmtree(pasta_do_instalador(), ignore_errors=True)


def baixar(lancamento: Lancamento, destino: Path, progresso: Callable[[int], None]) -> None:
    """Só deixa o arquivo em `destino` se o resumo bater com o publicado no GitHub."""
    if not lancamento.download or not lancamento.resumo:
        raise ValueError("lançamento sem instalador conferível")
    pedido = urllib.request.Request(
        lancamento.download, headers={"User-Agent": f"Rato-Alarme/{VERSAO}"}
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    resumo = hashlib.sha256()
    try:
        with (
            urllib.request.urlopen(pedido, timeout=ESPERA_S, context=_contexto_tls()) as resposta,
            parcial.open("wb") as arquivo,
        ):
            total = int(resposta.headers.get("Content-Length") or 0)
            feito = 0
            while bloco := resposta.read(BLOCO):
                arquivo.write(bloco)
                resumo.update(bloco)
                feito += len(bloco)
                if total:
                    progresso(min(100, feito * 100 // total))
        if f"sha256:{resumo.hexdigest()}" != lancamento.resumo:
            raise ValueError("instalador diferente do publicado")
        parcial.replace(destino)
    finally:
        parcial.unlink(missing_ok=True)
