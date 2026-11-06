"""O pet de verdade, sem tela (plugin offscreen do Qt) e com um relógio de mentira."""

import os
import random
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from shiboken6 import Shiboken

from alarma import config
from alarma import repertorio as rep
from alarma.cerebro import Cerebro
from alarma.painel import Painel
from alarma.pet import Passo, Pet

app = QApplication.instance() or QApplication([])


class Relogio:
    def __init__(self) -> None:
        self.t = 1000.0

    def monotonic(self) -> float:
        return self.t

    def time(self) -> float:
        return 1_700_000_000 + self.t


class Base(unittest.TestCase):
    def setUp(self) -> None:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        ambiente = mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": pasta.name, "XDG_STATE_HOME": pasta.name})
        ambiente.start()
        self.addCleanup(ambiente.stop)
        self.relogio = Relogio()
        for alvo, valor in (
            ("alarma.pet.time", self.relogio),
            ("alarma.sistema.tem_hyprland", lambda: False),
            ("alarma.travessuras.mutar", lambda *_: None),
            ("alarma.travessuras.restaurar_som", lambda *_: None),
            ("alarma.travessuras.abrir_youtube", lambda: None),
            ("alarma.acoes.falar", lambda *_: None),
        ):
            trava = mock.patch(alvo, valor)
            trava.start()
            self.addCleanup(trava.stop)

    def pet(self, criatura=None, **cfg) -> Pet:
        config.salvar(config.caminho_padrao(), config.Config(**cfg))
        pet = Pet(criatura, acaso=random.Random(7))
        pet.informante.buscar = lambda *a, **k: None
        pet.iniciar()
        for relogio in pet._relogios:
            relogio.stop()
        pet._area = (0, 0, 1600, 900)
        pet._tela.cursor = lambda: (5, 5)
        pet._tela.area = lambda _c: (0, 0, 1600, 900)
        self.addCleanup(self._parar, pet)
        return pet

    def _parar(self, pet: Pet) -> None:
        pet.desligar()

    def rodar(self, pet: Pet, segundos: float, passo: float = 0.05) -> None:
        for _ in range(int(segundos / passo)):
            self.relogio.t += passo
            pet._quadro()


class TestVisita(Base):
    def test_aparece_surge_e_desenha(self) -> None:
        pet = self.pet()
        pet.aparecer()
        self.assertTrue(pet._janela.isVisible())
        self.assertEqual(pet.estado, Pet.ATIVO)
        self.rodar(pet, 0.2)
        self.assertEqual(pet._anim, "surgindo")
        self.assertFalse(pet._janela.pixmap().isNull())

    def test_aparece_sozinho_quando_chega_a_hora(self) -> None:
        pet = self.pet(intensidade=100)
        self.relogio.t += 4000
        pet._decidir()
        self.assertEqual(pet.estado, Pet.ATIVO)

    def test_pet_desligado_nao_aparece(self) -> None:
        pet = self.pet(pet_ligado=False)
        self.relogio.t += 100_000
        pet._decidir()
        self.assertEqual(pet.estado, Pet.AUSENTE)

    def test_uma_visita_inteira_termina_sumindo(self) -> None:
        pet = self.pet(intensidade=0, permissoes=())
        pet.aparecer()
        pet._fim_visita = self.relogio.t + 20
        self.rodar(pet, 120, 0.1)
        self.assertEqual(pet.estado, Pet.AUSENTE)
        self.assertFalse(pet._janela.isVisible())
        self.assertGreater(pet.segundos_ate_voltar(), 0)

    def test_saudacao_do_boot_traz_alguma_coisa(self) -> None:
        pet = self.pet()
        pet.informante.guardar({"clima_agora": ["Agora em Salvador: 30°C, sol."]})
        pet.saudar()
        self.rodar(pet, 1.2)
        self.assertEqual(pet._passo.tipo, "falar")
        self.assertEqual(pet._anim, "acenando")
        self.assertIsNotNone(pet._balao)
        self.rodar(pet, 8)
        self.assertEqual(pet._passo.tipo, "placa")
        self.assertIn("Salvador", pet._passo.texto)
        self.assertIsNotNone(pet._placa)

    def test_alarme_na_tela_esconde_o_pet(self) -> None:
        criatura = mock.Mock(ativa=False)
        pet = self.pet(criatura)
        pet.aparecer()
        criatura.ativa = True
        pet._decidir()
        self.assertEqual(pet.estado, Pet.AUSENTE)
        self.assertFalse(pet._janela.isVisible())
        pet.aparecer()
        self.assertEqual(pet.estado, Pet.AUSENTE)


class TestTapaECarinho(Base):
    def test_tapa_ensina_a_evitar_o_que_ele_acabou_de_fazer(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet._executar(rep.por_id()["piada-01"])
        self.relogio.t += 2
        pet.tapa()
        self.assertLess(pet.cerebro.valor("piada-01"), 0)
        self.assertEqual(pet._fila[0].anim, "acerto")
        self.assertEqual(Cerebro(Path(os.environ["XDG_STATE_HOME"]) / "alarma-meme" / "cerebro.json").valor("piada-01"), pet.cerebro.valor("piada-01"))

    def test_tres_tapas_expulsam_por_pelo_menos_20_minutos(self) -> None:
        pet = self.pet(intensidade=100)
        pet.aparecer()
        for _ in range(3):
            pet.tapa()
            self.relogio.t += 0.5
        self.rodar(pet, 15)
        self.assertEqual(pet.estado, Pet.AUSENTE)
        self.assertGreaterEqual(pet.segundos_ate_voltar(), 19 * 60)

    def test_carinho_com_o_mouse_deixa_feliz(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet.x, pet.y = 500, 500
        pontos = iter([(560 + (60 if i % 2 else -20), 600) for i in range(400)])
        pet._tela.cursor = lambda: next(pontos)
        antes = pet.cerebro.xp
        self.rodar(pet, 3)
        self.assertGreater(pet.cerebro.xp, antes)

    def test_queijo_sobe_de_nivel_e_ensina_segredo(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet._tela.cursor = lambda: (700, 700)
        for _ in range(5):
            pet.dar_queijo()
            self.rodar(pet, 12, 0.1)
        self.assertGreaterEqual(pet.cerebro.nivel, 2)
        self.assertIn("segredo-0", pet.cerebro.desbloqueadas)

    def test_comida_vai_ate_ela_e_enche_a_barriga(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet.nec.barriga = 20
        pet._tela.cursor = lambda: (1200, 700)
        pet.dar_comida("biscoito")
        self.assertEqual([o.nome for o in pet._objetos], ["biscoito"])
        self.rodar(pet, 12, 0.1)
        self.assertEqual(pet._objetos, [])
        self.assertGreater(pet.nec.barriga, 40)
        self.assertEqual(pet.nec.refeicoes, 1)

    def test_voto_no_balao_e_especifico(self) -> None:
        pet = self.pet()
        pet.aparecer()
        i = rep.por_id()["curiosidade-01"]
        pet._votar(i, True)
        pet._votar(rep.por_id()["piada-02"], False)
        self.assertGreater(pet.cerebro.valor("curiosidade-01"), 0)
        self.assertLess(pet.cerebro.valor("piada-02"), 0)


class TestTravessuras(Base):
    def test_arrasta_o_cursor(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet._limpar()
        posicoes = []
        with mock.patch("alarma.pet.QCursor.setPos", side_effect=lambda x, y: posicoes.append((x, y))):
            pet._enfileirar(Passo("arrastar", 1.0, "puxando"))
            self.rodar(pet, 1.2)
        self.assertGreater(len(posicoes), 10)
        self.assertNotEqual(posicoes[0], posicoes[-1])

    def test_traz_um_queijo_e_larga_na_tela(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet._limpar()
        pet._executar(rep.por_id()["trazer-meia"])
        self.rodar(pet, 40, 0.1)
        self.assertEqual([o.nome for o in pet._objetos], ["meia"])
        objeto = pet._objetos[0]
        pet._objeto_clicado(objeto)
        self.assertEqual(pet._objetos, [])

    def test_desligar_fecha_todas_as_janelas(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet._largar("moeda")
        pet._limpar()
        pet._enfileirar(Passo("placa", texto="oi", titulo="t"))
        self.rodar(pet, 0.2)
        self.assertIsNotNone(pet._placa)
        pet.desligar()
        self.assertEqual((pet._janela, pet._placa, pet._objetos), (None, None, []))
        pet._quadro()
        pet.tapa()

    def test_fechar_aba_avisa_quando_deu_certo(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet._limpar()
        pet._depois_da_acao("fechar-aba", True)
        self.rodar(pet, 0.1)
        self.assertIn("aba", pet._passo.texto)

    def test_sem_permissao_nunca_apronta(self) -> None:
        pet = self.pet(travessura=100, permissoes=())
        pet.aparecer()
        pet._limpar()
        for _ in range(60):
            pet._fila.clear()
            pet._proxima()
            self.assertFalse(pet._atual is not None and pet._atual.tipo == rep.TRAVESSURA)


class TestSono(Base):
    def test_dormir_e_acordar(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet.dormir(config.SEMPRE)
        self.assertEqual(pet.estado, Pet.DORMINDO)
        self.assertTrue(config.carregar(config.caminho_padrao()).dormindo(datetime.now()))
        self.rodar(pet, 30, 0.1)
        self.assertEqual(pet._anim, "cochilando")
        self.relogio.t += 100_000
        pet._decidir()
        self.assertEqual(pet.estado, Pet.DORMINDO)
        pet.acordar()
        self.assertEqual(pet.estado, Pet.ATIVO)
        self.assertEqual(config.carregar(config.caminho_padrao()).dormir_ate, "")

    def test_dormindo_escondido_nao_aparece(self) -> None:
        pet = self.pet(dormir_visivel=False, dormir_ate=config.SEMPRE)
        self.relogio.t += 100_000
        pet._decidir()
        self.assertEqual(pet.estado, Pet.AUSENTE)
        self.assertFalse(pet._janela.isVisible())


class TestPainelDoPet(Base):
    def test_salva_os_controles_do_pet(self) -> None:
        pet = self.pet()
        painel = Painel(pet)
        self.addCleanup(Shiboken.delete, painel)
        painel.abrir()
        painel._intensidade.setValue(80)
        painel._travessura.setValue(10)
        painel._permissoes[rep.P_CURSOR].setChecked(False)
        painel._falas[rep.NOTICIAS].setChecked(False)
        painel._cidade.setText("Salvador")
        painel.salvar()
        salvo = config.carregar(config.caminho_padrao())
        self.assertEqual((salvo.intensidade, salvo.travessura, salvo.cidade), (80, 10, "Salvador"))
        self.assertNotIn(rep.P_CURSOR, salvo.permissoes)
        self.assertNotIn(rep.NOTICIAS, salvo.falas)
        self.assertEqual(pet.cfg, salvo)

    def test_ensinar_frase_e_dormir_pelo_painel(self) -> None:
        pet = self.pet()
        painel = Painel(pet)
        self.addCleanup(Shiboken.delete, painel)
        painel.abrir()
        painel._frase.setText("bora que dá")
        painel._ensinar()
        self.assertIn("bora que dá", pet.cerebro.frases)
        painel._duracao.setCurrentIndex(0)
        painel._por_para_dormir()
        self.assertTrue(pet.resumo().startswith("Dormindo até"))
        painel._acordar_rato()
        self.assertFalse(pet.resumo().startswith("Dormindo"))


if __name__ == "__main__":
    unittest.main()


class TestNovidades(Base):
    def test_bolinha_diverte(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet.nec.diversao = 10
        pet.brincar_bolinha()
        self.assertIsNotNone(pet._bola)
        self.rodar(pet, 40, 0.05)
        self.assertIsNone(pet._bola)
        self.assertGreater(pet.nec.diversao, 30)

    def test_pegar_no_colo_e_soltar(self) -> None:
        from PySide6.QtCore import QPoint

        pet = self.pet()
        pet.aparecer()
        pet._pegar(QPoint(800, 400))
        self.rodar(pet, 0.2)
        self.assertEqual(pet._anim, "pendurado")
        pet._arrastar(QPoint(900, 300))
        from alarma.pet import CANGOTE

        gx, gy = pet._ponto(CANGOTE)
        self.assertLess(abs(gx - 900) + abs(gy - 300), 4)
        pet.tapa()  # no colo, clique não vale como tapa
        self.assertEqual(pet.nec.tapas, 0)
        pet._soltar(QPoint(900, 300))
        self.rodar(pet, 3)
        self.assertNotEqual(pet._anim, "pendurado")
        self.assertTrue(pet.mapa.valido((pet.x, pet.y)))

    def test_anda_entre_duas_telas_sem_sair(self) -> None:
        pet = self.pet()
        pet._tela.telas = lambda: [(0, 200, 1440, 1100), (1440, 0, 3360, 1080)]
        pet._atualizar_mapa()
        pet.aparecer()
        pet._limpar()
        pet.x, pet.y = 100, 880
        pet._enfileirar(Passo("andar", destino=(3000, 50), anim="andando", vel=400))
        posicoes = []
        for _ in range(400):
            self.relogio.t += 0.05
            pet._quadro()
            posicoes.append((pet.x, pet.y))
        self.assertTrue(all(pet.mapa.valido(p) for p in posicoes))
        self.assertEqual(pet.mapa.indice((pet.x, pet.y)), 1)

    def test_morre_de_fome_e_deixa_lapide(self) -> None:
        pet = self.pet()
        pet.aparecer()
        pet.nec.barriga = 0
        pet.nec.vida = 0.5
        pet.nec.atualizado = 1_700_000_000 + self.relogio.t - 600
        pet._cuidar()
        self.assertEqual(pet.estado, Pet.MORTO)
        self.rodar(pet, 8, 0.1)
        self.assertIn("lapide", [o.nome for o in pet._objetos])
        self.assertFalse(pet._janela.isVisible())
        self.relogio.t += 10_000
        pet._decidir()
        self.assertEqual(pet.estado, Pet.MORTO)
        self.assertIn("morreu de fome", pet.resumo())
        pet.adotar()
        self.assertEqual(pet.estado, Pet.ATIVO)
        self.assertFalse(pet.nec.morto)

    def test_sem_morte_no_painel_nao_morre(self) -> None:
        pet = self.pet(pode_morrer=False)
        pet.nec.barriga = 0
        pet.nec.vida = 0.5
        pet.nec.atualizado = 1_700_000_000 + self.relogio.t - 600
        pet._cuidar()
        self.assertNotEqual(pet.estado, Pet.MORTO)

    def test_lembrete_acorda_e_mostra_placa(self) -> None:
        from datetime import time as hora

        from alarma.lembretes import Lembrete

        pet = self.pet()
        avisos = []
        pet.aviso.connect(lambda t, x: avisos.append((t, x)))
        pet.dormir(config.SEMPRE)
        with mock.patch("alarma.som.tocar"):
            pet.tocar_lembrete(Lembrete("x", hora(10), "mensagem", "Ligar pro banco"))
        self.rodar(pet, 1.5)
        self.assertEqual(pet._passo.tipo, "placa")
        self.assertEqual(pet._passo.texto, "Ligar pro banco")
        self.assertTrue(avisos)

    def test_vestir_troca_os_sprites(self) -> None:
        from alarma import aparencia

        pet = self.pet()
        antes = pet._anims["sentado"].direita[0].toImage()
        pet.vestir(aparencia.Aparencia(nome="Bigode", pelo="azul", chapeu="cartola"))
        depois = pet._anims["sentado"].direita[0].toImage()
        self.assertNotEqual(antes, depois)
        self.assertEqual(aparencia.carregar().nome, "Bigode")

    def test_personalidade_preguicosa_cochila_mais(self) -> None:
        import random as aleatorio

        from alarma import comportamento as comp
        from alarma.cerebro import Cerebro

        cfg = config.Config(travessura=0)
        ops = comp.elegiveis(rep.todas(), cfg, Cerebro(), lambda f: True, lambda p: True)
        def conta(jeito):
            acaso = aleatorio.Random(4)
            return sum(comp.planejar(ops, cfg, Cerebro(), acaso, jeito).interacao.id in ("cochilar", "espreguicar") for _ in range(800))
        self.assertGreater(conta("preguicoso"), conta("curioso") * 2)
