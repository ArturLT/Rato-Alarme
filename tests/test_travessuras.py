import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alarma import travessuras
from alarma.travessuras import MAX_JANELAS, comando_fechar, comandos_janelas


def cliente(endereco: str, pid: int = 1, ws: int = 1, **extra: object) -> dict:
    return {"address": endereco, "pid": pid, "workspace": {"id": ws}, **extra}


class TestTravessuras(unittest.TestCase):
    def test_abre_o_video_do_queijo(self) -> None:
        with mock.patch("webbrowser.open") as abrir:
            travessuras.abrir_youtube()
        abrir.assert_called_once_with("https://www.youtube.com/watch?v=WRlCEiGFEFM")

    def _marca(self) -> Path:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        return Path(pasta.name) / "estado" / "mudo-do-rato"

    def _mudar_som(self, marca: Path, ja_mudo: bool) -> list[bool]:
        """Muta e restaura, e retorna o que foi pedido ao sistema."""
        with (
            mock.patch("alarma.sistema.esta_mudo", return_value=ja_mudo),
            mock.patch("alarma.sistema.definir_mudo") as definir,
        ):
            travessuras.mutar(marca)
            travessuras.restaurar_som(marca)
        return [chamada.args[0] for chamada in definir.call_args_list]

    def test_som_volta_depois_do_mudo_do_rato(self) -> None:
        marca = self._marca()
        self.assertEqual(self._mudar_som(marca, ja_mudo=False), [True, False])
        self.assertFalse(marca.exists())

    def test_mudo_da_pessoa_continua_mudo(self) -> None:
        self.assertEqual(self._mudar_som(self._marca(), ja_mudo=True), [True])

    def test_rato_mutando_de_novo_ainda_restaura(self) -> None:
        marca = self._marca()
        with mock.patch("alarma.sistema.definir_mudo"):
            with mock.patch("alarma.sistema.esta_mudo", return_value=False):
                travessuras.mutar(marca)
            with mock.patch("alarma.sistema.esta_mudo", return_value=True):
                travessuras.mutar(marca)
        self.assertTrue(marca.exists())

    def test_sem_marca_nao_mexe_no_som(self) -> None:
        with mock.patch("alarma.sistema.definir_mudo") as definir:
            travessuras.restaurar_som(self._marca())
        definir.assert_not_called()

    def test_sem_como_marcar_nao_muta(self) -> None:
        with (
            mock.patch("alarma.sistema.esta_mudo", return_value=False),
            mock.patch("pathlib.Path.touch", side_effect=OSError),
            mock.patch("alarma.sistema.definir_mudo") as definir,
        ):
            travessuras.mutar(self._marca())
        definir.assert_not_called()

    def test_fecha_uma_janela_so(self) -> None:
        clientes = [cliente(f"0x{i}") for i in range(4)]
        comando = comando_fechar(clientes, 1, 99, random.Random(1))
        self.assertRegex(comando, r"^hl\.dsp\.window\.close\(\{ window = 'address:0x\d' \}\)$")

    def test_fechar_poupa_propria_outro_workspace_e_tela_cheia(self) -> None:
        clientes = [
            cliente("0xa", pid=99),
            cliente("0xb", ws=2),
            cliente("0xc", fullscreen=1),
        ]
        self.assertIsNone(comando_fechar(clientes, 1, 99, random.Random(1)))

    def test_mexer_janelas_nao_fecha(self) -> None:
        clientes = [cliente(f"0x{i}", floating=i % 2 == 0) for i in range(6)]
        comandos = comandos_janelas(clientes, 1, 99, random.Random(1))
        self.assertEqual(len(comandos), MAX_JANELAS)
        for comando in comandos:
            self.assertIn("hl.dsp.window.move(", comando)
            self.assertNotIn("close", comando)

    def test_ignora_propria_outro_workspace_e_tela_cheia(self) -> None:
        clientes = [
            cliente("0xa", pid=99),
            cliente("0xb", ws=2),
            cliente("0xc", fullscreen=1),
        ]
        self.assertEqual(comandos_janelas(clientes, 1, 99, random.Random(1)), [])


if __name__ == "__main__":
    unittest.main()
