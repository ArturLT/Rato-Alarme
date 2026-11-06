import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alarma import instalacao

HDIUTIL = """#!/bin/sh
echo "hdiutil $1" >> "$REGISTRO"
[ "$1" = detach ] && exit 0
[ -n "$FALHAR_MONTAGEM" ] && exit 1
while [ "$1" != -mountpoint ]; do shift; done
mkdir "$2/Rato-Alarme.app"
echo nova > "$2/Rato-Alarme.app/versao"
"""
DITTO = """#!/bin/sh
[ -n "$FALHAR_COPIA" ] && exit 1
cp -R "$1" "$2"
"""
OPEN = """#!/bin/sh
echo "open $1" >> "$REGISTRO"
"""


@unittest.skipUnless(os.name == "posix", "script do Mac")
class TestScriptMac(unittest.TestCase):
    def setUp(self) -> None:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.raiz = Path(pasta.name)
        self.app = self.raiz / "Applications/Rato-Alarme.app"
        self.app.mkdir(parents=True)
        (self.app / "versao").write_text("velha\n")
        self.registro = self.raiz / "registro"
        falsos = self.raiz / "falsos"
        falsos.mkdir()
        for nome, script in (("hdiutil", HDIUTIL), ("ditto", DITTO), ("open", OPEN)):
            caminho = falsos / nome
            caminho.write_text(script)
            caminho.chmod(caminho.stat().st_mode | stat.S_IEXEC)
        self.ambiente = {
            **os.environ,
            "PATH": f"{falsos}:{os.environ['PATH']}",
            "REGISTRO": str(self.registro),
        }

    def _rodar(self, **extra: str) -> None:
        morto = subprocess.Popen(["true"])
        morto.wait()
        subprocess.run(
            ["/bin/sh", "-c", instalacao.SCRIPT_MAC, "sh", "x.dmg", str(self.app), str(morto.pid)],
            env={**self.ambiente, **extra},
            check=True,
        )

    def _pasta_limpa(self) -> None:
        self.assertEqual([p.name for p in self.app.parent.iterdir()], ["Rato-Alarme.app"])

    def test_troca_o_app_desmonta_e_reabre(self) -> None:
        self._rodar()
        self.assertEqual((self.app / "versao").read_text(), "nova\n")
        self._pasta_limpa()
        self.assertEqual(
            self.registro.read_text().splitlines(),
            ["hdiutil attach", "hdiutil detach", f"open {self.app}"],
        )

    def test_falha_mantem_o_app_antigo_e_reabre(self) -> None:
        for falha in ("FALHAR_MONTAGEM", "FALHAR_COPIA"):
            self._rodar(**{falha: "1"})
            self.assertEqual((self.app / "versao").read_text(), "velha\n", falha)
            self._pasta_limpa()
            self.assertEqual(self.registro.read_text().splitlines()[-1], f"open {self.app}")


class TestSabeInstalar(unittest.TestCase):
    def test_codigo_fonte_nunca_instala(self) -> None:
        for sistema in ("win32", "darwin", "linux"):
            with mock.patch("sys.platform", sistema):
                self.assertFalse(instalacao.sabe_instalar())

    def test_app_empacotado_no_windows_instala(self) -> None:
        with mock.patch("sys.platform", "win32"), mock.patch("sys.frozen", True, create=True):
            self.assertTrue(instalacao.sabe_instalar())

    def test_mac_exige_pacote_em_pasta_gravavel(self) -> None:
        executavel = "/Applications/Rato-Alarme.app/Contents/MacOS/Rato-Alarme"
        with mock.patch("os.access", return_value=True):
            self.assertEqual(
                instalacao.app_do_mac(executavel), Path("/Applications/Rato-Alarme.app")
            )
            self.assertIsNone(instalacao.app_do_mac("/usr/local/bin/rato"))
        with mock.patch("os.access", return_value=False):
            self.assertIsNone(instalacao.app_do_mac(executavel))
