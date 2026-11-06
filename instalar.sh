#!/bin/bash
# Instala o Rato-Alarme para o usuário atual, sem sudo.
# Use --sem-iniciar para só deixar pronto para o próximo boot.
set -eu

PASTA="$(cd "$(dirname "$0")" && pwd)"
UNIDADES="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
ATALHOS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
PYTHON="$PASTA/.venv/bin/python"

faltando=""
for comando in systemctl hyprctl wpctl pw-play python3; do
    command -v "$comando" >/dev/null || faltando="$faltando $comando"
done
if [ -n "$faltando" ]; then
    echo "Falta instalar:$faltando" >&2
    exit 1
fi

# As dependências ficam em .venv, sem tocar no Python do sistema.
[ -x "$PYTHON" ] || python3 -m venv "$PASTA/.venv"
"$PYTHON" -m pip install --quiet --disable-pip-version-check -r "$PASTA/requirements.txt"
"$PYTHON" -c "from PySide6 import QtWidgets"

# Versões antigas tinham um serviço só para a bandeja. Hoje é um processo só.
if [ -e "$UNIDADES/alarma-meme-bandeja.service" ]; then
    systemctl --user disable --now alarma-meme-bandeja.service || true
    rm -f "$UNIDADES/alarma-meme-bandeja.service"
fi

mkdir -p "$UNIDADES" "$ATALHOS"

cat >"$UNIDADES/alarma-meme.service" <<UNIDADE
[Unit]
Description=Rato-Alarme
PartOf=graphical-session.target
After=graphical-session.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=$PASTA
ExecStart="$PYTHON" -m alarma --boot
Restart=on-failure
RestartSec=1

[Install]
WantedBy=graphical-session.target
UNIDADE

cat >"$ATALHOS/rato-alarme.desktop" <<ATALHO
[Desktop Entry]
Type=Application
Name=Rato-Alarme
Comment=Liga o alarme e abre o painel de controle
Exec="$PASTA/abrir.sh"
Icon=$PASTA/alarma/icones/rato-alarme.png
Terminal=false
Categories=Utility;
ATALHO

chmod +x "$PASTA/abrir.sh"
systemctl --user daemon-reload
systemctl --user enable alarma-meme.service

if [ "${1:-}" = "--sem-iniciar" ]; then
    echo "Instalado. O Rato-Alarme começa no próximo boot."
else
    systemctl --user start alarma-meme.service
    echo "Instalado e ligado. Procure o rato na bandeja."
fi
