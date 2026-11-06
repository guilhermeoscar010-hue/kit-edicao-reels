# Instala o kit de edicao de Reels no Claude Code (Windows / PowerShell).
# Uso: na pasta do repositorio clonado ->  powershell -ExecutionPolicy Bypass -File .\instalar.ps1
$ErrorActionPreference = "Stop"
$kit = $PSScriptRoot
$skills = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force $skills | Out-Null

Write-Host "1/6 Conferindo ffmpeg, python, node e git..."
foreach ($c in "ffmpeg", "python", "node", "git") {
    if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Write-Warning "$c nao encontrado. Veja docs/SKILLS-DE-EDICAO.md (winget)." }
}

Write-Host "2/6 Copiando a skill editar-reel..."
Copy-Item -Recurse -Force (Join-Path $kit "skills\editar-reel") $skills

Write-Host "3/6 Pastas de trabalho..."
foreach ($p in "Videos para editar", "Videos editados", "Videos de referência", "reels-studio\projetos") {
    New-Item -ItemType Directory -Force (Join-Path $kit $p) | Out-Null
}

Write-Host "4/6 Python (faster-whisper + onnxruntime) em ~/.venvs/whisper..."
$venv = Join-Path $env:USERPROFILE ".venvs\whisper"
if (-not (Test-Path "$venv\Scripts\python.exe")) { python -m venv $venv }
& "$venv\Scripts\python.exe" -m pip install --upgrade pip
& "$venv\Scripts\python.exe" -m pip install faster-whisper onnxruntime numpy

Write-Host "5/6 Modelo de recorte RVM (15 MB)..."
$onnx = Join-Path $kit "reels-studio\modelos\rvm_mobilenetv3_fp32.onnx"
if (-not (Test-Path $onnx)) {
    curl.exe -L -o $onnx "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
}

Write-Host "6/6 Skills de terceiros (get-brolls e HyperFrames)..."
$gb = Join-Path $skills "get-brolls"
if (-not (Test-Path $gb)) { git clone https://github.com/engenheirodevideo/get-brolls.git $gb }
npx -y skills add heygen-com/hyperframes

Write-Host ""
Write-Host "Pronto. Falta fazer a mao:"
Write-Host " - Seguir o README do get-brolls (cria .venv e .env) e colocar PIXABAY_API_KEY no .env dele."
Write-Host " - Colocar os SFX .wav em reels-studio\sfx\ (whip, whoosh, ding, vine-boom, mouse-click, page-turn, shutter-modern)."
Write-Host " - Rodar um render de teste do HyperFrames uma vez (baixa o Chrome headless e as fontes Poppins que o gerar_assets.cjs usa)."
Write-Host " - Pedir ao Claude Code: 'edita o video da pasta Videos para editar'."
