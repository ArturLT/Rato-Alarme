#!/bin/bash
# Gera o Rato-Alarme.app e o DMG no próprio Mac, igual ao que o GitHub faz ao lançar versão.
#   bash empacotar/gerar-dmg-mac.sh
# O resultado fica em dist/: Rato-Alarme.app e Rato-Alarme-macOS-<chip>.dmg
set -eu

if [ "$(uname)" != "Darwin" ]; then
    echo "Este script só funciona no macOS." >&2
    exit 1
fi

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"

# Precisa de Python 3.10 ou mais novo. O python3 que vem com o Mac costuma ser 3.9.
PYTHON=""
for candidato in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$candidato" >/dev/null && "$candidato" -c 'import sys; sys.exit(sys.version_info < (3, 10))' 2>/dev/null; then
        PYTHON="$candidato"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "Falta o Python 3.10 ou mais novo. Instale em https://www.python.org/downloads/macos/ e rode de novo." >&2
    exit 1
fi
echo "Usando $("$PYTHON" --version)"

# Tudo fica num ambiente separado, em .venv-empacotar, sem mexer no Python do sistema.
"$PYTHON" -m venv .venv-empacotar
VENV_PY="$RAIZ/.venv-empacotar/bin/python"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r requirements-empacotar.txt

echo "Rodando os testes..."
QT_QPA_PLATFORM=offscreen "$VENV_PY" -m unittest discover -s tests

echo "Montando o app..."
rm -rf build dist
"$VENV_PY" -m PyInstaller --noconfirm empacotar/rato-alarme.spec
QT_QPA_PLATFORM=offscreen dist/Rato-Alarme.app/Contents/MacOS/Rato-Alarme --verificar

if [ "$(uname -m)" = "arm64" ]; then CHIP="AppleSilicon"; else CHIP="Intel"; fi
DMG="dist/Rato-Alarme-macOS-$CHIP.dmg"
PASTA_DMG="$(mktemp -d)"
cp -R dist/Rato-Alarme.app "$PASTA_DMG/"
ln -s /Applications "$PASTA_DMG/Applications"
hdiutil create -volname Rato-Alarme -srcfolder "$PASTA_DMG" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$PASTA_DMG"

echo
echo "Pronto: $RAIZ/$DMG"
open -R "$DMG"
