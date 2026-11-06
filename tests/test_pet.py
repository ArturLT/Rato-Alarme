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
        for _ in range(5):
            pet.dar_queijo()
        self.assertGreaterEqual(pet.cerebro.nivel, 2)
        self.assertIn("segredo-0", pet.cerebro.desbloqueadas)

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
        pet._executar(rep.por_id()["trazer-queijo"])
        self.rodar(pet, 40, 0.1)
        self.assertEqual([o.nome for o in pet._objetos], ["queijo"])
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
