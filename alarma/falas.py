"""O que o rato reclama nos balões. Sem Qt: o acaso e o horário vêm de fora."""

import random
from datetime import datetime, time

from alarma.logica import Alarme

COMPUTADOR = (
    "esse computador esquenta mais que a minha gaiola.",
    "tanta aba aberta! nem queijo suíço tem tanto buraco.",
    "essa ventoinha faz mais barulho que eu.",
    "achei mais farelo no teclado do que na minha toca. obrigado.",
    "demorou tanto para ligar que eu quase dormi de novo.",
    "chamam esse aparelho de mouse. não come nem queijo.",
    "tanta memória nessa máquina e você esquece do ponto.",
    "sua área de trabalho é mais bagunçada que o meu ninho.",
    "limpa essa tela. estou vendo as suas digitais daqui.",
)
ENTRADA = (
    "bom dia para quem? o ponto de entrada continua aberto.",
    "o ponto não vai se bater sozinho.",
    "o café pode esperar. o ponto, não.",
)
SAIDA = (
    "acabou o expediente e o ponto continua sem bater.",
    "quer fazer hora extra de graça? bate o ponto.",
    "pode ir para casa. depois de bater o ponto.",
)
ATRASO_ENTRADA = (
    "{atraso} de atraso na entrada. eu cronometrei.",
    "já faz {atraso} que era para você ter batido o ponto.",
    "{atraso} de atraso! até o meu relógio de queijo é melhor.",
)
ATRASO_SAIDA = (
    "faz {atraso} que deu a hora de sair. e o ponto?",
    "{atraso} depois do horário e nada de ponto.",
)


def minutos_de_atraso(agora: datetime, horario: time) -> int:
    return max(0, (agora.hour - horario.hour) * 60 + agora.minute - horario.minute)


def por_extenso(minutos: int) -> str:
    horas, resto = divmod(minutos, 60)
    partes = []
    if horas:
        partes.append(f"{horas} hora" + ("s" if horas > 1 else ""))
    if resto or not horas:
        partes.append(f"{resto} minuto" + ("s" if resto != 1 else ""))
    return " e ".join(partes)


def pontualidade(alarme: str, atraso: int) -> tuple[str, ...]:
    """As frases sobre o ponto. As que citam o atraso só valem se ele existir."""
    manha = alarme == Alarme.MANHA
    frases = ENTRADA if manha else SAIDA
    if atraso < 1:
        return frases
    extenso = por_extenso(atraso)
    com_atraso = ATRASO_ENTRADA if manha else ATRASO_SAIDA
    return frases + tuple(f.format(atraso=extenso) for f in com_atraso)


def sortear(acaso: random.Random, alarme: str, atraso: int, ultima: str = "") -> str:
    """Metade das vezes reclama do computador, metade do ponto. Nunca repete a última."""
    tema = acaso.choice((COMPUTADOR, pontualidade(alarme, atraso)))
    return acaso.choice([f for f in tema if f != ultima])
