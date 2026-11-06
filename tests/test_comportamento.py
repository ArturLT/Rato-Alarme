import random
import unittest
from datetime import datetime

from alarma import comportamento as c
from alarma import repertorio as rep
from alarma.cerebro import LIMITE, Cerebro
from alarma.config import SEMPRE, Config


def tudo(_):
    return True


class TestRepertorio(unittest.TestCase):
    def test_mais_de_cem_interacoes_com_ids_unicos(self) -> None:
        todas = rep.todas()
        self.assertGreaterEqual(len(todas), 100)
        self.assertEqual(len({i.id for i in todas}), len(todas))

    def test_toda_categoria_e_permissao_existe(self) -> None:
        for i in rep.todas():
            if i.tipo in (rep.FALA, rep.INFO, rep.PERGUNTA):
                self.assertIn(i.categoria, rep.CATEGORIAS, i.id)
            if i.tipo == rep.TRAVESSURA:
                self.assertIn(i.permissao, rep.PERMISSOES, i.id)

    def test_falas_so_usam_fatos_que_ele_pergunta(self) -> None:
        perguntados = {i.fato for i in rep.todas() if i.tipo == rep.PERGUNTA}
        for i in rep.todas():
            for t in i.textos:
                self.assertLessEqual(rep.campos(t) - {"nome"}, perguntados, i.id)

    def test_preencher(self) -> None:
        self.assertEqual(rep.preencher("oi {nome}", {}), "oi humano")
        self.assertIsNone(rep.preencher("{comida}!", {}))
        self.assertEqual(rep.preencher("{comida}!", {"comida": "pizza"}), "pizza!")


class TestEscolhas(unittest.TestCase):
    def setUp(self) -> None:
        self.acaso = random.Random(5)

    def test_painel_desliga_categorias_e_permissoes(self) -> None:
        cfg = Config(falas=(rep.PIADAS,), permissoes=())
        ops = c.elegiveis(rep.todas(), cfg, Cerebro(), tudo, tudo)
        self.assertTrue(ops)
        self.assertFalse([i for i in ops if i.tipo == rep.TRAVESSURA])
        self.assertTrue(all(i.categoria in (rep.PIADAS, rep.BRINCADEIRA) for i in ops))

    def test_sem_internet_sem_noticias(self) -> None:
        cfg = Config(internet=False)
        ops = c.elegiveis(rep.todas(), cfg, Cerebro(), tudo, tudo)
        self.assertFalse([i for i in ops if i.internet])

    def test_info_so_quando_ja_buscou(self) -> None:
        ops = c.elegiveis(rep.todas(), Config(), Cerebro(), lambda f: f == "hora", tudo)
        infos = [i.fonte for i in ops if i.tipo == rep.INFO]
        self.assertEqual(infos, ["hora"])

    def test_nao_pergunta_o_que_ja_sabe(self) -> None:
        cerebro = Cerebro()
        cerebro.aprender_fato("nome", "Lucas")
        ops = c.elegiveis(rep.todas(), Config(), cerebro, tudo, tudo)
        self.assertNotIn("pergunta-nome", {i.id for i in ops})
        self.assertIn("lembranca-01", {i.id for i in ops})

    def test_travessura_zero_quase_nunca_apronta(self) -> None:
        ops = c.elegiveis(rep.todas(), Config(travessura=0), Cerebro(), tudo, tudo)
        planos = [c.planejar(ops, Config(travessura=0), Cerebro(), self.acaso) for _ in range(500)]
        n = sum(p.interacao.tipo == rep.TRAVESSURA for p in planos)
        self.assertLess(n, 50)

    def test_travessura_cem_apronta_muito(self) -> None:
        cfg = Config(travessura=100)
        ops = c.elegiveis(rep.todas(), cfg, Cerebro(), tudo, tudo)
        n = sum(c.planejar(ops, cfg, Cerebro(), self.acaso).interacao.tipo == rep.TRAVESSURA for _ in range(500))
        self.assertGreater(n, 200)

    def test_desaprendeu_todas_as_travessuras_e_avisa(self) -> None:
        cfg = Config(travessura=100, liberdade=0)
        cerebro = Cerebro()
        ops = c.elegiveis(rep.todas(), cfg, cerebro, tudo, tudo)
        for i in ops:
            if i.tipo == rep.TRAVESSURA:
                cerebro.pesos[i.id] = -LIMITE
        planos = [c.planejar(ops, cfg, cerebro, self.acaso) for _ in range(300)]
        self.assertFalse([p for p in planos if p.interacao.tipo == rep.TRAVESSURA])
        self.assertTrue([p for p in planos if p.desistiu is not None])

    def test_extras_trazem_frases_ensinadas(self) -> None:
        cerebro = Cerebro()
        cerebro.ensinar("vai dar certo")
        cerebro.desbloquear("segredo-0")
        ids = {i.id for i in c.extras(cerebro, Config())}
        self.assertEqual(ids, {"ensinada:vai dar certo", "segredo-0"})


class TestTempo(unittest.TestCase):
    def test_intensidade_alta_aparece_mais(self) -> None:
        acaso = random.Random(1)
        alta = sum(c.espera_ate_aparecer(100, acaso) for _ in range(100))
        baixa = sum(c.espera_ate_aparecer(0, acaso) for _ in range(100))
        self.assertLess(alta * 10, baixa)
        self.assertGreaterEqual(c.espera_depois_de_expulso(100, acaso), 20 * 60)

    def test_dormir(self) -> None:
        agora = datetime(2026, 11, 6, 10, 0)
        self.assertTrue(Config(dormir_ate=SEMPRE).dormindo(agora))
        self.assertTrue(Config(dormir_ate="2026-11-06T11:00").dormindo(agora))
        self.assertFalse(Config(dormir_ate="2026-11-06T09:00").dormindo(agora))
        self.assertFalse(Config(dormir_ate="banana").dormindo(agora))
        self.assertFalse(Config().dormindo(agora))

    def test_periodos(self) -> None:
        self.assertEqual([c.periodo(h) for h in (3, 8, 14, 20)], ["madrugada", "manha", "tarde", "noite"])


class TestGestos(unittest.TestCase):
    def test_tres_tapas_expulsam(self) -> None:
        t = c.Tapas()
        self.assertFalse(t.bater(0))
        self.assertFalse(t.bater(1))
        self.assertTrue(t.bater(2))
        self.assertFalse(t.bater(3))

    def test_tapas_espacados_nao_expulsam(self) -> None:
        t = c.Tapas()
        self.assertFalse(any(t.bater(x * 10.0) for x in range(10)))

    def test_carinho_e_mexer_o_mouse_em_cima(self) -> None:
        k = c.Carinho()
        feito = False
        for passo in range(40):
            x = 100 + (40 if passo % 2 else -40)
            feito = k.notar(passo * 0.05, (x, 100), True) or feito
        self.assertTrue(feito)

    def test_passar_reto_nao_e_carinho(self) -> None:
        k = c.Carinho()
        self.assertFalse(any(k.notar(i * 0.05, (i * 30, 0), i < 3) for i in range(30)))
