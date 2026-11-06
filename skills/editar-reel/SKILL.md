---
name: editar-reel
description: Edita Reels/vídeos verticais no estilo do kit (legenda Poppins com destaque amarelo em 2ª linha maior, imagens PNG atrás da pessoa, cards tracejados acima da cabeça, punch-in/zoom-out, SFX, cor viva) com pipeline ffmpeg rápido. Use quando o usuário mandar um vídeo (.MOV/.mp4) pedindo para editar, legendar, colocar efeitos, ou disser "edita esse vídeo", "/editar-reel".
---

# Editar Reel (pipeline rápido)

Convenções (ajuste se clonou em outro lugar):
- `KIT` = pasta onde o repositório foi clonado (padrão: `%USERPROFILE%\kit-edicao-reels`).
- `RS` = `KIT\reels-studio`.
- `PYW` = Python com Whisper: `%USERPROFILE%\.venvs\whisper\Scripts\python.exe` (criado pelo `instalar.ps1`).
- HyperFrames CLI fixado: `npx hyperframes@0.8.189` (só para baixar Chrome headless/fontes e para o estilo antigo).

## Pastas fixas (ler antes de tudo)
- **Fila de entrada**: `KIT\Videos para editar\`. Quando o usuário pedir "edita" sem passar caminho, **listar a pasta na hora** e pegar o vídeo de lá; se houver mais de um e não for óbvio, perguntar UMA vez.
- **Saída**: `KIT\Videos editados\`.
- **Referências**: `KIT\Videos de referência\`. Modelo descrito em `RS/ESTILO.md` seção 6. Vídeo novo na pasta → contact sheet com ffmpeg e atualizar a seção 6.

## 0. Antes de tudo (30 s)
1. **Ler `KIT/docs/ESTILO-E-FEEDBACK.md`** (correções já feitas, preferências, erros a não repetir, checklist). Não adicionar título/emoji que não foi pedido; sempre camada visual (PNG atrás + cards).
2. Ler `RS/ESTILO.md`, `RS/estilo-ref.json`, `RS/glossario.txt` (troque os termos do glossário pelos do seu nicho).
3. Só perguntar o que bloqueia. Palavras que o Whisper não entendeu: juntar todas e perguntar UMA vez.
4. RAM livre > 1,5 GB e nenhum `node`/`ffmpeg` esquecido rodando (`Get-Process`).

## 1. Preparar (rodar em background; converte HDR→SDR sozinho; Whisper com 10 threads e beam 1)
`PYW -I RS/ferramentas/preparar.py "<video>" <nome-curto>` (`--modelo small` se o vídeo for longo e a pressa maior).
Gera `RS/projetos/<nome>/`: `assets/video.mp4` (1080×1920 H.264 30 fps), `assets/sfx/`, `work/palavras.json`, `work/lista.txt`, `work/folha.jpg`.
Enquanto roda: olhar `work/folha.jpg` (onde ficam rostos → ajustar posição da legenda se tampar algo).

## 2. Paginar (automático, 1 s)
`python RS/ferramentas/paginar.py RS/projetos/<nome>` → `edicao.json` + `work/legenda.txt` (`*palavra*` = destaque, lista de EFEITOS).
Já aplica: glossário, máx 3 palavras, quebra em pontuação/pausa, sem take < 0,4 s, sem terminar em artigo, destaques (glossário + números), efeitos por prioridade, cortes de zoom por frase.

## 3. Revisar o rascunho (único trabalho manual: ~5 min)
Ler `work/legenda.txt` + `work/lista.txt` (`<<` = baixa confiança). Corrigir no `edicao.json`:
- palavras erradas (registrar no `glossario.txt` como `errado => certo`);
- destaques (palavra-chave da frase, números, CTA) — o destaque vai na 2ª linha, maior, amarelo `#F5D90A`;
- efeitos nos momentos de efeito (gancho, virada, número, CTA): `punch` (zoom-in + tremida + flash) / `afasta` (zoom-out). SFX: `whip`, `whoosh`, `ding`, `vine-boom`, `mouse-click`, `page-turn`, `shutter-modern` (arquivos .wav em `RS/sfx/`);
- **camada visual obrigatória**: `imagens[]` com `modo: "atras"` (objeto grande atrás da cabeça) e `modo: "card"` (moldura amarela tracejada acima da cabeça), `atras[]` para texto atrás da pessoa;
- cortes de silêncio inicial, repetições e pausas quando pedido.
Imagens: Pixabay via `curl` (licença livre; chave em `PIXABAY_API_KEY`). Objeto = PNG já transparente (`image_type=illustration`/`vector`) ou foto inteira dentro do card. Registrar origem em `assets/png/origem.txt`.

## 4. Gerar (pipeline ffmpeg — NÃO usar o render do Chrome/HyperFrames)
Medido num notebook i5-1235U / 7,7 GB RAM sem GPU dedicada: o render do HyperFrames faz ~0,6 s por quadro (≈20× o tempo real) e quebra com "Unable to capture screenshot" em vídeo HDR; o `hyperframes remove-background` levou > 30 min para 4 s. Tudo isso está FORA do fluxo. Use:
1. `PYW -I RS/ferramentas/recortar.py RS/projetos/<nome>`: alfa da pessoa (RVM MobileNetV3, ~4 fps) **só nas janelas com texto/imagem ATRÁS** → `assets/matte-*.mkv`. Nunca recortar o vídeo inteiro.
2. `node RS/ferramentas/gerar_assets.cjs RS/projetos/<nome>`: legendas, textos atrás, cards e imagens viram PNGs transparentes (~1 s por PNG) → `work/png/`.
3. `python RS/ferramentas/gerar_ff.py RS/projetos/<nome> --qsv` → `renders/<nome>-ff.mp4` (zoom/punch/tremida, flash, cor, SFX, loudnorm −14 LUFS). `--qsv` só com GPU Intel; sem ela, omitir. Prévia: `--ate 10`. Isolar camada: `--pular atras,recorte,zoom,flash,cards,legendas`.
Revisão visual: `ffmpeg -ss <t> -i renders/<nome>-ff.mp4 -frames:v 1 q.png` em 4–6 instantes (efeito, destaque, card, objeto atrás) antes de entregar.

## 5. Entrega
1. Copiar para `KIT\Videos editados\<nome>-editado.mp4` e gerar cópia leve (`-vf scale=720:-2 -crf 26`) para mandar no chat/celular.
2. Orçamento-alvo para vídeo de 2 min: preparar ≈ 8–10 min · revisar ≈ 5 · recortar ≈ 2 · assets ≈ 3 · compor ≈ 6 → **30–40 min no total**.

## 6. Depois de entregar
Atualizar `glossario.txt`, `ESTILO.md` (se algo foi aprovado) e `docs/ESTILO-E-FEEDBACK.md` com qualquer correção nova do usuário.
