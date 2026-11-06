import subprocess
import unittest
from pathlib import Path
from unittest import mock

from alarma import caminhos, sistema


class TestComandos(unittest.TestCase):
    def _em(self, plataforma: str):
        trava = mock.patch("sys.platform", plataforma)
        trava.start()
        self.addCleanup(trava.stop)

    def _popen(self):
        trava = mock.patch("subprocess.Popen")
        popen = trava.start()
        self.addCleanup(trava.stop)
        return popen

    def test_linux_usa_pipewire(self) -> None:
        self._em("linux")
        popen = self._popen()
        sistema.tocar(Path("a.wav"))
        sistema.definir_mudo(True)
        sistema.definir_mudo(False)
        self.assertEqual(
            [c.args[0] for c in popen.call_args_list],
            [
                ("pw-play", "a.wav"),
                ("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1"),
                ("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "0"),
            ],
        )

    def test_mac_usa_afplay_e_osascript(self) -> None:
        self._em("darwin")
        popen = self._popen()
        sistema.tocar(Path("a.wav"))
        sistema.definir_mudo(True)
        self.assertEqual(
            [c.args[0] for c in popen.call_args_list],
            [("afplay", "a.wav"), ("osascript", "-e", "set volume output muted true")],
        )

    def _saida(self, texto: str):
        return mock.patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, stdout=texto),
        )

    def test_le_mudo_no_linux(self) -> None:
        self._em("linux")
        with self._saida("Volume: 0.40 [MUTED]\n"):
            self.assertTrue(sistema.esta_mudo())
        with self._saida("Volume: 0.40\n"):
            self.assertFalse(sistema.esta_mudo())

    def test_le_mudo_no_mac(self) -> None:
        self._em("darwin")
        with self._saida("true\n"):
            self.assertTrue(sistema.esta_mudo())
        with self._saida("false\n"):
            self.assertFalse(sistema.esta_mudo())

    def test_falha_no_windows_nao_derruba_o_alarme(self) -> None:
        self._em("win32")
        with mock.patch("alarma.sistema._volume_do_windows", side_effect=OSError):
            self.assertFalse(sistema.esta_mudo())
            sistema.definir_mudo(True)

    def test_programa_ausente_nao_derruba_o_alarme(self) -> None:
        self._em("linux")
        with mock.patch("subprocess.Popen", side_effect=FileNotFoundError):
            sistema.definir_mudo(True)
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            self.assertFalse(sistema.esta_mudo())


class TestCaminhos(unittest.TestCase):
    def _pastas(self, plataforma: str, ambiente: dict[str, str]) -> tuple[Path, Path]:
        with (
            mock.patch("sys.platform", plataforma),
            mock.patch.dict("os.environ", ambiente, clear=True),
            mock.patch("pathlib.Path.home", return_value=Path("/casa")),
        ):
            return caminhos.pasta_config(), caminhos.pasta_estado()

    def test_linux_mantem_as_pastas_de_sempre(self) -> None:
        self.assertEqual(
            self._pastas("linux", {}),
            (Path("/casa/.config/alarma-meme"), Path("/casa/.local/state/alarma-meme")),
        )

    def test_mac(self) -> None:
        pasta = Path("/casa/Library/Application Support/alarma-meme")
        self.assertEqual(self._pastas("darwin", {}), (pasta, pasta))

    def test_windows(self) -> None:
        pasta = Path("/roaming/alarma-meme")
        self.assertEqual(self._pastas("win32", {"APPDATA": "/roaming"}), (pasta, pasta))

    def test_xdg_vale_em_qualquer_sistema(self) -> None:
        ambiente = {"XDG_CONFIG_HOME": "/c", "XDG_STATE_HOME": "/e"}
        self.assertEqual(
            self._pastas("darwin", ambiente),
            (Path("/c/alarma-meme"), Path("/e/alarma-meme")),
        )
