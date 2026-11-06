# Estilo de edição e feedback acumulado

Tudo que o Guilherme corrigiu, preferiu e aprovou enquanto o estilo foi construído com o Claude Code. A skill `editar-reel` lê este arquivo antes de cada edição. Quando o seu gosto divergir, edite aqui: este é o "cérebro" do estilo.

## A. Regras de estilo (vieram de correções diretas)

1. **Não inventar elemento que não foi pedido.** Um título "🚗 carro no boleto" no começo do vídeo foi rejeitado. Legenda = só a fala. Título, emoji, gancho de texto: só se pedir.
2. **Legenda sozinha não basta.** Todo vídeo sai com camada visual: **imagens PNG atrás da pessoa** (objeto grande atrás da cabeça), **cards** acima da cabeça, **cor viva** e efeitos.
3. **Estilo das imagens** (modelo aprovado):
   - 3 cards com **moldura amarela tracejada** acima da cabeça (ex.: caixa, silhueta com maleta, maço de dinheiro);
   - **laptop com contador regressivo** (01:00 → 00:17);
   - **globo gigante atrás da cabeça** com legenda de 2 linhas: 1ª branca pequena, 2ª amarela grande em caixa alta;
   - objetos 3D/emoji, contratos voando, polaroid — sempre ao lado/atrás, **nunca cobrindo o rosto**.
4. **Imagens livres de copyright** (Pixabay, sem crédito obrigatório). Registrar a origem de cada imagem em `origem.txt`. Nunca colar a chave da API em chat ou arquivo versionado.
5. **Cor viva**: saturação e contraste acima do original (`eq=saturation=1.28:contrast=1.08:brightness=0.02`).
6. **Cortes**: quando pedir, cortar silêncio inicial, repetições e pausas.
7. **Tempo**: edição inteira em **30–40 min** para vídeo de 50 s–2 min. 2 horas é inaceitável.

## B. Tipografia e ritmo (modelo das referências)

- **Legenda**: Poppins 800, 2–3 palavras por take, branca com sombra suave, no peito (y ≈ 55–65% da tela), abaixo do rosto.
- **Destaque**: palavra-chave em **amarelo `#F5D90A`**, maior, numa **2ª linha** embaixo da legenda.
- **Cartelas de lista**: número amarelo itálico grande + título em itálico no topo.
- **Ritmo**: algo novo na tela a cada 2–4 s; legenda troca a cada ~1 s; rosto nunca fica 5 s sem novidade.
- **Câmera**: punch-in (zoom rápido + tremida + flash) nas falas de efeito; zoom-out em números/datas; micro-zoom entre frases.
- **Som**: SFX discretos só onde há ação (whip/whoosh alternados, ding em termo de impacto, click em "link"). Nunca o mesmo som em todo efeito. Música só se pedir.
- Valores exatos: `reels-studio/estilo-ref.json`.

## C. Forma de trabalhar

- **Pastas fixas**: `Videos para editar` (entrada — listar na hora, o conteúdo muda), `Videos editados` (saída), `Videos de referência` (modelo).
- **Entrega dupla**: salvar em `Videos editados` e mandar no chat uma cópia leve 720p (arquivo > 30 MB não chega no celular).
- **Autonomia**: "faça o que preferir" → escolher o padrão sensato e seguir; perguntar só o que bloqueia, numa pergunta só.
- **Causa medida**: quando algo é lento ou falha, explicar o motivo com número, não palpite.
- Respostas curtas e diretas, em português.

## D. Erros que não se repetem (lições técnicas)

1. **Medir antes de agir.** `remove-background` no vídeo inteiro levou > 30 min. Sempre amostra pequena com timeout; recorte só nas janelas "atrás".
2. **Ler o log antes de repetir.** Render quebrou 3× com "Unable to capture screenshot"; causa: vídeo do iPhone em HDR (HLG/BT.2020). Checar `ffprobe color_transfer` primeiro; o `preparar.py` já converte HDR→SDR.
3. **Nada de benchmark esquecido em background**: infla todas as medições. Antes de medir: `Get-Process` (node/ffmpeg) e RAM livre; ao terminar, matar o que foi iniciado.
4. **RAM é o gargalo oculto** em notebook de 8 GB. Antes do render: RAM livre > 1,5 GB; fechar VS Code/Chrome/apps pesados.
5. **Não usar o render do Chrome/HyperFrames** para vídeo > 30 s em notebook. Fluxo: `recortar.py` → `gerar_assets.cjs` → `gerar_ff.py`. Prévia rápida: `--ate 10`. Não re-renderizar tudo para ajuste pequeno.
6. **Conferir o arquivo, não o exit code.** Olhar quadros (inclusive emendas) antes de dizer que está pronto.
7. **Download do Pixabay**: `urllib` do Python leva 403 → usar `curl`. Nunca falsificar User-Agent.
8. **Windows**: PowerShell `$in` é palavra reservada; `\U` em string Python de caminho vira escape (usar `/` ou `r""`).
9. **Objetos ≠ pessoa**: `remove-background` só serve para pessoa; para objeto usar PNG já transparente (Pixabay `image_type=illustration`/`vector`) ou a foto inteira dentro do card.
10. **Mudança de estilo**: avisar uma vez e registrar em `ESTILO.md`, nunca trocar em silêncio.

## E. Checklist de cada edição

1. Listar `Videos para editar`; ler este arquivo, `ESTILO.md` e a skill `editar-reel`.
2. RAM livre > 1,5 GB, sem processos esquecidos.
3. `preparar.py` (background) → `folha.jpg` → `paginar.py` → revisar `edicao.json` (cortes, destaques, efeitos, **imagens atrás + cards**, sem título/emoji).
4. Imagens: Pixabay via `curl`, registrar origem.
5. `recortar.py` → `gerar_assets.cjs` → `gerar_ff.py` → conferir quadros.
6. Salvar em `Videos editados` e mandar a cópia leve.
