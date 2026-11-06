"""Decide qual alarme do ponto está ativo.

O computador precisa estar ligado. A hora local em que ele ligou, no dia
de hoje, escolhe o alarme:

- 13:00 ou depois → tarde
- 06:50 até 12:59 → manhã
- antes das 06:50, ou ligado em outro dia → nenhum

Quando a hora do boot passa dos dois limiares, vale o da tarde.
"""

from dataclasses import dataclass
from datetime import datetime, time, tzinfo

LIMIAR_MANHA = time(6, 50)
LIMIAR_TARDE = time(13, 0)


class Alarme:
    NENHUM = "nenhum"
    MANHA = "manha"
    TARDE = "tarde"


@dataclass(frozen=True)
class Decisao:
    alarme: str
    ligado: bool
    boot: datetime
    agora: datetime

    @property
    def ativo(self) -> bool:
        return self.alarme != Alarme.NENHUM


def _no_fuso(momento: datetime, fuso: tzinfo) -> datetime:
    if momento.tzinfo is None:
        return momento.replace(tzinfo=fuso)
    return momento.astimezone(fuso)


def decidir(
    ligado: bool,
    boot: datetime,
    agora: datetime,
    fuso: tzinfo | None = None,
) -> Decisao:
    zona = fuso if fuso is not None else datetime.now().astimezone().tzinfo
    if zona is None:
        raise RuntimeError("fuso local indisponível")

    boot_local = _no_fuso(boot, zona)
    agora_local = _no_fuso(agora, zona)

    if not ligado or boot_local.date() != agora_local.date():
        alarme = Alarme.NENHUM
    else:
        hora = boot_local.time()
        if hora >= LIMIAR_TARDE:
            alarme = Alarme.TARDE
        elif hora >= LIMIAR_MANHA:
            alarme = Alarme.MANHA
        else:
            alarme = Alarme.NENHUM

    return Decisao(alarme, ligado, boot_local, agora_local)


def descrever(decisao: Decisao) -> str:
    boot = decisao.boot.strftime("%Y-%m-%d %H:%M:%S")
    if decisao.alarme == Alarme.MANHA:
        estado = "alarme da manhã (06:50)"
    elif decisao.alarme == Alarme.TARDE:
        estado = "alarme da tarde (13:00)"
    else:
        estado = "nenhum alarme"
    ligado = "ligado" if decisao.ligado else "desligado"
    return f"computador {ligado}, boot {boot} → {estado}"
