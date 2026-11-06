"""Lembra o que já aconteceu em cada alarme, mesmo se a criatura reiniciar."""

import json
from pathlib import Path

from alarma.caminhos import pasta_estado

PEGO = "pego"
DISPARADO = "disparado"
MARCA_MUDO = "mudo-do-rato"


def caminho_padrao() -> Path:
    return pasta_estado() / "registro.json"


def caminho_mudo() -> Path:
    return caminho_padrao().with_name(MARCA_MUDO)


class Registro:
    """Com caminho None, guarda só na memória (usado no modo demo)."""

    def __init__(self, caminho: Path | None) -> None:
        self._caminho = caminho
        self._dados: dict[str, list[str]] = {}
        if caminho is not None and caminho.exists():
            try:
                self._dados = json.loads(caminho.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._dados = {}

    def tem(self, dia: str, alarme: str, evento: str) -> bool:
        return evento in self._dados.get(f"{dia}/{alarme}", [])

    def marcar(self, dia: str, alarme: str, evento: str) -> None:
        chave = f"{dia}/{alarme}"
        self._dados = {
            k: v for k, v in self._dados.items() if k.startswith(f"{dia}/")
        }
        self._dados.setdefault(chave, []).append(evento)
        self._gravar()

    def limpar(self, dia: str, alarme: str) -> None:
        if self._dados.pop(f"{dia}/{alarme}", None) is not None:
            self._gravar()

    def _gravar(self) -> None:
        if self._caminho is None:
            return
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self._caminho.with_suffix(".tmp")
        temporario.write_text(json.dumps(self._dados), encoding="utf-8")
        temporario.replace(self._caminho)
