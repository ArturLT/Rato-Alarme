"""Quando o pet aparece, quanto tempo fica e o que escolhe fazer. Sem Qt.

A intensidade (0 a 100) decide de quanto em quanto tempo ele aparece e quanto
fica; o nível de travessura decide quantas das escolhas são travessuras. Quem
escolhe entre as opções permitidas é o cérebro, pelo que aprendeu.
"""

import random
from dataclasses import dataclass
from datetime import datetime

from alarma import repertorio as rep
from alarma.cerebro import DESISTIU_TXT, Cerebro, Escolha
from alarma.config import Config

TAPAS_PARA_EXPULSAR = 3
JANELA_TAPAS_S = 8.0
CARINHO_PX = 650.0
CARINHO_S = 3.0


def espera_ate_aparecer(intensidade: int, acaso: random.Random) -> float:
    """Segundos até a próxima visita. 100 → 1 a 3 min; 50 → uns 15 min; 0 → mais de 1 hora."""
    i = max(0, min(100, intensidade)) / 100
    base = 60 + 3900 * (1 - i) ** 2
    return base * acaso.uniform(0.6, 1.4)


def duracao_visita(intensidade: int, acaso: random.Random) -> float:
    i = max(0, min(100, intensidade)) / 100
    return (40 + 200 * i) * acaso.uniform(0.7, 1.3)


def pausa_entre_interacoes(intensidade: int, acaso: random.Random) -> float:
    i = max(0, min(100, intensidade)) / 100
    return (14 - 9 * i) * acaso.uniform(0.7, 1.4)


def espera_depois_de_expulso(intensidade: int, acaso: random.Random) -> float:
    """Expulso, ele demora bem mais para voltar, e nunca menos de 20 minutos."""
    return max(20 * 60, espera_ate_aparecer(intensidade, acaso) * 3)


def chance_travessura(travessura: int) -> float:
    return 0.04 + 0.56 * max(0, min(100, travessura)) / 100


def periodo(hora: int) -> str:
    if 5 <= hora < 12:
        return "manha"
    if 12 <= hora < 18:
        return "tarde"
    if 18 <= hora < 24:
        return "noite"
    return "madrugada"


@dataclass(frozen=True)
class Plano:
    interacao: rep.Interacao | None
    teimosa: bool = False
    desistiu: rep.Interacao | None = None


def elegiveis(
    interacoes: list[rep.Interacao],
    cfg: Config,
    cerebro: Cerebro,
    tem_fonte,
    possivel,
) -> list[rep.Interacao]:
    """O que ele pode fazer agora: permitido no painel, com o que precisa disponível.
    tem_fonte(fonte) diz se já há informação; possivel(permissao) se o sistema deixa."""
    saida = []
    for i in interacoes:
        if i.tipo == rep.TRAVESSURA:
            if not cfg.permite(i.permissao) or not possivel(i.permissao):
                continue
        elif i.tipo == rep.BRINCADEIRA:
            pass
        elif not cfg.fala(i.categoria):
            continue
        if i.internet and not cfg.internet:
            continue
        if i.tipo == rep.INFO and not tem_fonte(i.fonte):
            continue
        if i.tipo == rep.PERGUNTA and i.fato in cerebro.fatos:
            continue
        if i.tipo == rep.FALA and any(rep.preencher(t, cerebro.fatos) is None for t in i.textos):
            continue
        saida.append(i)
    return saida


def extras(cerebro: Cerebro, cfg: Config) -> list[rep.Interacao]:
    """Interações que nascem do aprendizado: frases ensinadas e segredos desbloqueados."""
    lista = []
    if cfg.fala(rep.ENSINADAS):
        for frase in cerebro.frases:
            lista.append(rep.Interacao(f"ensinada:{frase}", rep.FALA, rep.ENSINADAS, (frase,), peso=1.3))
    if cfg.fala(rep.CARINHO):
        for ident in cerebro.desbloqueadas:
            if ident.startswith("segredo-"):
                try:
                    texto = rep.segredo(int(ident.split("-")[1]))
                except ValueError:
                    continue
                lista.append(rep.Interacao(ident, rep.FALA, rep.CARINHO, (texto,), peso=1.2))
    return lista


# Personalidade: quanto cada tipo ou categoria pesa a mais. "travessura" mexe na chance de aprontar.
PERSONALIDADES = {
    "brincalhao": {rep.BRINCADEIRA: 2.0},
    "curioso": {rep.INFO: 1.8, rep.CURIOSIDADES: 1.8, rep.PERGUNTAS: 1.5},
    "carinhoso": {rep.CARINHO: 2.2, rep.LEMBRANCAS: 1.6},
    "travesso": {"travessura": 1.5, rep.PROVOCACOES: 1.5},
    "preguicoso": {"cochilar": 3.0, "espreguicar": 3.0, "sentar-olhar": 2.0, "correr": 0.4},
}


def _peso(i: rep.Interacao, bonus: dict) -> float:
    return i.peso * bonus.get(i.id, 1.0) * bonus.get(i.categoria, 1.0) * (bonus.get(i.tipo, 1.0) if i.tipo != i.categoria else 1.0)


def planejar(
    opcoes: list[rep.Interacao],
    cfg: Config,
    cerebro: Cerebro,
    acaso: random.Random,
    personalidade: str = "",
) -> Plano:
    """Escolhe a próxima interação. Primeiro sorteia se vai ser travessura, depois o cérebro escolhe."""
    bonus = PERSONALIDADES.get(personalidade, {})
    travessuras = [i for i in opcoes if i.tipo == rep.TRAVESSURA]
    resto = [i for i in opcoes if i.tipo != rep.TRAVESSURA]
    liberdade = cfg.liberdade / 100
    desistiu = None
    if travessuras and acaso.random() < min(0.9, chance_travessura(cfg.travessura) * bonus.get("travessura", 1.0)):
        escolha = cerebro.escolher([(i.id, _peso(i, bonus)) for i in travessuras], liberdade, acaso)
        if escolha.acao is not None:
            return Plano(_achar(travessuras, escolha), escolha.teimosa)
        # todas as travessuras foram desaprendidas: ele conta que desistiu
        desistiu = acaso.choice([i for i in travessuras if cerebro.opiniao(i.id) == DESISTIU_TXT] or travessuras)
    if not resto:
        return Plano(None, desistiu=desistiu)
    escolha = cerebro.escolher([(i.id, _peso(i, bonus)) for i in resto], liberdade, acaso)
    return Plano(_achar(resto, escolha), escolha.teimosa, desistiu)


def _achar(lista: list[rep.Interacao], escolha: Escolha) -> rep.Interacao | None:
    return next((i for i in lista if i.id == escolha.acao), None)


class Tapas:
    """Conta os tapas recentes. TAPAS_PARA_EXPULSAR em JANELA_TAPAS_S expulsa o rato."""

    def __init__(self) -> None:
        self._momentos: list[float] = []

    def bater(self, agora: float) -> bool:
        self._momentos = [t for t in self._momentos if agora - t <= JANELA_TAPAS_S] + [agora]
        if len(self._momentos) >= TAPAS_PARA_EXPULSAR:
            self._momentos = []
            return True
        return False

    @property
    def seguidos(self) -> int:
        return len(self._momentos)


class Carinho:
    """Carinho é passar o cursor por cima do rato, indo e voltando, sem clicar."""

    def __init__(self) -> None:
        self._ultimo: tuple[int, int] | None = None
        self._trilha: list[tuple[float, float]] = []

    def notar(self, agora: float, cursor: tuple[int, int] | None, em_cima: bool) -> bool:
        if cursor is None or not em_cima:
            self._ultimo = None
            self._trilha = [(t, d) for t, d in self._trilha if agora - t <= CARINHO_S]
            return False
        if self._ultimo is not None:
            dx, dy = cursor[0] - self._ultimo[0], cursor[1] - self._ultimo[1]
            distancia = (dx * dx + dy * dy) ** 0.5
            if distancia > 0:
                self._trilha.append((agora, distancia))
        self._ultimo = cursor
        self._trilha = [(t, d) for t, d in self._trilha if agora - t <= CARINHO_S]
        if sum(d for _, d in self._trilha) >= CARINHO_PX:
            self._trilha = []
            return True
        return False


def texto_saudacao(agora: datetime, cerebro: Cerebro, acaso: random.Random) -> str:
    opcoes = rep.SAUDACOES[periodo(agora.hour)]
    texto = rep.preencher(acaso.choice(opcoes), cerebro.fatos) or opcoes[0].replace("{nome}", "humano")
    favorita = cerebro.hora_favorita()
    if favorita is not None and abs(agora.hour - favorita) >= 3 and acaso.random() < 0.5:
        texto += f" Você costuma chegar lá pelas {favorita}h, hein."
    return texto
