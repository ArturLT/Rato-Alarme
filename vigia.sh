#!/bin/sh
# Sobe a criatura com a sessão e traz ela de volta se o processo morrer.
cd "/home/artur/Área de trabalho/off-code/alarma_meme" || exit 1

LOCK="${XDG_RUNTIME_DIR:-/tmp}/alarma-meme.lock"
exec 9>"$LOCK"
flock -n 9 || exit 0

while true; do
    /usr/bin/python3 -m alarma
    sleep 1
done
