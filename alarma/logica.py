"""Decide qual alarme do ponto vale agora, pelo relógio. Com os horários padrão:

- 12:49 ou depois → tarde
- 06:50 até 12:48 → manhã
- antes das 06:50 → nenhum

O rato da manhã vale até a saída, porque a pessoa pode chegar atrasada. O da tarde
vale até TOLERANCIA_MIN depois da saída, para quem religa o computador nesse
intervalo. Depois disso, ativar o programa não solta o rato, mas uma caçada já
iniciada continua até ele ser pego.
"""

from dataclasses import dataclass
from datetime import datetime, time

LIMIAR_MANHA = time(6, 50)
# Antes das 13:00 de propósito: desligar o computador antes do ponto faria o alarme falhar.
LIMIAR_TARDE = time(12, 49)
TOLERANCIA_MIN = 60


class Alarme:
    NENHUM = "nenhum"
    MANHA = "manha"
    TARDE = "tarde"


@dataclass(frozen=True)
class Decisao:
    alarme: str
    no_horario: bool
    agora: datetime

    @property
    def ativo(self) -> bool:
        return self.alarme != Alarme.NENHUM


def _minutos(hora: time) -> int:
    return hora.hour * 60 + hora.minute


def decidir(
    agora: datetime,
    entrada: time = LIMIAR_MANHA,
    saida: time = LIMIAR_TARDE,
) -> Decisao:
    hora = agora.time()
    if hora >= saida:
        return Decisao(Alarme.TARDE, _minutos(hora) - _minutos(saida) < TOLERANCIA_MIN, agora)
    if hora >= entrada:
        return Decisao(Alarme.MANHA, True, agora)
    return Decisao(Alarme.NENHUM, False, agora)


def pendente(decisao: Decisao, alarme_ligado: bool, pego: bool, disparado: bool) -> bool:
    """Solta o rato no horário, e mantém solto o que já tinha disparado."""
    if not alarme_ligado or not decisao.ativo or pego:
        return False
    return decisao.no_horario or disparado


def resumir(decisao: Decisao, alarme_ligado: bool, pego: bool, solto: bool) -> str:
    if not alarme_ligado:
        return "Alarme desligado"
    nome = "da manhã" if decisao.alarme == Alarme.MANHA else "da tarde"
    if solto:
        return f"Alarme {nome}: rato solto"
    if pego:
        return f"Alarme {nome}: rato pego"
    return "Rato esperando o horário"
