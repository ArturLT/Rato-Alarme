import json
import random
import tempfile
import unittest
from pathlib import Path

from alarma.cerebro import (
    DESISTIU,
    DESISTIU_TXT,
    EVITA_TXT,
    GOSTA,
    JANELA_S,
    LIMITE,
    XP_POR_NIVEL,
    Cerebro,
)


class TestAprendizado(unittest.TestCase):
    def test_tapa_tira_valor_da_ultima_acao_mais_que_da_anterior(self) -> None:
        c = Cerebro()
        c.lembrar("fala:piada", 100.0)
        c.lembrar("fechar_aba", 118.0)
        afetadas = c.punir(120.0)
        self.assertEqual(afetadas[0], "fechar_aba")
        self.assertLess(c.valor("fechar_aba"), c.valor("fala:piada"))
        self.assertLess(c.valor("fala:piada"), 0)

    def test_acao_antiga_demais_nao_leva_credito(self) -> None:
        c = Cerebro()
        c.lembrar("minimizar", 0.0)
        c.punir(JANELA_S + 5)
        self.assertEqual(c.valor("minimizar"), 0.0)

    def test_carinho_aumenta_valor_e_xp(self) -> None:
        c = Cerebro()
        c.lembrar("fala:clima", 10.0)
        c.recompensar(12.0, queijo=True)
        self.assertGreater(c.valor("fala:clima"), 0)
        self.assertGreater(c.xp, 0)

    def test_valor_tem_limite(self) -> None:
        c = Cerebro()
        for _ in range(50):
            c.punir(0.0, acao="mover_cursor")
        self.assertEqual(c.valor("mover_cursor"), -LIMITE)
        self.assertEqual(c.opiniao("mover_cursor"), DESISTIU_TXT)

    def test_opinioes(self) -> None:
        c = Cerebro()
        c.pesos = {"a": 2.0, "b": -1.5, "c": DESISTIU - 0.1}
        self.assertEqual(c.opiniao("a"), GOSTA)
        self.assertEqual(c.opiniao("b"), EVITA_TXT)
        self.assertEqual(c.opiniao("c"), DESISTIU_TXT)

    def test_sem_liberdade_nunca_repete_o_que_desistiu(self) -> None:
        c = Cerebro()
        c.pesos["fechar_aba"] = -LIMITE
        acaso = random.Random(1)
        escolhas = {c.escolher([("fechar_aba", 1.0), ("fala", 1.0)], 0.0, acaso).acao for _ in range(500)}
        self.assertEqual(escolhas, {"fala"})

    def test_com_liberdade_as_vezes_teima(self) -> None:
        c = Cerebro()
        c.pesos["fechar_aba"] = -LIMITE
        acaso = random.Random(2)
        escolhas = [c.escolher([("fechar_aba", 1.0), ("fala", 1.0)], 1.0, acaso) for _ in range(2000)]
        teimosas = [e for e in escolhas if e.acao == "fechar_aba"]
        self.assertTrue(teimosas)
        self.assertTrue(all(e.teimosa for e in teimosas))
        self.assertLess(len(teimosas), 200)

    def test_prefere_o_que_ganhou_carinho(self) -> None:
        c = Cerebro()
        c.pesos["fala:noticia"] = 3.0
        acaso = random.Random(3)
        n = sum(c.escolher([("fala:noticia", 1.0), ("fala:piada", 1.0)], 0.2, acaso).acao == "fala:noticia" for _ in range(1000))
        self.assertGreater(n, 800)

    def test_nivel_sobe_com_xp(self) -> None:
        c = Cerebro()
        self.assertEqual(c.nivel, 1)
        c.xp = XP_POR_NIVEL * 2
        self.assertEqual(c.nivel, 3)

    def test_humor_volta_ao_meio(self) -> None:
        c = Cerebro()
        c.punir(0.0, forca=3)
        logo = c.humor(1.0)
        depois = c.humor(100_000.0)
        self.assertLess(logo, 50)
        self.assertGreater(depois, logo)

    def test_frases_ensinadas_sem_repetir(self) -> None:
        c = Cerebro()
        self.assertTrue(c.ensinar("  bom   dia, chefe "))
        self.assertFalse(c.ensinar("bom dia, chefe"))
        self.assertEqual(c.frases, ["bom dia, chefe"])
        c.esquecer_frase("bom dia, chefe")
        self.assertEqual(c.frases, [])


class TestMemoria(unittest.TestCase):
    def test_salva_e_le_de_volta(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "cerebro.json"
            c = Cerebro(caminho)
            c.lembrar("objeto", 0.0)
            c.recompensar(1.0)
            c.ensinar("queijo é vida")
            c.aprender_fato("nome", "Lucas")
            c.salvar()
            outro = Cerebro(caminho)
            self.assertAlmostEqual(outro.valor("objeto"), c.valor("objeto"))
            self.assertEqual(outro.frases, ["queijo é vida"])
            self.assertEqual(outro.fatos["nome"], "Lucas")
            self.assertEqual(outro.xp, c.xp)

    def test_arquivo_estragado_vira_filhote(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "cerebro.json"
            caminho.write_text("{isso não é json")
            self.assertEqual(Cerebro(caminho).xp, 0)
            caminho.write_text(json.dumps({"pesos": {"a": "x"}, "xp": True, "horas": [1]}))
            c = Cerebro(caminho)
            self.assertEqual(c.valor("a"), 0.0)
            self.assertEqual(c.horas, [0] * 24)

    def test_esquecer_tudo(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "cerebro.json"
            c = Cerebro(caminho)
            c.punir(0.0, acao="x")
            c.ensinar("oi")
            c.esquecer_tudo()
            self.assertEqual(c.pesos, {})
            self.assertEqual(Cerebro(caminho).frases, [])
