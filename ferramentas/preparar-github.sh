#!/bin/bash
# Liga esta pasta (baixada como .zip) ao repositório do GitHub e guarda tudo num commit, numa branch nova.
#   bash ferramentas/preparar-github.sh [URL do repositório] [nome da branch]
# Não envia nada sozinho: no fim ele mostra o comando de push.
set -eu

URL="${1:-https://github.com/ArturLT/Rato-Alarme.git}"
BRANCH="${2:-pet-pixel-art}"
cd "$(dirname "$0")/.."

command -v git >/dev/null || { echo "Falta o git. No Mac: xcode-select --install" >&2; exit 1; }

if [ ! -d .git ]; then
    echo "Ligando esta pasta a $URL..."
    git init -q
    git remote add origin "$URL"
fi
git fetch origin

if ! git rev-parse --verify -q HEAD >/dev/null; then
    # Pasta nova: o histórico passa a ser o da main do GitHub, e os arquivos daqui ficam como mudanças.
    git reset -q origin/main
fi
git checkout -q -B "$BRANCH"

if [ -x .venv-empacotar/bin/python ]; then
    echo "Rodando os testes..."
    QT_QPA_PLATFORM=offscreen .venv-empacotar/bin/python -m unittest discover -s tests
fi

git add -A
echo
echo "O que muda em relação à main do GitHub:"
git status --short | head -60
echo
if git diff --cached --quiet; then
    echo "Nada para guardar."
    exit 0
fi
git commit -q -m "feat: pet em pixel art com personalização, vida, lembretes e painel novo" \
    -m "Rato personalizável (pelo, roupa, chapéu, cabelo, rosto, pescoço, nome e personalidade), barriga, diversão, felicidade e vida, lembretes com aviso, colo, bolinha, comida, travessuras novas, andar entre monitores e painel e menus em pixel art."
echo "Commit criado na branch $BRANCH."
echo
echo "Confira se nada da main sumiu (se o .zip era mais antigo que a main, aparece aqui como apagado):"
echo "    git diff --stat origin/main"
echo
echo "Para enviar ao GitHub:"
echo "    git push -u origin $BRANCH"
echo "Depois abra um Pull Request no GitHub, ou junte na main seguindo a colinha de git."
