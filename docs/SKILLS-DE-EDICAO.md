# Skills de edição usadas no kit

Skills de terceiros não são copiadas para cá: instale da fonte oficial (recebe atualizações e respeita a licença de cada uma). O `instalar.ps1` faz tudo isso.

| Skill | Para que serve | Fonte | Instalação |
|---|---|---|---|
| **editar-reel** (deste kit) | Edição completa no estilo do Guilherme | este repositório | copiar `skills/editar-reel` para `~/.claude/skills/` |
| **get-brolls** | Busca B-rolls/imagens (Pixabay, Pexels) com revisão e origem registrada | [engenheirodevideo/get-brolls](https://github.com/engenheirodevideo/get-brolls) (MIT) | `git clone https://github.com/engenheirodevideo/get-brolls.git ~/.claude/skills/get-brolls` e seguir o README dele (cria `.venv` e `.env`) |
| **hyperframes** | Contrato HTML→vídeo, captions, motion, formatos verticais | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | `npx skills add heygen-com/hyperframes` |
| **hyperframes-cli** | CLI: init, check, preview, render, remove-background | idem | idem (vem junto) |
| **hyperframes-registry** | ~450 blocos prontos (transições, títulos, kinetic type) | idem | idem |
| **media-use** | Música, SFX, imagens, ícones, transcrição para vídeos | idem | idem |
| **video** (opcional) | Planejamento de vídeo com IA/frameworks | [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) | `npx skills add coreyhaines31/marketingskills --skill video` |
| **remotion** (opcional) | Vídeo em React (alternativa ao HyperFrames) | [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | `npx skills add remotion-dev/remotion` |
| **find-skills** (opcional) | Descobrir outras skills | [vercel-labs/skills](https://github.com/vercel-labs/skills) | `npx skills add https://github.com/vercel-labs/skills --skill find-skills` |

## Ferramentas (não são skills)

| Ferramenta | Uso | Instalação (Windows) |
|---|---|---|
| ffmpeg ≥ 7 (com libass, zscale) | toda a composição | `winget install Gyan.FFmpeg` |
| Python 3.10+ | Whisper, recorte RVM | `winget install Python.Python.3.12` |
| faster-whisper, onnxruntime, numpy | transcrição e recorte | venv em `~/.venvs/whisper` (o `instalar.ps1` cria) |
| Node.js 18+ | `gerar_assets.cjs` e `npx hyperframes` | `winget install OpenJS.NodeJS.LTS` |
| Modelo RVM MobileNetV3 (ONNX, 15 MB, GPL-3.0) | recorte da pessoa | baixado pelo `instalar.ps1` de [PeterL1n/RobustVideoMatting](https://github.com/PeterL1n/RobustVideoMatting/releases) |
| Chave Pixabay | imagens livres | grátis em https://pixabay.com/api/docs/ → `PIXABAY_API_KEY` no `.env` do get-brolls |
