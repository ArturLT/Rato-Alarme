"""Sobe a interface de verdade sem tela, no plugin offscreen do Qt."""

import os
import tempfile
import unittest
from datetime import time
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from alarma import atualizacao, config, sprites
from alarma.animacao import NOMES
from alarma.bandeja import Bandeja
from alarma.caca import CLIQUES, FECHAR, JANELAS, LADO_RATO, Fase
from alarma.criatura import Criatura
from alarma.janela import JanelaHyprland, JanelaQt, nova
from alarma.logica import Alarme, Decisao
from alarma.painel import Painel
from alarma.registro import PEGO
from alarma.unico import Instancia

app = QApplication.instance() or QApplication([])


class Base(unittest.TestCase):
    def setUp(self) -> None:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.pasta = Path(pasta.name)
        ambiente = mock.patch.dict(
            "os.environ",
            {"XDG_CONFIG_HOME": pasta.name, "XDG_STATE_HOME": pasta.name},
        )
        ambiente.start()
        self.addCleanup(ambiente.stop)


class TestSprites(Base):
    def test_carrega_todas_as_folhas_no_tamanho_do_rato(self) -> None:
        animacoes = sprites.carregar(LADO_RATO)
        self.assertEqual(set(animacoes), set(NOMES))
        for animacao in animacoes.values():
            self.assertEqual(len(animacao.direita), animacao.clipe.quadros)
            for quadro in animacao.direita + animacao.esquerda:
                self.assertEqual((quadro.width(), quadro.height()), (LADO_RATO, LADO_RATO))

    def test_esquerda_e_o_espelho_da_direita_e_o_fundo_e_transparente(self) -> None:
        animacao = sprites.carregar(LADO_RATO)["fuga"]
        direita = animacao.direita[0].toImage()
        esquerda = animacao.esquerda[0].toImage()
        self.assertEqual(direita.pixelColor(0, 0).alpha(), 0)
        for x, y in ((40, 100), (98, 98), (150, 120)):
            self.assertEqual(direita.pixel(x, y), esquerda.pixel(LADO_RATO - 1 - x, y))


class TestPainel(Base):
    def _painel(self) -> Painel:
        painel = Painel()
        self.addCleanup(painel.close)
        painel.abrir()
        return painel

    def test_mostra_e_grava_os_horarios(self) -> None:
        painel = self._painel()
        painel._entrada.setTime(QTime(8, 15))
        painel._saida.setTime(QTime(17, 45))
        painel._alarme.setChecked(False)
        painel.salvar()
        salvo = config.carregar(config.caminho_padrao())
        self.assertEqual((salvo.entrada, salvo.saida), (time(8, 15), time(17, 45)))
        self.assertFalse(salvo.alarme_ligado)
        self.assertEqual(painel._aviso.text(), "Salvo.")

    def test_recusa_horarios_invertidos(self) -> None:
        painel = self._painel()
        painel._entrada.setTime(QTime(18, 0))
        painel._saida.setTime(QTime(8, 0))
        painel.salvar()
        self.assertFalse(config.caminho_padrao().exists())
        self.assertIn("antes da saída", painel._aviso.text())

    def test_sem_hyprland_mantem_a_preferencia_de_fechar_janelas(self) -> None:
        config.salvar(config.caminho_padrao(), config.Config(fechar_janela=False))
        with mock.patch("alarma.sistema.mexe_em_outras_janelas", return_value=False):
            painel = self._painel()
        painel.salvar()
        self.assertFalse(config.carregar(config.caminho_padrao()).fechar_janela)


class TestCriatura(Base):
    def _criatura(self, solto: bool) -> Criatura:
        hyprland = mock.patch("alarma.sistema.tem_hyprland", return_value=False)
        hyprland.start()
        self.addCleanup(hyprland.stop)
        for alvo in ("alarma.criatura.tocar", "alarma.travessuras.restaurar_som"):
            trava = mock.patch(alvo)
            trava.start()
            self.addCleanup(trava.stop)
        with mock.patch.object(
            Criatura,
            "_decidir",
            return_value=Decisao(Alarme.MANHA if solto else Alarme.NENHUM, solto, _agora()),
        ):
            criatura = Criatura(demo=True)
            criatura._demo = False
            criatura.iniciar()
        self.addCleanup(self._parar, criatura)
        return criatura

    def _parar(self, criatura: Criatura) -> None:
        for relogio in criatura._relogios:
            relogio.stop()
        criatura._janela.hide()

    def test_fora_do_horario_o_rato_fica_escondido(self) -> None:
        criatura = self._criatura(solto=False)
        self.assertFalse(criatura._janela.isVisible())

    def test_no_horario_aparece_e_desenha(self) -> None:
        criatura = self._criatura(solto=True)
        self.assertTrue(criatura._janela.isVisible())
        self.assertIsInstance(criatura._janela.pixmap(), QPixmap)
        self.assertFalse(criatura._janela.pixmap().isNull())

    def test_tres_cliques_pegam_o_rato(self) -> None:
        criatura = self._criatura(solto=True)
        criatura._caca.fase = Fase.SOLTO
        for _ in range(CLIQUES):
            criatura._clicado()
        self.assertIsNone(criatura._caca)

    def test_clique_de_verdade_na_janela_conta(self) -> None:
        criatura = self._criatura(solto=True)
        criatura._caca.fase = Fase.SOLTO
        QTest.mouseClick(criatura._janela, Qt.MouseButton.LeftButton)
        self.assertEqual(criatura._caca.cliques, 1)

    def _no_relogio(self, criatura: Criatura, alarme: str, no_horario: bool) -> None:
        with mock.patch.object(
            Criatura, "_decidir", return_value=Decisao(alarme, no_horario, _agora())
        ):
            criatura._sincronizar()

    def test_cacada_da_manha_atravessa_a_saida_ate_ser_pega(self) -> None:
        criatura = self._criatura(solto=True)
        caca = criatura._caca
        self._no_relogio(criatura, Alarme.TARDE, True)
        self._no_relogio(criatura, Alarme.TARDE, False)
        self.assertIs(criatura._caca, caca)
        self.assertTrue(criatura._janela.isVisible())

    def _muda_saida(self, antes: time, depois: time) -> Criatura:
        """Às 09:00, com o rato da tarde já pego, troca a saída."""
        criatura = self._criatura(solto=False)
        criatura._config = config.Config(entrada=time(6, 0), saida=antes)
        criatura._registro.marcar(_agora().date().isoformat(), Alarme.TARDE, PEGO)
        novo = config.Config(entrada=time(6, 0), saida=depois)
        with mock.patch.object(Criatura, "_ler_config", return_value=novo):
            self._no_relogio(criatura, Alarme.MANHA, True)
        return criatura

    def _tarde_pega(self, criatura: Criatura) -> bool:
        return criatura._registro.tem(_agora().date().isoformat(), Alarme.TARDE, PEGO)

    def test_saida_adiada_reabre_o_alarme_da_tarde(self) -> None:
        self.assertFalse(self._tarde_pega(self._muda_saida(time(8, 30), time(12, 0))))

    def test_horario_ja_passado_nao_reabre(self) -> None:
        self.assertTrue(self._tarde_pega(self._muda_saida(time(8, 30), time(8, 45))))

    def test_sem_mudanca_de_horario_nao_reabre(self) -> None:
        self.assertTrue(self._tarde_pega(self._muda_saida(time(12, 0), time(12, 0))))

    def test_sem_hyprland_nao_mexe_em_janelas_alheias(self) -> None:
        criatura = self._criatura(solto=False)
        self.assertEqual(criatura._proibidas(), (FECHAR, JANELAS))


def _agora():
    from datetime import datetime

    return datetime(2026, 1, 5, 9, 0).astimezone()


class TestJanela(Base):
    def test_escolhe_pelo_ambiente(self) -> None:
        from PySide6.QtWidgets import QWidget

        widget = QWidget()
        with mock.patch.dict("os.environ", {"HYPRLAND_INSTANCE_SIGNATURE": "x"}):
            self.assertIsInstance(nova(widget), JanelaHyprland)
        with mock.patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "Hyprland"}):
            os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
            self.assertIsInstance(nova(widget), JanelaHyprland)
        with mock.patch.dict("os.environ", {"XDG_CURRENT_DESKTOP": "KDE"}):
            os.environ.pop("HYPRLAND_INSTANCE_SIGNATURE", None)
            self.assertIsInstance(nova(widget), JanelaQt)

    def test_qt_le_a_area_e_move(self) -> None:
        from PySide6.QtWidgets import QWidget

        widget = QWidget()
        janela = JanelaQt(widget)
        x0, y0, x1, y1 = janela.area(janela.cursor())
        self.assertLess(x0, x1)
        self.assertLess(y0, y1)
        janela.mover(30, 40)
        self.assertEqual((widget.x(), widget.y()), (30, 40))


class TestInstanciaUnica(Base):
    def _primeira(self) -> list[int]:
        self.primeira = Instancia(self.pasta)
        self.assertTrue(self.primeira.assumir(avisar=True))
        self.addCleanup(self._soltar)
        pedidos: list[int] = []
        self.primeira.pedido.connect(lambda: pedidos.append(1))
        return pedidos

    def _soltar(self) -> None:
        self.primeira._relogio.stop()
        self.primeira._trava.unlock()

    def test_segunda_abertura_pede_o_painel_a_primeira(self) -> None:
        pedidos = self._primeira()
        self.assertFalse(Instancia(self.pasta).assumir(avisar=True))
        for _ in range(150):
            QTest.qWait(20)
            if pedidos:
                break
        self.assertEqual(pedidos, [1])

    def test_boot_repetido_nao_abre_o_painel(self) -> None:
        pedidos = self._primeira()
        self.assertFalse(Instancia(self.pasta).assumir(avisar=False))
        QTest.qWait(500)
        self.assertEqual(pedidos, [])

    def test_pedido_antigo_nao_abre_o_painel_no_proximo_boot(self) -> None:
        (self.pasta / "abrir-painel").touch()
        pedidos = self._primeira()
        QTest.qWait(500)
        self.assertEqual(pedidos, [])


class TestBandeja(Base):
    def _bandeja(self) -> Bandeja:
        self.bandeja = Bandeja(mock.Mock())
        self.addCleanup(self._parar)
        return self.bandeja

    def _parar(self) -> None:
        self.bandeja._icone.hide()
        self.bandeja._relogio.stop()
        self.bandeja._busca.stop()

    def _lancamento(self, download: str | None = "https://d/i.exe") -> atualizacao.Lancamento:
        return atualizacao.Lancamento("1.2.0", "https://p", download)

    def test_atualizar_so_aparece_com_versao_nova(self) -> None:
        bandeja = self._bandeja()
        self.assertFalse(bandeja._atualizar_app.isVisible())
        bandeja._mostrar_lancamento(self._lancamento())
        self.assertTrue(bandeja._atualizar_app.isVisible())
        self.assertIn("1.2.0", bandeja._atualizar_app.text())

    def test_sem_git_abre_o_instalador_no_navegador(self) -> None:
        bandeja = self._bandeja()
        bandeja._mostrar_lancamento(self._lancamento())
        with (
            mock.patch("alarma.bandeja.atualiza_sozinho", return_value=False),
            mock.patch("webbrowser.open") as abrir,
        ):
            bandeja._instalar()
        abrir.assert_called_once_with("https://d/i.exe")

    def test_sem_instalador_abre_a_pagina(self) -> None:
        bandeja = self._bandeja()
        bandeja._mostrar_lancamento(self._lancamento(download=None))
        with (
            mock.patch("alarma.bandeja.atualiza_sozinho", return_value=False),
            mock.patch("webbrowser.open") as abrir,
        ):
            bandeja._instalar()
        abrir.assert_called_once_with("https://p")

    def test_no_git_o_script_roda_fora_do_servico(self) -> None:
        bandeja = self._bandeja()
        bandeja._mostrar_lancamento(self._lancamento())
        with (
            mock.patch("alarma.bandeja.atualiza_sozinho", return_value=True),
            mock.patch("subprocess.Popen") as popen,
        ):
            bandeja._instalar()
        comando = popen.call_args.args[0]
        self.assertEqual(comando[:3], ["systemd-run", "--user", "--collect"])
        self.assertTrue(comando[3].endswith("atualizar.sh"))

    def test_sair_restaura_o_som_e_termina_com_zero(self) -> None:
        bandeja = self._bandeja()
        with (
            mock.patch("alarma.travessuras.restaurar_som") as restaurar,
            mock.patch("PySide6.QtWidgets.QApplication.exit") as sair,
        ):
            bandeja._sair()
        restaurar.assert_called_once()
        sair.assert_called_once_with(0)
