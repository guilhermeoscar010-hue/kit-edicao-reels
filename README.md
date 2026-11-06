# Kit de Edição de Reels (Claude Code)

Estilo de edição do Guilherme empacotado como skill do Claude Code. Você joga o vídeo numa pasta, pede "edita" e recebe o Reel pronto, com:

- legenda Poppins com palavra-chave em amarelo numa 2ª linha maior;
- imagens PNG **atrás da pessoa** (objeto grande atrás da cabeça) e **cards com moldura amarela tracejada** acima da cabeça;
- punch-in, zoom-out, tremida, flash, cor viva e efeitos sonoros;
- cortes de pausas e repetições;
- tudo em ~30–40 min para um vídeo de 1–2 min, num notebook comum.

## O que tem aqui

| Caminho | Conteúdo |
|---|---|
| `skills/editar-reel/SKILL.md` | A skill (o passo a passo que o Claude segue) |
| `docs/ESTILO-E-FEEDBACK.md` | Todas as correções, preferências e lições acumuladas: o "gosto" do estilo |
| `docs/SKILLS-DE-EDICAO.md` | Todas as skills de edição usadas (get-brolls, HyperFrames etc.) e como instalar |
| `reels-studio/` | Ferramentas (Python/Node/ffmpeg), `ESTILO.md`, `estilo-ref.json`, glossário |
| `instalar.ps1` | Instalação automática no Windows |

## Instalar (Windows)

1. Instale [Claude Code](https://claude.com/claude-code), Git, ffmpeg, Python 3.10+ e Node 18+ (comandos `winget` em `docs/SKILLS-DE-EDICAO.md`).
2. Clone na sua pasta de usuário:
   ```powershell
   git clone https://github.com/guilhermeoscar010-hue/kit-edicao-reels.git $env:USERPROFILE\kit-edicao-reels
   cd $env:USERPROFILE\kit-edicao-reels
   powershell -ExecutionPolicy Bypass -File .\instalar.ps1
   ```
3. Faça os passos manuais que o instalador listar no final (chave Pixabay grátis, SFX, render de teste do HyperFrames).
4. Coloque um vídeo em `Videos para editar\`, abra o Claude Code na pasta do kit e peça: **"edita o vídeo"**.

## Adaptar ao seu nicho

- `reels-studio/glossario.txt`: troque pelos termos do seu conteúdo (melhora a transcrição e os destaques).
- `docs/ESTILO-E-FEEDBACK.md`: quando o resultado não for do seu gosto, corrija o Claude no chat e peça para ele registrar aqui.
- Coloque Reels que você quer imitar em `Videos de referência\` e peça para ele analisar e atualizar `ESTILO.md` seção 6.

## Observações

- Sem GPU Intel, rode o `gerar_ff.py` sem `--qsv`.
- Notebook com 8 GB de RAM: feche navegador/VS Code antes de compor.
- Skills de terceiros mantêm suas licenças (get-brolls MIT; RVM GPL-3.0).
