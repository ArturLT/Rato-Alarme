"""Preferências que a pessoa muda no painel. A bandeja e o rato também leem daqui."""

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, time
from pathlib import Path

from alarma.caminhos import pasta_config
from alarma.logica import LIMIAR_MANHA, LIMIAR_TARDE
from alarma.repertorio import CATEGORIAS, P_MUDO, PERMISSOES

PERMISSOES_PADRAO = tuple(p for p in PERMISSOES if p != P_MUDO)
FALAS_PADRAO = tuple(CATEGORIAS)
SEMPRE = "sempre"


@dataclass(frozen=True)
class Config:
    entrada: time = LIMIAR_MANHA
    saida: time = LIMIAR_TARDE
    alarme_ligado: bool = True
    fechar_janela: bool = True
    iniciar_com_sistema: bool = True
    # o pet
    pet_ligado: bool = True
    intensidade: int = 50
    travessura: int = 40
    liberdade: int = 30
    saudacao_boot: bool = True
    internet: bool = True
    falar_alto: bool = False
    cidade: str = ""
    dormir_ate: str = ""
    dormir_visivel: bool = True
    permissoes: tuple[str, ...] = field(default=PERMISSOES_PADRAO)
    falas: tuple[str, ...] = field(default=FALAS_PADRAO)

    def permite(self, permissao: str | None) -> bool:
        return permissao is None or permissao in self.permissoes

    def fala(self, categoria: str) -> bool:
        return categoria in self.falas

    def dormindo(self, agora: datetime) -> bool:
        """dormir_ate é "sempre" (até acordar pelo painel) ou uma data e hora ISO."""
        if not self.dormir_ate:
            return False
        if self.dormir_ate == SEMPRE:
            return True
        try:
            limite = datetime.fromisoformat(self.dormir_ate)
        except ValueError:
            return False
        if limite.tzinfo is None and agora.tzinfo is not None:
            agora = agora.replace(tzinfo=None)
        return agora < limite

    def com(self, **mudancas) -> "Config":
        return replace(self, **mudancas)


def caminho_padrao() -> Path:
    return pasta_config() / "config.json"


def _hora(texto: object, padrao: time) -> time:
    try:
        hora = time.fromisoformat(texto)
    except (TypeError, ValueError):
        return padrao
    return time(hora.hour, hora.minute)


def _sim_ou_nao(valor: object, padrao: bool) -> bool:
    return valor if isinstance(valor, bool) else padrao


def _nivel(valor: object, padrao: int) -> int:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return padrao
    return max(0, min(100, int(valor)))


def _texto(valor: object, padrao: str, limite: int = 80) -> str:
    return valor.strip()[:limite] if isinstance(valor, str) else padrao


def _lista(valor: object, validos, padrao: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(valor, list):
        return padrao
    return tuple(v for v in validos if v in valor)


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
        _sim_ou_nao(dados.get("iniciar_com_sistema"), padrao.iniciar_com_sistema),
        pet_ligado=_sim_ou_nao(dados.get("pet_ligado"), padrao.pet_ligado),
        intensidade=_nivel(dados.get("intensidade"), padrao.intensidade),
        travessura=_nivel(dados.get("travessura"), padrao.travessura),
        liberdade=_nivel(dados.get("liberdade"), padrao.liberdade),
        saudacao_boot=_sim_ou_nao(dados.get("saudacao_boot"), padrao.saudacao_boot),
        internet=_sim_ou_nao(dados.get("internet"), padrao.internet),
        falar_alto=_sim_ou_nao(dados.get("falar_alto"), padrao.falar_alto),
        cidade=_texto(dados.get("cidade"), padrao.cidade),
        dormir_ate=_texto(dados.get("dormir_ate"), padrao.dormir_ate, 40),
        dormir_visivel=_sim_ou_nao(dados.get("dormir_visivel"), padrao.dormir_visivel),
        permissoes=_lista(dados.get("permissoes"), PERMISSOES, padrao.permissoes),
        falas=_lista(dados.get("falas"), CATEGORIAS, padrao.falas),
    )


def salvar(caminho: Path, config: Config) -> None:
    if config.entrada >= config.saida:
        raise ValueError("a entrada precisa ser antes da saída")
    dados = {
        "entrada": config.entrada.strftime("%H:%M"),
        "saida": config.saida.strftime("%H:%M"),
        "alarme_ligado": config.alarme_ligado,
        "fechar_janela": config.fechar_janela,
        "iniciar_com_sistema": config.iniciar_com_sistema,
        "pet_ligado": config.pet_ligado,
        "intensidade": config.intensidade,
        "travessura": config.travessura,
        "liberdade": config.liberdade,
        "saudacao_boot": config.saudacao_boot,
        "internet": config.internet,
        "falar_alto": config.falar_alto,
        "cidade": config.cidade,
        "dormir_ate": config.dormir_ate,
        "dormir_visivel": config.dormir_visivel,
        "permissoes": list(config.permissoes),
        "falas": list(config.falas),
    }
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    temporario.replace(caminho)
