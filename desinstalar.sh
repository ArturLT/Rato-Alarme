#!/bin/bash
# Remove serviços e atalho. Mantém a configuração e esta pasta.
set -eu

cd "$(dirname "$0")"
UNIDADES="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
ATALHOS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SERVICOS="alarma-meme.service alarma-meme-bandeja.service"

systemctl --user disable --now $SERVICOS || true
/usr/bin/python3 -c "
from alarma import travessuras
from alarma.registro import caminho_mudo
travessuras.restaurar_som(caminho_mudo())"
rm -f "$UNIDADES/alarma-meme.service" "$UNIDADES/alarma-meme-bandeja.service"
rm -f "$ATALHOS/rato-alarme.desktop"
systemctl --user daemon-reload
echo "Rato-Alarme removido."
