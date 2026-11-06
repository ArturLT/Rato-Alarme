#!/bin/bash
# Troca para a última versão publicada e reinicia o rato. A configuração continua igual.
# As chaves fazem o bash ler o script inteiro antes: o git troca este arquivo no meio.
{
set -eu
cd "$(dirname "$(readlink -f "$0")")"

if ! git diff --quiet HEAD -- ; then
    echo "Há mudanças locais nesta pasta. Guarde ou desfaça antes de atualizar." >&2
    exit 1
fi

git fetch --quiet --tags origin
versao="$(git tag --list 'v*' --sort=-v:refname | head -n 1)"
if [ -z "$versao" ]; then
    echo "Ainda não há versão publicada." >&2
    exit 1
fi

git -c advice.detachedHead=false checkout --quiet "$versao"
./instalar.sh --sem-iniciar
systemctl --user restart alarma-meme.service
echo "Atualizado para $versao."
exit 0
}
