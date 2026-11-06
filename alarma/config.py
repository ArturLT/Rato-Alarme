"""Preferências que a pessoa muda no painel. Sem GTK: a bandeja também lê daqui."""

import json
import os
from dataclasses import dataclass
from datetime import time
from pathlib import Path

from alarma.logica import LIMIAR_MANHA, LIMIAR_TARDE


@dataclass(frozen=True)
class Config:
    entrada: time = LIMIAR_MANHA
    saida: time = LIMIAR_TARDE
    alarme_ligado: bool = True
    fechar_janela: bool = True


def caminho_padrao() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "alarma-meme" / "config.json"


def _hora(texto: object, padrao: time) -> time:
    try:
        hora = time.fromisoformat(texto)
    except (TypeError, ValueError):
        return padrao
    return time(hora.hour, hora.minute)


def _sim_ou_nao(valor: object, padrao: bool) -> bool:
    return valor if isinstance(valor, bool) else padrao


def carregar(caminho: Path) -> Config:
    """Arquivo ausente ou estragado não pode impedir o alarme: vale o padrão."""
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Config()
    if not isinstance(dados, dict):
        return Config()

    padrao = Config()
    entrada = _hora(dados.get("entrada"), padrao.entrada)
    saida = _hora(dados.get("saida"), padrao.saida)
    if entrada >= saida:
        entrada, saida = padrao.entrada, padrao.saida
    return Config(
        entrada,
        saida,
        _sim_ou_nao(dados.get("alarme_ligado"), padrao.alarme_ligado),
        _sim_ou_nao(dados.get("fechar_janela"), padrao.fechar_janela),
    )


def salvar(caminho: Path, config: Config) -> None:
    if config.entrada >= config.saida:
        raise ValueError("a entrada precisa ser antes da saída")
    dados = {
        "entrada": config.entrada.strftime("%H:%M"),
        "saida": config.saida.strftime("%H:%M"),
        "alarme_ligado": config.alarme_ligado,
        "fechar_janela": config.fechar_janela,
    }
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(dados, indent=2), encoding="utf-8")
    temporario.replace(caminho)
