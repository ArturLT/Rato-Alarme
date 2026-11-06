# Rato-Alarme

Um rato que foge pela tela até você bater o ponto. Ele aparece nos horários de entrada e de saída, toca um alarme e apronta travessuras até ser pego com 3 cliques. Se o computador ligar até 1 hora depois do horário, ele aparece assim que o programa iniciar. Depois disso, espera o próximo horário.

Funciona no Windows, no macOS e no Linux com Hyprland e PipeWire. Fechar e mexer em janelas de outros programas só existe no Hyprland. No Windows e no macOS, o rato faz as outras travessuras.

## Instalar no Windows

1. Baixe `Rato-Alarme-Windows.exe` na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest).
2. Abra o arquivo. Como o app não tem assinatura digital, o Windows pode avisar que ele é desconhecido. Clique em **Mais informações** e depois em **Executar assim mesmo**.

Não precisa de administrador. O rato passa a iniciar com o computador.

Para remover, use **Configurações > Aplicativos**.

## Instalar no macOS

1. Baixe o arquivo da [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest):
   - Mac com chip M: `Rato-Alarme-macOS-AppleSilicon.dmg`
   - Mac com Intel: `Rato-Alarme-macOS-Intel.dmg`
2. Abra o arquivo e arraste o Rato-Alarme para **Aplicativos**.
3. Abra o app. Como ele não tem assinatura digital, o macOS vai bloquear. Vá em **Ajustes do Sistema > Privacidade e Segurança** e clique em **Abrir Mesmo Assim**.

O ícone fica na barra de menus, e o rato passa a iniciar com o computador.

Para remover, desligue **Iniciar com o computador** no painel, clique em **Sair** e apague o app de **Aplicativos**.

## Instalar no Linux

Precisa de Hyprland, PipeWire, Python 3.10 ou mais novo, Git e uma barra compatível com StatusNotifierItem.

```sh
git clone https://github.com/ArturLT/Rato-Alarme.git
cd Rato-Alarme
./instalar.sh
```

As dependências ficam em `.venv`, dentro da pasta. Se você instalar até 1 hora depois de um horário, o alarme toca na hora. Para evitar isso, use `./instalar.sh --sem-iniciar`, e ele começa só no próximo boot.

Não mova a pasta depois de instalar. Se mover, rode `./instalar.sh` de novo.

Para remover, rode `./desinstalar.sh`. A configuração fica em `~/.config/alarma-meme` e pode ser apagada à mão.

## Usar

Abra o menu do ícone na bandeja para ver o estado do alarme:

- **Painel de controle:** muda os horários de entrada e saída e desliga o alarme.
- **Sair:** encerra o rato até o próximo boot.

Para ligar de novo depois de sair, abra o **Rato-Alarme** pelo menu de aplicativos. Abrir o programa com ele já rodando mostra o painel.

## Atualizar

O programa consulta o GitHub de tempos em tempos. Quando há versão nova, a bandeja avisa e o menu mostra **Atualizar para a versão X**. A configuração continua igual depois de atualizar.

- **Linux:** o rato atualiza e reinicia sozinho. Também dá para rodar `./atualizar.sh`.
- **Windows:** a opção baixa o instalador novo. Abra o arquivo, e ele troca a versão antiga.
- **macOS:** a opção baixa o DMG novo. Clique em **Sair** e arraste o app para **Aplicativos** de novo.

Se você instalou no Linux antes da versão 1.0.0, atualize uma vez à mão:

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

O GitHub Actions roda os testes nos sistemas, monta os instaladores e publica o Release. Se a tag não bater com `alarma/versao.py`, nada é publicado.

## Desenvolver

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests
```
