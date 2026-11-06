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

from alarma import atualizacao, balao, config, falas, sprites
from alarma.animacao import FALANDO, NOMES
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


class TestBalao(Base):
    AREA = (0, 0, 1920, 1080)

    def _balao(self) -> balao.Balao:
        janela = balao.Balao()
        self.addCleanup(janela.close)
        return janela

    def test_fica_sobre_a_cabeca_e_a_ponta_acha_a_boca(self) -> None:
        onde = balao.lugar(800, 500, False, self.AREA)
        self.assertTrue(onde.acima)
        self.assertLess(onde.y, 500 + LADO_RATO)
        boca = 800 + round(LADO_RATO * balao.BOCA_X)
        self.assertEqual(onde.x + onde.ponta, boca)
        espelhado = balao.lugar(800, 500, True, self.AREA)
        self.assertEqual(espelhado.x + espelhado.ponta, 800 + LADO_RATO - round(LADO_RATO * balao.BOCA_X))

    def test_nunca_sai_da_tela(self) -> None:
        x0, y0, x1, y1 = self.AREA
        for rato_x in (x0, 900, x1 - LADO_RATO):
            for rato_y in (y0, 500, y1 - LADO_RATO):
                for esquerda in (False, True):
                    onde = balao.lugar(rato_x, rato_y, esquerda, self.AREA)
                    self.assertGreaterEqual(onde.x, x0)
                    self.assertLessEqual(onde.x + balao.LARGURA, x1)
                    self.assertGreaterEqual(onde.y, y0)
                    self.assertLessEqual(onde.y + balao.ALTURA, y1)

    def test_sem_espaco_em_cima_vai_para_baixo_do_rato(self) -> None:
        onde = balao.lugar(800, 0, False, self.AREA)
        self.assertFalse(onde.acima)
        self.assertGreaterEqual(onde.y, LADO_RATO)

    def test_toda_frase_cabe_na_caixa_mesmo_com_o_maior_atraso(self) -> None:
        janela = self._balao()
        medidas = janela.fontMetrics()
        largura = balao.LARGURA - 2 * balao.RESPIRO
        frases = list(falas.COMPUTADOR)
        for alarme in (Alarme.MANHA, Alarme.TARDE):
            frases += falas.pontualidade(alarme, 11 * 60 + 59)
        cabem = (balao.ALTURA - balao.PONTA - 2 * balao.BORDA) // medidas.lineSpacing()
        for frase in frases:
            linhas = balao.quebrar(frase, medidas, largura)
            self.assertEqual(" ".join(linhas), frase)
            self.assertLessEqual(len(linhas), cabem, frase)
            for linha in linhas:
                self.assertLessEqual(medidas.horizontalAdvance(linha), largura, linha)

    def test_escreve_aos_poucos_e_nao_recebe_clique(self) -> None:
        janela = self._balao()
        self.assertTrue(janela.windowFlags() & Qt.WindowType.WindowTransparentForInput)
        self.assertFalse(janela.aberto)
        janela.dizer("oi rato", balao.lugar(800, 500, False, self.AREA))
        self.assertTrue(janela.aberto and janela.digitando)
        for _ in range(len("oi rato")):
            janela._escrever()
        self.assertFalse(janela.digitando)
        janela.calar()
        self.assertFalse(janela.aberto)

    def test_desenha_a_caixa_so_quando_ha_fala(self) -> None:
        janela = self._balao()
        janela.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        vazio = janela.grab().toImage()
        for acima_y in (500, 0):
            janela.dizer("reclamação", balao.lugar(800, acima_y, False, self.AREA))
            janela._letras = 5
            imagem = janela.grab().toImage()
            self.assertNotEqual(imagem, vazio)
            corpo = janela._corpo()
            self.assertEqual(imagem.pixelColor(corpo.right() - 8, corpo.center().y()), balao.CLARO)


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
        criatura._balao.calar()
        criatura._balao.hide()
        criatura._janela.hide()

    def test_fora_do_horario_o_rato_fica_escondido(self) -> None:
        criatura = self._criatura(solto=False)
        self.assertFalse(criatura._janela.isVisible())

    def test_no_horario_aparece_e_desenha(self) -> None:
        criatura = self._criatura(solto=True)
        self.assertTrue(criatura._janela.isVisible())
        self.assertIsInstance(criatura._janela.pixmap(), QPixmap)
        self.assertFalse(criatura._janela.pixmap().isNull())

    def _solto_e_pronto(self) -> Criatura:
        criatura = self._criatura(solto=True)
        criatura._caca.fase = Fase.SOLTO
        criatura._caca.x, criatura._caca.y = 800.0, 500.0
        return criatura

    def test_fala_para_o_rato_abre_o_balao_e_depois_fecha(self) -> None:
        criatura = self._solto_e_pronto()
        caca = criatura._caca
        inicio = caca._proxima_fala
        criatura._falar(inicio)
        self.assertTrue(criatura._balao.aberto)
        self.assertTrue(caca.falando(inicio))
        self.assertTrue(criatura._ultima_fala)
        criatura._falar(caca._fala_ate + 0.1)
        self.assertFalse(criatura._balao.aberto)

    def test_animacao_de_fala_mexe_a_boca_so_enquanto_escreve(self) -> None:
        criatura = self._solto_e_pronto()
        with mock.patch("alarma.criatura.time.monotonic", return_value=criatura._caca._proxima_fala + 0.15):
            criatura._falar(criatura._caca._proxima_fala)
            criatura._quadro()
            self.assertEqual(criatura._nome_atual, FALANDO)
            criatura._balao._relogio.stop()
            criatura._quadro()
        fechada = criatura._animacoes[FALANDO].direita[0].toImage()
        self.assertEqual(criatura._janela.pixmap().toImage(), fechada)

    def test_clique_cala_o_rato_e_conta_acerto(self) -> None:
        criatura = self._solto_e_pronto()
        caca = criatura._caca
        criatura._falar(caca._proxima_fala)
        criatura._clicado()
        self.assertFalse(criatura._balao.aberto)
        self.assertEqual(caca.cliques, 1)

    def test_pegar_o_rato_e_o_fim_do_alarme_calam_o_balao(self) -> None:
        criatura = self._solto_e_pronto()
        criatura._falar(criatura._caca._proxima_fala)
        criatura._encerrar()
        self.assertFalse(criatura._balao.aberto)

    def test_balao_some_junto_com_o_rato(self) -> None:
        criatura = self._criatura(solto=True)
        self.assertTrue(criatura._balao.isVisible())
        criatura._esconder()
        self.assertFalse(criatura._balao.isVisible())

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
        self.bandeja._aviso.hide()
        self.bandeja._icone.hide()
        self.bandeja._relogio.stop()
        self.bandeja._busca.stop()

    def _lancamento(self, download: str | None = "https://d/i.exe") -> atualizacao.Lancamento:
        return atualizacao.Lancamento("1.2.0", "https://p", download, "sha256:abc")

    def test_atualizar_so_aparece_com_versao_nova(self) -> None:
        bandeja = self._bandeja()
        self.assertFalse(bandeja._atualizar_app.isVisible())
        bandeja._mostrar_lancamento(self._lancamento())
        self.assertTrue(bandeja._atualizar_app.isVisible())
        self.assertIn("1.2.0", bandeja._atualizar_app.text())

    def test_versao_nova_abre_a_janela_uma_vez_so(self) -> None:
        bandeja = self._bandeja()
        bandeja._mostrar_lancamento(self._lancamento())
        self.assertTrue(bandeja._aviso.isVisible())
        self.assertIn("1.2.0", bandeja._aviso._titulo.text())
        bandeja._aviso._depois.click()
        self.assertFalse(bandeja._aviso.isVisible())
        bandeja._mostrar_lancamento(self._lancamento())
        self.assertFalse(bandeja._aviso.isVisible())

    def _instalar_sozinho(self, bandeja: Bandeja) -> None:
        bandeja._mostrar_lancamento(self._lancamento())
        with (
            mock.patch("alarma.bandeja.atualiza_sozinho", return_value=False),
            mock.patch("alarma.instalacao.sabe_instalar", return_value=True),
            mock.patch("threading.Thread") as linha,
        ):
            bandeja._aviso._agora.click()
            bandeja._aviso._agora.click()  # o segundo clique não pode baixar de novo
        linha.assert_called_once()
        self.assertTrue(bandeja._aviso._barra.isVisibleTo(bandeja._aviso))
        self.assertFalse(bandeja._aviso._agora.isVisibleTo(bandeja._aviso))

    def test_clique_baixa_instala_e_fecha_o_app(self) -> None:
        bandeja = self._bandeja()
        self._instalar_sozinho(bandeja)
        with (
            mock.patch("alarma.atualizacao.baixar") as baixar,
            mock.patch("alarma.instalacao.iniciar") as iniciar,
            mock.patch("alarma.travessuras.restaurar_som") as restaurar,
            mock.patch("PySide6.QtWidgets.QApplication.exit") as sair,
        ):
            bandeja._baixar(self._lancamento())
            app.processEvents()
        baixar.assert_called_once()
        destino = baixar.call_args.args[1]
        iniciar.assert_called_once_with(destino)
        restaurar.assert_called_once()
        sair.assert_called_once_with(0)

    def test_download_com_erro_deixa_tentar_de_novo_e_abrir_o_site(self) -> None:
        bandeja = self._bandeja()
        self._instalar_sozinho(bandeja)
        with (
            mock.patch("alarma.atualizacao.baixar", side_effect=ValueError),
            mock.patch("alarma.instalacao.iniciar") as iniciar,
        ):
            bandeja._baixar(self._lancamento())
            app.processEvents()
        iniciar.assert_not_called()
        self.assertEqual(bandeja._aviso._agora.text(), "Tentar de novo")
        self.assertTrue(bandeja._aviso._site.isVisibleTo(bandeja._aviso))
        with mock.patch("webbrowser.open") as abrir:
            bandeja._aviso._site.click()
        abrir.assert_called_once_with("https://d/i.exe")
        self._instalar_sozinho_de_novo(bandeja)

    def _instalar_sozinho_de_novo(self, bandeja: Bandeja) -> None:
        with (
            mock.patch("alarma.bandeja.atualiza_sozinho", return_value=False),
            mock.patch("alarma.instalacao.sabe_instalar", return_value=True),
            mock.patch("threading.Thread") as linha,
        ):
            bandeja._aviso._agora.click()
        linha.assert_called_once()

    def test_falha_ao_abrir_o_instalador_nao_fecha_o_app(self) -> None:
        bandeja = self._bandeja()
        self._instalar_sozinho(bandeja)
        with (
            mock.patch("alarma.instalacao.iniciar", side_effect=OSError),
            mock.patch("PySide6.QtWidgets.QApplication.exit") as sair,
        ):
            bandeja._trocar_app(self.pasta / "instalador.exe")
        sair.assert_not_called()
        self.assertEqual(bandeja._aviso._agora.text(), "Tentar de novo")

    def test_sem_resumo_vai_para_o_navegador(self) -> None:
        bandeja = self._bandeja()
        bandeja._mostrar_lancamento(atualizacao.Lancamento("1.2.0", "https://p", "https://d/i.exe"))
        with (
            mock.patch("alarma.bandeja.atualiza_sozinho", return_value=False),
            mock.patch("alarma.instalacao.sabe_instalar", return_value=True),
            mock.patch("webbrowser.open") as abrir,
        ):
            bandeja._instalar()
        abrir.assert_called_once_with("https://d/i.exe")

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
