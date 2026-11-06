"""Notícias, clima e curiosidades da internet, e o que dá para saber do computador.

As buscas rodam fora da thread do Qt e guardam o resultado num cache; o rato só lê
o cache. Sem internet, ou com a internet desligada no painel, as fontes da rede
ficam vazias e o rato fala de outra coisa. Nenhum dado pessoal é enviado: as
consultas levam no máximo o nome da cidade digitada no painel.
"""

import json
import os
import platform
import random
import shutil
import ssl
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

ESPERA_S = 10
VALIDADE_S = 40 * 60
AGENTE = "Rato-Alarme (pet de mesa)"

URL_LOCAL = "https://ipwho.is/"
URL_GEO = "https://geocoding-api.open-meteo.com/v1/search?count=1&language=pt&format=json&name="
URL_CLIMA = (
    "https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    "&current=temperature_2m,apparent_temperature,weather_code,relative_humidity_2m"
    "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
    "&timezone=auto&forecast_days=2"
)
_GOOGLE = "https://news.google.com/rss{caminho}?hl=pt-BR&gl=BR&ceid=BR:pt-419"
URL_NOTICIAS = {
    "noticia_brasil": _GOOGLE.format(caminho="/headlines/section/geo/Brasil"),
    "noticia_mundo": _GOOGLE.format(caminho="/headlines/section/topic/WORLD"),
    "noticia_tecnologia": _GOOGLE.format(caminho="/headlines/section/topic/TECHNOLOGY"),
    "noticia_ciencia": _GOOGLE.format(caminho="/headlines/section/topic/SCIENCE"),
    "noticia_esportes": _GOOGLE.format(caminho="/headlines/section/topic/SPORTS"),
    "noticia_economia": _GOOGLE.format(caminho="/headlines/section/topic/BUSINESS"),
    "noticia_saude": _GOOGLE.format(caminho="/headlines/section/topic/HEALTH"),
}
RESERVA_NOTICIAS = {
    "noticia_brasil": "https://g1.globo.com/rss/g1/",
    "noticia_mundo": "https://feeds.bbci.co.uk/portuguese/rss.xml",
}
URL_COTACAO = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL,BTC-BRL"
URL_HISTORIA = "https://pt.wikipedia.org/api/rest_v1/feed/onthisday/events/{mes:02d}/{dia:02d}"
URL_WIKI = "https://pt.wikipedia.org/api/rest_v1/page/random/summary"
URL_FERIADOS = "https://brasilapi.com.br/api/feriados/v1/{ano}"

FONTES_REDE = (
    "clima_agora", "clima_hoje", "clima_amanha", "clima_chuva", *URL_NOTICIAS,
    "cotacao_dolar", "cotacao_euro", "cotacao_bitcoin", "hoje_na_historia", "proximo_feriado", "wikipedia",
)

# Códigos de tempo da OMM que o Open-Meteo usa.
TEMPO = {
    0: "céu limpo", 1: "quase sem nuvens", 2: "parcialmente nublado", 3: "nublado",
    45: "neblina", 48: "neblina com geada", 51: "garoa fraca", 53: "garoa", 55: "garoa forte",
    56: "garoa congelante", 57: "garoa congelante forte", 61: "chuva fraca", 63: "chuva", 65: "chuva forte",
    66: "chuva congelante", 67: "chuva congelante forte", 71: "neve fraca", 73: "neve", 75: "neve forte",
    77: "granizo miúdo", 80: "pancadas de chuva", 81: "pancadas de chuva fortes", 82: "temporal",
    85: "pancadas de neve", 86: "nevasca", 95: "trovoada", 96: "trovoada com granizo", 99: "trovoada forte com granizo",
}


def descrever_tempo(codigo: object) -> str:
    return TEMPO.get(codigo, "tempo esquisito") if isinstance(codigo, int) else "tempo esquisito"


def _contexto() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def baixar(url: str) -> bytes | None:
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(pedido, timeout=ESPERA_S, context=_contexto()) as resposta:
            return resposta.read(2_000_000)
    except (OSError, ValueError):
        return None


def baixar_json(url: str) -> object:
    dados = baixar(url)
    if dados is None:
        return None
    try:
        return json.loads(dados.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None


# ---- leitores: recebem a resposta crua e devolvem frases. Testáveis sem rede. ----


@dataclass(frozen=True)
class Lugar:
    nome: str
    lat: float
    lon: float


def ler_local(dados: object) -> Lugar | None:
    """Resposta do ipwho.is: só a cidade aproximada, para o clima."""
    if not isinstance(dados, dict) or dados.get("success") is False:
        return None
    try:
        return Lugar(str(dados.get("city") or "aqui"), float(dados["latitude"]), float(dados["longitude"]))
    except (KeyError, TypeError, ValueError):
        return None


def ler_geocodificacao(dados: object) -> Lugar | None:
    if not isinstance(dados, dict):
        return None
    resultados = dados.get("results")
    if not isinstance(resultados, list) or not resultados or not isinstance(resultados[0], dict):
        return None
    r = resultados[0]
    try:
        return Lugar(str(r.get("name", "aqui")), float(r["latitude"]), float(r["longitude"]))
    except (KeyError, TypeError, ValueError):
        return None


def _graus(valor: object) -> str:
    return f"{round(valor)}°C" if isinstance(valor, (int, float)) else "?"


def ler_clima(dados: object, lugar: str) -> dict[str, list[str]]:
    if not isinstance(dados, dict):
        return {}
    saida: dict[str, list[str]] = {}
    atual = dados.get("current")
    if isinstance(atual, dict) and "temperature_2m" in atual:
        tempo = descrever_tempo(atual.get("weather_code"))
        temp = _graus(atual.get("temperature_2m"))
        sente = _graus(atual.get("apparent_temperature"))
        umidade = atual.get("relative_humidity_2m")
        linhas = [f"Agora em {lugar}: {temp}, {tempo}."]
        if sente != temp and sente != "?":
            linhas.append(f"Sensação de {sente}.")
        if isinstance(umidade, (int, float)):
            linhas.append(f"Umidade {round(umidade)}%.")
        saida["clima_agora"] = [" ".join(linhas)]
    diario = dados.get("daily")
    if isinstance(diario, dict):
        def dia(i: int) -> tuple[str, str, str, object] | None:
            try:
                return (
                    descrever_tempo(diario["weather_code"][i]),
                    _graus(diario["temperature_2m_max"][i]),
                    _graus(diario["temperature_2m_min"][i]),
                    diario.get("precipitation_probability_max", [None, None])[i],
                )
            except (KeyError, IndexError, TypeError):
                return None

        hoje, amanha = dia(0), dia(1)
        if hoje:
            saida["clima_hoje"] = [f"Hoje em {lugar}: {hoje[0]}, máxima de {hoje[1]} e mínima de {hoje[2]}."]
            chuva = hoje[3]
            if isinstance(chuva, (int, float)):
                if chuva >= 60:
                    saida["clima_chuva"] = [f"Leva guarda-chuva! {round(chuva)}% de chance de chuva hoje."]
                elif chuva >= 30:
                    saida["clima_chuva"] = [f"Pode chover hoje: {round(chuva)}% de chance. Fica esperto."]
                else:
                    saida["clima_chuva"] = [f"Chuva hoje? Só {round(chuva)}% de chance. Pode deixar o guarda-chuva."]
        if amanha:
            saida["clima_amanha"] = [f"Amanhã em {lugar}: {amanha[0]}, de {amanha[2]} a {amanha[1]}."]
    return saida


def _limpar_titulo(titulo: str) -> str:
    """O Google Notícias põe ' - Nome do Jornal' no fim. Fica a fonte entre parênteses."""
    titulo = " ".join(titulo.split())
    if " - " in titulo:
        texto, fonte = titulo.rsplit(" - ", 1)
        if 0 < len(fonte) <= 40:
            return f"{texto} ({fonte})"
    return titulo


def ler_rss(dados: bytes | None, limite: int = 12) -> list[str]:
    if not dados:
        return []
    try:
        raiz = ET.fromstring(dados)
    except ET.ParseError:
        return []
    titulos = []
    for item in raiz.iter("item"):
        titulo = item.findtext("title")
        if titulo and titulo.strip():
            titulos.append(_limpar_titulo(titulo.strip()))
        if len(titulos) >= limite:
            break
    return titulos


def _reais(valor: object, casas: int = 2) -> str | None:
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    texto = f"{numero:,.{casas}f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def ler_cotacao(dados: object) -> dict[str, list[str]]:
    if not isinstance(dados, dict):
        return {}
    saida = {}
    for chave, fonte, nome, casas in (
        ("USDBRL", "cotacao_dolar", "O dólar", 2),
        ("EURBRL", "cotacao_euro", "O euro", 2),
        ("BTCBRL", "cotacao_bitcoin", "Um bitcoin", 0),
    ):
        moeda = dados.get(chave)
        if not isinstance(moeda, dict):
            continue
        preco = _reais(moeda.get("bid"), casas)
        if preco is None:
            continue
        frase = f"{nome} está {preco}."
        try:
            variacao = float(moeda.get("pctChange"))
        except (TypeError, ValueError):
            variacao = None
        if variacao is not None:
            sentido = "subiu" if variacao > 0 else "caiu" if variacao < 0 else "ficou parado"
            porcento = f"{abs(variacao):.2f}".replace(".", ",")
            frase += f" Hoje {sentido} {porcento}%." if variacao else " Hoje ficou parado."
        saida[fonte] = [frase]
    return saida


def ler_historia(dados: object, limite: int = 15) -> list[str]:
    if not isinstance(dados, dict) or not isinstance(dados.get("events"), list):
        return []
    frases = []
    for evento in dados["events"]:
        if not isinstance(evento, dict):
            continue
        texto, ano = evento.get("text"), evento.get("year")
        if isinstance(texto, str) and isinstance(ano, int) and len(texto) < 220:
            frases.append(f"Num dia como hoje, em {ano}: {texto.strip()}")
        if len(frases) >= limite:
            break
    return frases


def ler_wiki(dados: object) -> list[str]:
    if not isinstance(dados, dict):
        return []
    titulo, resumo = dados.get("title"), dados.get("extract")
    if not isinstance(titulo, str) or not isinstance(resumo, str) or not resumo.strip():
        return []
    resumo = " ".join(resumo.split())
    if len(resumo) > 230:
        corte = resumo[:230].rsplit(". ", 1)[0]
        resumo = (corte if len(corte) > 80 else resumo[:227]).rstrip(".") + "..."
    return [f"Li na Wikipédia sobre {titulo}: {resumo}"]


def ler_feriados(dados: object, hoje: date) -> list[str]:
    if not isinstance(dados, list):
        return []
    for feriado in dados:
        if not isinstance(feriado, dict):
            continue
        try:
            dia = date.fromisoformat(str(feriado.get("date")))
        except ValueError:
            continue
        if dia < hoje:
            continue
        nome = feriado.get("name", "feriado")
        falta = (dia - hoje).days
        if falta == 0:
            return [f"Hoje é feriado: {nome}! Por que você tá no computador?"]
        if falta == 1:
            return [f"Amanhã é feriado: {nome}! Já tem planos?"]
        return [f"Faltam {falta} dias para o próximo feriado: {nome}, em {dia:%d/%m}."]
    return []


# ---- o computador ----


def _psutil():
    try:
        import psutil

        return psutil
    except ImportError:
        return None


def _tamanho(n: float) -> str:
    for unidade in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unidade == "TB":
            return f"{n:.0f} {unidade}" if unidade in ("B", "KB") else f"{n:.1f} {unidade}".replace(".", ",")
        n /= 1024
    return f"{n:.1f} TB"


def _duracao(segundos: float) -> str:
    minutos = int(segundos // 60)
    horas, minutos = divmod(minutos, 60)
    dias, horas = divmod(horas, 24)
    partes = []
    if dias:
        partes.append(f"{dias} dia" + ("s" if dias > 1 else ""))
    if horas:
        partes.append(f"{horas} hora" + ("s" if horas > 1 else ""))
    if minutos or not partes:
        partes.append(f"{minutos} minuto" + ("s" if minutos != 1 else ""))
    return " e ".join(partes[:2])


def info_computador(agora: datetime | None = None) -> dict[str, list[str]]:
    """Tudo local. Sem psutil, fica o que a biblioteca padrão consegue."""
    agora = agora or datetime.now()
    saida: dict[str, list[str]] = {}
    ps = _psutil()
    semana = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"][agora.weekday()]
    saida["hora"] = [f"Agora são {agora:%H:%M} de {semana}, {agora:%d/%m}."]
    saida["sistema"] = [f"Você usa {platform.system() or 'um sistema'} {platform.release()} num processador {platform.machine() or 'misterioso'}. Chique."]
    try:
        disco = shutil.disk_usage(Path.home())
        livre = disco.free / disco.total * 100
        frase = f"Seu disco tem {_tamanho(disco.free)} livres de {_tamanho(disco.total)} ({livre:.0f}%)."
        if livre < 10:
            frase += " Tá quase cheio! Posso comer uns arquivos?"
        saida["disco"] = [frase]
    except OSError:
        pass
    try:
        downloads = Path.home() / "Downloads"
        if downloads.is_dir():
            n = sum(1 for _ in downloads.iterdir())
            saida["downloads"] = [f"Sua pasta Downloads tem {n} coisas. {'Que bagunça!' if n > 100 else 'Tá organizadinha.'}"]
    except OSError:
        pass
    if ps is None:
        if hasattr(os, "getloadavg"):
            carga = os.getloadavg()[0]
            saida["cpu"] = [f"A carga do processador está em {carga:.1f}."]
        return saida
    try:
        uso = ps.cpu_percent(interval=0.3)
        saida["cpu"] = [f"O processador tá em {uso:.0f}%." + (" Tá suando!" if uso > 70 else " Tranquilo.")]
    except Exception:
        pass
    try:
        mem = ps.virtual_memory()
        saida["memoria"] = [f"Memória: {mem.percent:.0f}% usada, sobram {_tamanho(mem.available)}."]
    except Exception:
        pass
    try:
        bateria = ps.sensors_battery()
        if bateria is not None:
            ligado = "na tomada" if bateria.power_plugged else "na bateria"
            frase = f"Bateria em {bateria.percent:.0f}%, {ligado}."
            if not bateria.power_plugged and bateria.percent < 20:
                frase += " Liga o carregador!"
            saida["bateria"] = [frase]
    except Exception:
        pass
    try:
        ligado_ha = time.time() - ps.boot_time()
        saida["tempo_ligado"] = [f"O computador está ligado há {_duracao(ligado_ha)}."]
    except Exception:
        pass
    try:
        processos = list(ps.process_iter(["name", "memory_info"]))
        saida["processos"] = [f"Tem {len(processos)} programas e processos rodando agora. Eu sou o mais fofo."]
        maiores = sorted(
            (p for p in processos if p.info.get("memory_info") and p.info.get("name")),
            key=lambda p: p.info["memory_info"].rss,
            reverse=True,
        )
        if maiores:
            p = maiores[0]
            saida["maior_programa"] = [f"Quem mais come memória agora é o {p.info['name']}: {_tamanho(p.info['memory_info'].rss)}. Guloso igual eu."]
    except Exception:
        pass
    return saida


# ---- cache e buscas ----


class Informante:
    """Guarda as frases de cada fonte. As buscas rodam numa thread por vez."""

    def __init__(self, acaso: random.Random | None = None, baixador=None) -> None:
        self._acaso = acaso or random.Random()
        self._baixar = baixador or baixar
        self._frases: dict[str, list[str]] = {}
        self._quando: dict[str, float] = {}
        self._ditas: set[str] = set()
        self._trava = threading.Lock()
        self._buscando = False
        self.lugar: Lugar | None = None

    def guardar(self, frases: dict[str, list[str]], agora: float | None = None) -> None:
        agora = time.time() if agora is None else agora
        with self._trava:
            for fonte, lista in frases.items():
                if lista:
                    self._frases[fonte] = list(lista)
                    self._quando[fonte] = agora

    def tem(self, fonte: str) -> bool:
        with self._trava:
            return bool(self._frases.get(fonte))

    def frase(self, fonte: str) -> str | None:
        """Sorteia uma frase da fonte, evitando repetir as já ditas."""
        with self._trava:
            lista = self._frases.get(fonte) or []
            novas = [f for f in lista if f not in self._ditas] or lista
            if not novas:
                return None
            escolhida = self._acaso.choice(novas)
            self._ditas.add(escolhida)
            return escolhida

    def velha(self, fonte: str, agora: float) -> bool:
        return agora - self._quando.get(fonte, 0) > VALIDADE_S

    def atualizar_computador(self) -> None:
        self.guardar(info_computador())

    def buscar(self, cidade: str = "", internet: bool = True, em_segundo_plano: bool = True) -> None:
        """Renova o que estiver velho. Roda numa thread para a rede lenta não travar o rato."""
        if self._buscando:
            return
        self._buscando = True
        if em_segundo_plano:
            threading.Thread(target=self._buscar, args=(cidade, internet), daemon=True).start()
        else:
            self._buscar(cidade, internet)

    def _buscar(self, cidade: str, internet: bool) -> None:
        try:
            self.atualizar_computador()
            if internet:
                self._buscar_rede(cidade, time.time())
        finally:
            self._buscando = False

    def _json(self, url: str) -> object:
        dados = self._baixar(url)
        if dados is None:
            return None
        try:
            return json.loads(dados.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return None

    def _buscar_rede(self, cidade: str, agora: float) -> None:
        if self.velha("clima_agora", agora):
            lugar = None
            if cidade.strip():
                lugar = ler_geocodificacao(self._json(URL_GEO + urllib.parse.quote(cidade.strip())))
            lugar = lugar or self.lugar or ler_local(self._json(URL_LOCAL))
            if lugar is not None:
                self.lugar = lugar
                self.guardar(ler_clima(self._json(URL_CLIMA.format(lat=lugar.lat, lon=lugar.lon)), lugar.nome), agora)
        for fonte, url in URL_NOTICIAS.items():
            if self.velha(fonte, agora):
                titulos = ler_rss(self._baixar(url))
                if not titulos and fonte in RESERVA_NOTICIAS:
                    titulos = ler_rss(self._baixar(RESERVA_NOTICIAS[fonte]))
                self.guardar({fonte: titulos}, agora)
        if self.velha("cotacao_dolar", agora):
            self.guardar(ler_cotacao(self._json(URL_COTACAO)), agora)
        hoje = datetime.now()
        if self.velha("hoje_na_historia", agora - VALIDADE_S * 5):
            self.guardar({"hoje_na_historia": ler_historia(self._json(URL_HISTORIA.format(mes=hoje.month, dia=hoje.day)))}, agora)
        if self.velha("proximo_feriado", agora - VALIDADE_S * 5):
            self.guardar({"proximo_feriado": ler_feriados(self._json(URL_FERIADOS.format(ano=hoje.year)), hoje.date())}, agora)
            if not self.tem("proximo_feriado"):
                proximo = self._json(URL_FERIADOS.format(ano=hoje.year + 1))
                self.guardar({"proximo_feriado": ler_feriados(proximo, hoje.date())}, agora)
        wiki = ler_wiki(self._json(URL_WIKI))
        if wiki:
            with self._trava:
                atual = self._frases.get("wikipedia", [])
                self._frases["wikipedia"] = (atual + wiki)[-8:]
                self._quando["wikipedia"] = agora
