"""Lembretes: avisos que o rato dá em horários marcados. Sem Qt.

Cada lembrete tem hora, dias da semana e um tipo de aviso. No horário, o rato
aparece (mesmo dormindo, se o lembrete pedir), segura a placa com o aviso e o
computador mostra uma notificação. Um lembrete dispara uma vez por dia, até
TOLERANCIA_MIN depois da hora: se o computador ligar mais tarde, ele não toca.
"""

import json
import random
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time
from pathlib import Path

from alarma.caminhos import pasta_estado

TOLERANCIA_MIN = 15
DIAS = ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom")
TODOS_OS_DIAS = (0, 1, 2, 3, 4, 5, 6)
DIAS_UTEIS = (0, 1, 2, 3, 4)

# tipo: (nome no painel, título da placa, falas possíveis)
TIPOS = {
    "mensagem": ("Mensagem minha", "Lembrete", ["{texto}"]),
    "agua": ("Beber água", "Hora da água", ["Bebe água, {nome}! Eu espero.", "Um copo d'água agora. É ordem do rato.", "Hidratação! Glub glub."]),
    "pausa": ("Fazer uma pausa", "Pausa", ["Levanta um pouco, {nome}. Cinco minutinhos.", "Pausa! Seus olhos agradecem.", "Hora de descansar a cabeça."]),
    "alongar": ("Alongar", "Alongamento", ["Estica os braços! Gira o pescoço!", "Alonga as costas que eu alongo o rabo.", "Bora alongar, {nome}!"]),
    "almoco": ("Almoço", "Almoço", ["Hora do almoço! Traz um queijinho pra mim?", "Bora comer, {nome}!", "Almoço! Comida primeiro, trabalho depois."]),
    "remedio": ("Tomar remédio", "Remédio", ["Hora do remédio, {nome}.", "Não esquece o remédio!", "Remédio agora. Eu fico de olho."]),
    "reuniao": ("Reunião", "Reunião", ["Sua reunião vai começar!", "Reunião! Arruma o cabelo.", "Hora da reunião. Boa sorte!"]),
    "dormir": ("Ir dormir", "Hora de dormir", ["Tá tarde, {nome}. Bora dormir?", "Desliga isso e vai descansar!", "Até amanhã? Dormir faz bem."]),
    "clima": ("Previsão do tempo", "Previsão do rato", ["{clima}"]),
    "noticias": ("Notícias do dia", "Notícia fresquinha", ["{noticia}"]),
    "ponto": ("Bater o ponto", "Ponto", ["Bateu o ponto, {nome}?", "Não esquece o ponto!", "Ponto! Ponto! Ponto!"]),
}


@dataclass(frozen=True)
class Lembrete:
    id: str
    hora: time
    tipo: str = "mensagem"
    texto: str = ""
    dias: tuple[int, ...] = field(default=TODOS_OS_DIAS)
    ativo: bool = True
    som: bool = True
    acordar: bool = True

    def com(self, **mudancas) -> "Lembrete":
        return replace(self, **mudancas)

    @property
    def nome_tipo(self) -> str:
        return TIPOS.get(self.tipo, TIPOS["mensagem"])[0]

    def resumo(self) -> str:
        dias = "todo dia" if self.dias == TODOS_OS_DIAS else "dias úteis" if self.dias == DIAS_UTEIS else ", ".join(DIAS[d] for d in self.dias) or "nunca"
        texto = self.texto if self.tipo == "mensagem" and self.texto else self.nome_tipo
        return f"{self.hora:%H:%M} · {dias} · {texto}"

    def para_dict(self) -> dict:
        return {
            "id": self.id, "hora": self.hora.strftime("%H:%M"), "tipo": self.tipo, "texto": self.texto,
            "dias": list(self.dias), "ativo": self.ativo, "som": self.som, "acordar": self.acordar,
        }


def novo_id(acaso: random.Random | None = None) -> str:
    return f"{(acaso or random.Random()).getrandbits(40):010x}"


def de_dict(dados: object) -> Lembrete | None:
    if not isinstance(dados, dict):
        return None
    try:
        hora = time.fromisoformat(str(dados.get("hora")))
    except ValueError:
        return None
    ident = dados.get("id")
    if not isinstance(ident, str) or not ident:
        return None
    tipo = dados.get("tipo") if dados.get("tipo") in TIPOS else "mensagem"
    texto = dados.get("texto") if isinstance(dados.get("texto"), str) else ""
    dias = dados.get("dias")
    dias = tuple(sorted({d for d in dias if isinstance(d, int) and 0 <= d <= 6})) if isinstance(dias, list) else TODOS_OS_DIAS
    sim = lambda chave, padrao: dados.get(chave) if isinstance(dados.get(chave), bool) else padrao  # noqa: E731
    return Lembrete(ident, time(hora.hour, hora.minute), tipo, texto[:200], dias, sim("ativo", True), sim("som", True), sim("acordar", True))


def ler_lista(dados: object) -> tuple[Lembrete, ...]:
    if not isinstance(dados, list):
        return ()
    return tuple(l for l in (de_dict(d) for d in dados) if l is not None)


def devidos(lembretes, agora: datetime, ja_disparados: set[str]) -> list[Lembrete]:
    """Os lembretes que tocam agora: ativos, no dia certo, na janela de tolerância e ainda não tocados hoje."""
    hoje = agora.date().isoformat()
    minuto = agora.hour * 60 + agora.minute
    saida = []
    for l in lembretes:
        if not l.ativo or agora.weekday() not in l.dias or f"{hoje}/{l.id}" in ja_disparados:
            continue
        alvo = l.hora.hour * 60 + l.hora.minute
        if 0 <= minuto - alvo < TOLERANCIA_MIN:
            saida.append(l)
    return sorted(saida, key=lambda l: l.hora)


def texto_do_aviso(l: Lembrete, fatos: dict, extras: dict, acaso: random.Random) -> tuple[str, str]:
    """(título da placa, texto). extras: {"clima": ..., "noticia": ...} já buscados, se houver."""
    _, titulo, falas = TIPOS.get(l.tipo, TIPOS["mensagem"])
    valores = {"nome": fatos.get("nome", "humano"), "texto": l.texto or "Lembrete!", **{k: v for k, v in extras.items() if v}}
    valores.setdefault("clima", "Não consegui ver o tempo agora. Olha pela janela!")
    valores.setdefault("noticia", "Sem notícias fresquinhas agora. Nenhuma notícia, boa notícia!")
    texto = acaso.choice(falas).format(**valores)
    if l.texto and l.tipo != "mensagem":
        texto = f"{texto} {l.texto}"
    return titulo, texto


# ---- o que já tocou hoje (para não tocar de novo se o programa reiniciar) ----


def caminho_estado() -> Path:
    return pasta_estado() / "lembretes-tocados.json"


def ler_tocados(caminho: Path | None = None, hoje: date | None = None) -> set[str]:
    caminho = caminho or caminho_estado()
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    prefixo = (hoje or date.today()).isoformat() + "/"
    return {d for d in dados if isinstance(d, str) and d.startswith(prefixo)} if isinstance(dados, list) else set()


def gravar_tocados(tocados: set[str], caminho: Path | None = None) -> None:
    caminho = caminho or caminho_estado()
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(json.dumps(sorted(tocados)), encoding="utf-8")
    except OSError:
        pass
