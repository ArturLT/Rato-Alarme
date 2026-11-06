import tempfile
import unittest
from pathlib import Path

from alarma.registro import Registro


class TestRegistro(unittest.TestCase):
    def test_sobrevive_a_reinicio(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "sub" / "registro.json"
            Registro(caminho).marcar("2026-11-06", "manha", "pego")
            novo = Registro(caminho)
            self.assertTrue(novo.tem("2026-11-06", "manha", "pego"))
            self.assertFalse(novo.tem("2026-11-06", "tarde", "pego"))
            self.assertFalse(novo.tem("2026-11-07", "manha", "pego"))

    def test_arquivo_corrompido_nao_derruba(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "registro.json"
            caminho.write_text("{quebrado", encoding="utf-8")
            self.assertFalse(Registro(caminho).tem("2026-11-06", "manha", "pego"))

    def test_sem_caminho_fica_na_memoria(self) -> None:
        registro = Registro(None)
        registro.marcar("2026-11-06", "manha", "pego")
        self.assertTrue(registro.tem("2026-11-06", "manha", "pego"))

    def test_limpar_apaga_so_aquele_alarme_e_persiste(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "registro.json"
            registro = Registro(caminho)
            registro.marcar("2026-11-06", "manha", "pego")
            registro.marcar("2026-11-06", "tarde", "pego")
            registro.limpar("2026-11-06", "tarde")
            novo = Registro(caminho)
            self.assertFalse(novo.tem("2026-11-06", "tarde", "pego"))
            self.assertTrue(novo.tem("2026-11-06", "manha", "pego"))


if __name__ == "__main__":
    unittest.main()
