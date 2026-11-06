# Rato-Alarme

Um rato que foge pela tela até você bater o ponto. Nos horários de entrada e de saída, ele aparece, toca um alarme e apronta travessuras até ser pego com 3 cliques.

Funciona no Windows, no macOS e no Linux com Hyprland. A versão para Windows e macOS é nova e ainda está em teste.

## Instalar no Windows

Precisa do Windows 10 ou 11 de 64 bits. Não precisa de administrador.

1. Baixe `Rato-Alarme-Windows.exe` na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest).
2. Abra o arquivo.
3. Se aparecer o aviso "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**. O aviso aparece porque o app não tem assinatura digital.
4. Siga o instalador.

O ícone do rato fica na bandeja, perto do relógio. Se não aparecer, clique na setinha **^** ao lado do relógio.

## Instalar no macOS

Precisa do macOS 14 (Sonoma) ou mais novo.

1. Na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest), baixe o arquivo do seu Mac:
   - Chip Apple (M1 ou mais novo): `Rato-Alarme-macOS-AppleSilicon.dmg`
   - Processador Intel: `Rato-Alarme-macOS-Intel.dmg`

   Para saber qual é o seu, abra o menu  > **Sobre Este Mac**.
2. Abra o arquivo e arraste o Rato-Alarme para a pasta **Aplicativos**.
3. Abra o Rato-Alarme. O macOS vai bloquear, porque o app não tem assinatura digital.
4. Vá em **Ajustes do Sistema > Privacidade e Segurança**, role até o aviso do Rato-Alarme e clique em **Abrir Mesmo Assim**.

O ícone do rato fica na barra de menus, no topo da tela. O app não aparece no Dock.

## Primeiro uso

Na primeira vez, o painel de controle abre sozinho. Coloque seus horários de entrada e de saída e clique em **Salvar**. Os horários padrão são 06:50 e 12:49.

Se você abrir o app até 1 hora depois de um desses horários, o rato aparece na hora.

Depois disso, o rato inicia junto com o computador e fica escondido até o próximo horário. Para desligar isso, use **Iniciar com o computador** no painel.

## Como funciona

O rato aparece no horário e foge do cursor. De tempos em tempos ele cansa e para, e fica mais fácil clicar. São 3 cliques para pegar.

Enquanto está solto, ele pode:

- abrir um bloco de notas e escrever nele;
- abrir um vídeo de queijo no navegador, no máximo uma vez por alarme;
- deixar o computador sem som. O som volta quando você pega o rato.

Se o computador ligar até 1 hora depois do horário, ele aparece assim que o programa iniciar. Depois disso, espera o próximo horário.

No Linux com Hyprland, ele também mexe e fecha janelas de outros programas. Isso não existe no Windows e no macOS.

## Menu do ícone

- **Painel de controle:** muda os horários e desliga o alarme.
- **Sair:** encerra o rato até o próximo boot.

No Windows, um clique no ícone abre o painel, e o botão direito abre o menu. No macOS, um clique abre o menu.

Para ligar de novo depois de sair, abra o Rato-Alarme pelo menu Iniciar ou pela pasta **Aplicativos**. Abrir o app com ele já rodando mostra o painel.

## Atualizar

Quando sai uma versão nova, o ícone avisa e o menu mostra **Atualizar para a versão X**. Seus horários continuam iguais depois de atualizar.

- **Windows:** clique na opção para baixar o instalador novo e abra o arquivo. Ele troca a versão antiga.
- **macOS:** clique na opção para baixar o DMG novo, clique em **Sair** no menu e arraste o app para **Aplicativos**, escolhendo **Substituir**. Pode ser preciso liberar o app de novo em **Privacidade e Segurança**.
- **Linux:** clique na opção e ele atualiza e reinicia sozinho. Também dá para rodar `./atualizar.sh`.

Para isso, o programa consulta o GitHub de tempos em tempos. Ele não envia seus horários nem dados pessoais.

## Problemas comuns

**O rato não apareceu.** Confira no painel se **Alarme ligado** está marcado e se o horário está certo. Ele só aparece se o computador estiver ligado até 1 hora depois do horário.

**O computador ficou sem som.** O som volta quando você pega o rato ou quando o programa abre de novo. Se você mesmo tinha deixado sem som, ele continua assim.

**Abri o app e nada aconteceu.** Procure o ícone na bandeja ou na barra de menus. No Mac com muitos ícones, ele pode ficar escondido atrás do entalhe da tela.

## Remover

**Windows:** clique em **Sair** no menu do ícone. Depois, vá em **Configurações > Aplicativos > Aplicativos instalados** e desinstale o Rato-Alarme. Seus horários ficam em `%APPDATA%\alarma-meme`, e a pasta pode ser apagada à mão.

**macOS:** desmarque **Iniciar com o computador** no painel, clique em **Salvar** e depois em **Sair**. Apague o app da pasta **Aplicativos**. Seus horários ficam em `~/Library/Application Support/alarma-meme`, e a pasta pode ser apagada à mão.

## Linux

Precisa de Hyprland, PipeWire, Python 3.10 ou mais novo, Git e uma barra compatível com StatusNotifierItem.

```sh
git clone https://github.com/ArturLT/Rato-Alarme.git
cd Rato-Alarme
./instalar.sh
```

As dependências ficam em `.venv`, dentro da pasta. Se você instalar até 1 hora depois de um horário, o alarme toca na hora. Para evitar isso, use `./instalar.sh --sem-iniciar`, e ele começa só no próximo boot.

Não mova a pasta depois de instalar. Se mover, rode `./instalar.sh` de novo.

Para remover, rode `./desinstalar.sh`. A configuração fica em `~/.config/alarma-meme` e pode ser apagada à mão.

Se você instalou antes da versão 1.0.0, atualize uma vez à mão:

```sh
git pull
./instalar.sh --sem-iniciar
systemctl --user restart alarma-meme.service
```

## Publicar uma versão

1. Mude o número em `alarma/versao.py` e faça o commit.
2. Crie e envie a tag com o mesmo número:

   ```sh
   git tag v1.1.0
   git push origin main v1.1.0
   ```

O GitHub Actions roda os testes, monta os instaladores e publica o Release. Se a tag não bater com `alarma/versao.py`, nada é publicado.

## Desenvolver

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests
```
