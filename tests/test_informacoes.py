import json
import random
import unittest
from datetime import date, datetime

from alarma import informacoes as info

RSS = b"""<?xml version="1.0"?><rss><channel><title>x</title>
<item><title>Chuva forte atinge capital - G1</title></item>
<item><title>  Time vence   cl\xc3\xa1ssico </title></item>
</channel></rss>"""

CLIMA = {
    "current": {"temperature_2m": 28.4, "apparent_temperature": 31.2, "weather_code": 2, "relative_humidity_2m": 70},
    "daily": {
        "weather_code": [61, 0],
        "temperature_2m_max": [30.1, 29.0],
        "temperature_2m_min": [22.6, 21.2],
        "precipitation_probability_max": [80, 10],
    },
}


class TestLeitores(unittest.TestCase):
    def test_clima(self) -> None:
        f = info.ler_clima(CLIMA, "Salvador")
        self.assertEqual(f["clima_agora"], ["Agora em Salvador: 28°C, parcialmente nublado. Sensação de 31°C. Umidade 70%."])
        self.assertIn("máxima de 30°C", f["clima_hoje"][0])
        self.assertIn("guarda-chuva", f["clima_chuva"][0])
        self.assertIn("céu limpo", f["clima_amanha"][0])

    def test_clima_estragado(self) -> None:
        self.assertEqual(info.ler_clima(None, "x"), {})
        self.assertEqual(info.ler_clima({"daily": {"weather_code": []}}, "x"), {})

    def test_rss(self) -> None:
        self.assertEqual(info.ler_rss(RSS), ["Chuva forte atinge capital (G1)", "Time vence clássico"])
        self.assertEqual(info.ler_rss(b"<rss"), [])
        self.assertEqual(info.ler_rss(None), [])

    def test_cotacao(self) -> None:
        dados = {"USDBRL": {"bid": "5.4321", "pctChange": "-0.5"}, "BTCBRL": {"bid": "512345.6", "pctChange": "1.25"}}
        f = info.ler_cotacao(dados)
        self.assertEqual(f["cotacao_dolar"], ["O dólar está R$ 5,43. Hoje caiu 0,50%."])
        self.assertEqual(f["cotacao_bitcoin"], ["Um bitcoin está R$ 512.346. Hoje subiu 1,25%."])
        self.assertNotIn("cotacao_euro", f)

    def test_historia_e_wiki(self) -> None:
        h = info.ler_historia({"events": [{"text": "Algo aconteceu.", "year": 1900}, {"text": 3}]})
        self.assertEqual(h, ["Num dia como hoje, em 1900: Algo aconteceu."])
        w = info.ler_wiki({"title": "Queijo", "extract": "O queijo é bom. " * 30})
        self.assertTrue(w[0].startswith("Li na Wikipédia sobre Queijo:"))
        self.assertLess(len(w[0]), 290)

    def test_feriados(self) -> None:
        dados = [{"date": "2026-11-02", "name": "Finados"}, {"date": "2026-11-15", "name": "República"}]
        self.assertIn("Faltam 9 dias", info.ler_feriados(dados, date(2026, 11, 6))[0])
        self.assertIn("Amanhã", info.ler_feriados(dados, date(2026, 11, 14))[0])
        self.assertEqual(info.ler_feriados(dados, date(2026, 12, 1)), [])

    def test_local(self) -> None:
        self.assertEqual(info.ler_local({"city": "Salvador", "latitude": -12.9, "longitude": -38.5}).nome, "Salvador")
        self.assertIsNone(info.ler_local({"success": False}))
        g = info.ler_geocodificacao({"results": [{"name": "Recife", "latitude": -8.0, "longitude": -34.9}]})
        self.assertEqual(g.nome, "Recife")
        self.assertIsNone(info.ler_geocodificacao({}))

    def test_computador(self) -> None:
        f = info.info_computador(datetime(2026, 11, 6, 9, 5))
        self.assertEqual(f["hora"], ["Agora são 09:05 de sexta, 06/11."])
        self.assertIn("disco", f)


class TestInformante(unittest.TestCase):
    def test_busca_completa_com_rede_falsa(self) -> None:
        def baixador(url: str) -> bytes | None:
            if "ipwho" in url:
                return json.dumps({"city": "Salvador", "latitude": -12.9, "longitude": -38.5}).encode()
            if "forecast" in url:
                return json.dumps(CLIMA).encode()
            if "rss" in url:
                return RSS
            if "awesomeapi" in url:
                return json.dumps({"USDBRL": {"bid": "5", "pctChange": "0"}}).encode()
            return None

        i = info.Informante(random.Random(1), baixador)
        i.buscar(em_segundo_plano=False)
        self.assertIn("Salvador", i.frase("clima_agora"))
        self.assertTrue(i.tem("noticia_mundo"))
        self.assertTrue(i.tem("cotacao_dolar"))
        self.assertTrue(i.tem("hora"))

    def test_sem_internet_so_o_computador(self) -> None:
        chamadas = []
        i = info.Informante(random.Random(1), lambda url: chamadas.append(url))
        i.buscar(internet=False, em_segundo_plano=False)
        self.assertEqual(chamadas, [])
        self.assertTrue(i.tem("hora"))
        self.assertFalse(i.tem("clima_agora"))

    def test_nao_repete_ate_acabar(self) -> None:
        i = info.Informante(random.Random(1))
        i.guardar({"x": ["a", "b"]})
        self.assertEqual({i.frase("x"), i.frase("x")}, {"a", "b"})
        self.assertIn(i.frase("x"), ("a", "b"))
