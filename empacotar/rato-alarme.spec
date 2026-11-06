# Gera o app do Windows e do Mac: pyinstaller empacotar/rato-alarme.spec
import re
import sys
from pathlib import Path

RAIZ = Path(SPECPATH).parent
VERSAO = re.search(r'VERSAO = "(.+)"', (RAIZ / "alarma/versao.py").read_text(encoding="utf-8"))[1]
ICONE = str(RAIZ / "alarma/icones/rato-alarme.png")

a = Analysis(
    [str(RAIZ / "rato_alarme.py")],
    pathex=[str(RAIZ)],
    datas=[
        (str(RAIZ / "alarma/folhas"), "alarma/folhas"),
        (str(RAIZ / "alarma/icones"), "alarma/icones"),
    ],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Rato-Alarme",
    console=False,
    icon=ICONE,
)
coleta = COLLECT(exe, a.binaries, a.datas, name="Rato-Alarme")

if sys.platform == "darwin":
    app = BUNDLE(
        coleta,
        name="Rato-Alarme.app",
        icon=ICONE,
        bundle_identifier="meme.alarma",
        version=VERSAO,
        info_plist={"LSUIElement": True, "CFBundleShortVersionString": VERSAO},
    )
