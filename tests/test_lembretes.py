import random
import tempfile
import unittest
from datetime import date, datetime, time
from pathlib import Path

from alarma import config
from alarma import lembretes as lem
from alarma.lembretes import DIAS_UTEIS, Lembrete


class TestLembretes(unittest.TestCase):
    def setUp(self) -> None:
        self.agua = Lembrete("a1", time(10, 0), "agua")
        self.sexta = datetime(2026, 11, 6, 10, 3)  # sexta-feira

    def test_toca_na_hora_e_so_uma_vez(self) -> None:
        self.assertEqual(lem.devidos([self.agua], self.sexta, set()), [self.agua])
        self.assertEqual(lem.devidos([self.agua], self.sexta, {"2026-11-06/a1"}), [])

    def test_fora_da_janela_nao_toca(self) -> None:
        self.assertEqual(lem.devidos([self.agua], datetime(2026, 11, 6, 9, 59), set()), [])
        self.assertEqual(lem.devidos([self.agua], datetime(2026, 11, 6, 10, lem.TOLERANCIA_MIN), set()), [])

    def test_dias_da_semana_e_desligado(self) -> None:
        util = self.agua.com(dias=DIAS_UTEIS)
        sabado = datetime(2026, 11, 7, 10, 1)
        self.assertEqual(lem.devidos([util], sabado, set()), [])
        self.assertEqual(lem.devidos([self.agua.com(ativo=False)], self.sexta, set()), [])

    def test_texto_do_aviso(self) -> None:
        acaso = random.Random(1)
        titulo, texto = lem.texto_do_aviso(Lembrete("x", time(9), "mensagem", "Ligar pro banco"), {}, {}, acaso)
        self.assertEqual((titulo, texto), ("Lembrete", "Ligar pro banco"))
        _, texto = lem.texto_do_aviso(Lembrete("y", time(9), "clima"), {}, {"clima": "Sol, 30°C."}, acaso)
        self.assertEqual(texto, "Sol, 30°C.")
        _, texto = lem.texto_do_aviso(self.agua, {"nome": "Lucas"}, {}, random.Random(0))
        self.assertTrue(texto)

    def test_resumo(self) -> None:
        self.assertEqual(self.agua.com(dias=DIAS_UTEIS).resumo(), "10:00 · dias úteis · Beber água")

    def test_vai_e_volta_pelo_config(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "c.json"
            cfg = config.Config(lembretes=(self.agua, Lembrete("b", time(8, 30), "mensagem", "oi", (0, 2))))
            config.salvar(caminho, cfg)
            self.assertEqual(config.carregar(caminho).lembretes, cfg.lembretes)

    def test_lembrete_estragado_e_ignorado(self) -> None:
        lista = lem.ler_lista([{"id": "a", "hora": "25:00"}, {"hora": "10:00"}, "x", {"id": "ok", "hora": "07:05", "tipo": "??", "dias": [9, 1]}])
        self.assertEqual(len(lista), 1)
        self.assertEqual((lista[0].tipo, lista[0].dias), ("mensagem", (1,)))

    def test_tocados_de_hoje(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "t.json"
            lem.gravar_tocados({"2026-11-06/a1", "2026-11-05/a1"}, caminho)
            self.assertEqual(lem.ler_tocados(caminho, date(2026, 11, 6)), {"2026-11-06/a1"})
