"""O que o rato aprende com a pessoa. Sem Qt: o tempo e o acaso vêm de fora.

Cada coisa que o rato faz tem uma chave (por exemplo "fechar_aba" ou "fala:piada").
Carinho e queijo aumentam o valor do que ele fez há pouco; tapa diminui. O que
aconteceu mais perto do carinho ou do tapa leva mais crédito, como num bicho de
verdade.

Ele escolhe o que fazer sorteando com pesos: quanto mais valor, mais chance. Uma
ação com valor muito baixo ele deixa de fazer, mas a liberdade de escolha (no
painel) deixa uma chance pequena de ele teimar.
"""

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from alarma.caminhos import pasta_estado

TAXA = 0.7
JANELA_S = 30.0
MEIA_VIDA_S = 10.0
LIMITE = 4.0
EVITA = -1.2
DESISTIU = -2.6
XP_CARINHO = 3
XP_QUEIJO = 6
XP_POR_NIVEL = 25
HUMOR_NEUTRO = 60.0
HUMOR_VOLTA_S = 1800.0
MAX_FRASES = 60
MAX_RECENTES = 30

GOSTA = "gosta"
NEUTRO = "neutro"
EVITA_TXT = "evita"
DESISTIU_TXT = "desistiu"


def caminho_padrao() -> Path:
    return pasta_estado() / "cerebro.json"


@dataclass(frozen=True)
class Escolha:
    acao: str | None
    teimosa: bool = False


def _limitar(valor: float) -> float:
    return max(-LIMITE, min(LIMITE, valor))


class Cerebro:
    """Com caminho None, guarda só na memória (modo demo e testes)."""

    def __init__(self, caminho: Path | None = None) -> None:
        self._caminho = caminho
        self.pesos: dict[str, float] = {}
        self.vezes: dict[str, int] = {}
        self.xp = 0
        self._humor = HUMOR_NEUTRO
        self._humor_em: float | None = None
        self.frases: list[str] = []
        self.desbloqueadas: list[str] = []
        self.fatos: dict[str, str] = {}
        self.horas = [0] * 24
        self.ligacoes = 0
        self.recentes: list[tuple[str, float]] = []
        self._carregar()

    # ---- memória em disco ----

    def _carregar(self) -> None:
        if self._caminho is None or not self._caminho.exists():
            return
        try:
            dados = json.loads(self._caminho.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(dados, dict):
            return

        def numero(valor: object, padrao: float) -> float:
            return float(valor) if isinstance(valor, (int, float)) and not isinstance(valor, bool) else padrao

        pesos = dados.get("pesos")
        if isinstance(pesos, dict):
            self.pesos = {str(k): _limitar(numero(v, 0.0)) for k, v in pesos.items()}
        vezes = dados.get("vezes")
        if isinstance(vezes, dict):
            self.vezes = {str(k): int(numero(v, 0)) for k, v in vezes.items()}
        self.xp = max(0, int(numero(dados.get("xp"), 0)))
        self._humor = max(0.0, min(100.0, numero(dados.get("humor"), HUMOR_NEUTRO)))
        em = dados.get("humor_em")
        self._humor_em = float(em) if isinstance(em, (int, float)) and not isinstance(em, bool) else None
        frases = dados.get("frases")
        if isinstance(frases, list):
            self.frases = [f for f in frases if isinstance(f, str) and f.strip()][:MAX_FRASES]
        desbloqueadas = dados.get("desbloqueadas")
        if isinstance(desbloqueadas, list):
            self.desbloqueadas = [d for d in desbloqueadas if isinstance(d, str)]
        fatos = dados.get("fatos")
        if isinstance(fatos, dict):
            self.fatos = {str(k): str(v) for k, v in fatos.items() if isinstance(v, str) and v.strip()}
        horas = dados.get("horas")
        if isinstance(horas, list) and len(horas) == 24:
            self.horas = [int(numero(h, 0)) for h in horas]
        self.ligacoes = int(numero(dados.get("ligacoes"), 0))

    def salvar(self) -> None:
        if self._caminho is None:
            return
        dados = {
            "pesos": self.pesos,
            "vezes": self.vezes,
            "xp": self.xp,
            "humor": self._humor,
            "humor_em": self._humor_em,
            "frases": self.frases,
            "desbloqueadas": self.desbloqueadas,
            "fatos": self.fatos,
            "horas": self.horas,
            "ligacoes": self.ligacoes,
        }
        try:
            self._caminho.parent.mkdir(parents=True, exist_ok=True)
            temporario = self._caminho.with_suffix(".tmp")
            temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
            temporario.replace(self._caminho)
        except OSError:
            pass

    def esquecer_tudo(self) -> None:
        """Volta a ser um filhote. Frases ensinadas e fatos também somem."""
        caminho = self._caminho
        self.__init__(None)
        self._caminho = caminho
        self.salvar()

    # ---- o que ele fez ----

    def lembrar(self, acao: str, agora: float) -> None:
        self.recentes.append((acao, agora))
        self.recentes = [(a, t) for a, t in self.recentes if agora - t <= JANELA_S][-MAX_RECENTES:]
        self.vezes[acao] = self.vezes.get(acao, 0) + 1

    def _credito(self, agora: float, acao: str | None) -> dict[str, float]:
        """Quanto cada ação recente leva do carinho ou do tapa. A mais nova leva mais."""
        if acao is not None:
            return {acao: 1.0}
        credito: dict[str, float] = {}
        for nome, momento in self.recentes:
            idade = agora - momento
            if 0 <= idade <= JANELA_S:
                peso = 0.5 ** (idade / MEIA_VIDA_S)
                credito[nome] = max(credito.get(nome, 0.0), peso)
        return credito

    def _ajustar(self, agora: float, sinal: float, forca: float, acao: str | None) -> list[str]:
        credito = self._credito(agora, acao)
        for nome, peso in credito.items():
            self.pesos[nome] = _limitar(self.pesos.get(nome, 0.0) + sinal * TAXA * forca * peso)
        return sorted(credito, key=credito.__getitem__, reverse=True)

    def recompensar(self, agora: float, forca: float = 1.0, acao: str | None = None, queijo: bool = False) -> list[str]:
        """Carinho ou queijo. Retorna as ações que ganharam valor, da mais à menos afetada."""
        self.xp += XP_QUEIJO if queijo else XP_CARINHO
        self._mudar_humor(agora, 12 if queijo else 7)
        return self._ajustar(agora, +1, forca, acao)

    def punir(self, agora: float, forca: float = 1.0, acao: str | None = None) -> list[str]:
        """Tapa ou 'não gostei'. Retorna as ações que perderam valor."""
        self._mudar_humor(agora, -10 * forca)
        return self._ajustar(agora, -1, forca, acao)

    # ---- opinião e escolha ----

    def valor(self, acao: str) -> float:
        return self.pesos.get(acao, 0.0)

    def opiniao(self, acao: str) -> str:
        valor = self.valor(acao)
        if valor <= DESISTIU:
            return DESISTIU_TXT
        if valor <= EVITA:
            return EVITA_TXT
        if valor >= 1.0:
            return GOSTA
        return NEUTRO

    def escolher(
        self,
        opcoes: list[tuple[str, float]],
        liberdade: float,
        acaso: random.Random,
    ) -> Escolha:
        """Sorteia uma ação. liberdade 0..1: 0 obedece o que aprendeu, 1 faz quase o que quer."""
        if not opcoes:
            return Escolha(None)
        liberdade = max(0.0, min(1.0, liberdade))
        obediencia = 1.0 - liberdade * 0.75
        pesos = []
        for acao, base in opcoes:
            valor = self.valor(acao)
            if valor <= DESISTIU:
                # só teima se tiver liberdade; e mesmo assim, pouco
                pesos.append(base * 0.06 * liberdade)
            else:
                pesos.append(base * math.exp(valor * obediencia))
        total = sum(pesos)
        if total <= 0:
            return Escolha(None)
        sorteio = acaso.uniform(0, total)
        for (acao, _), peso in zip(opcoes, pesos):
            sorteio -= peso
            if sorteio <= 0:
                return Escolha(acao, self.valor(acao) <= EVITA)
        acao = opcoes[-1][0]
        return Escolha(acao, self.valor(acao) <= EVITA)

    # ---- humor, nível ----

    def humor(self, agora: float) -> float:
        """0 triste, 100 radiante. Sem nada acontecer, volta aos poucos para o meio."""
        if self._humor_em is None:
            return self._humor
        passado = max(0.0, agora - self._humor_em)
        fator = 0.5 ** (passado / HUMOR_VOLTA_S)
        return HUMOR_NEUTRO + (self._humor - HUMOR_NEUTRO) * fator

    def _mudar_humor(self, agora: float, delta: float) -> None:
        self._humor = max(0.0, min(100.0, self.humor(agora) + delta))
        self._humor_em = agora

    @property
    def nivel(self) -> int:
        return 1 + self.xp // XP_POR_NIVEL

    def progresso(self) -> float:
        """Quanto falta para o próximo nível, de 0 a 1."""
        return (self.xp % XP_POR_NIVEL) / XP_POR_NIVEL

    # ---- o que a pessoa ensina ----

    def ensinar(self, frase: str) -> bool:
        frase = " ".join(frase.split())[:140]
        if not frase or frase in self.frases:
            return False
        self.frases.append(frase)
        self.frases = self.frases[-MAX_FRASES:]
        return True

    def esquecer_frase(self, frase: str) -> None:
        self.frases = [f for f in self.frases if f != frase]
        self.pesos.pop(f"ensinada:{frase}", None)

    def aprender_fato(self, chave: str, valor: str) -> None:
        valor = " ".join(valor.split())[:60]
        if valor:
            self.fatos[chave] = valor

    def desbloquear(self, ident: str) -> None:
        if ident not in self.desbloqueadas:
            self.desbloqueadas.append(ident)

    def notar_atividade(self, hora: int) -> None:
        self.horas[hora % 24] += 1

    def hora_favorita(self) -> int | None:
        if sum(self.horas) < 10:
            return None
        return max(range(24), key=self.horas.__getitem__)
