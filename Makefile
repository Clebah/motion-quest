.PHONY: help test test-ai test-video pipeline-mock render run all clean

help:
	@echo "=========================================================="
	@echo "🎬 Motion Quest — Monorepo Automation (SPEC-002 v3)"
	@echo "=========================================================="
	@echo "Comandos disponíveis:"
	@echo "  make run           - Roda o pipeline com as fotos de inputs/ e gera o vídeo final"
	@echo "  make all           - Roda testes + pipeline em modo teste + renderiza vídeo"
	@echo "  make test          - Executa os testes automatizados de ambos os workers"
	@echo "  make test-ai       - Executa os testes do Worker de IA (Python)"
	@echo "  make test-video    - Executa os testes do Worker de Vídeo (Remotion/Node)"
	@echo "  make render        - Renderiza o vídeo a partir do último manifest gerado"
	@echo "=========================================================="

test-ai:
	@echo "🧪 Executando testes do Worker IA & Visão (Python)..."
	cd packages/ai-vision && python3 tests/exec_tests.py

test-video:
	@echo "🧪 Executando testes do Worker Video Render (Node/TS)..."
	cd packages/video-render && node --test tests/manifest_parser.test.js

test: test-ai test-video
	@echo "✅ Todos os testes dos workers passaram com sucesso!"

pipeline-mock:
	@echo "🚀 Executando Pipeline de IA & Visão (Modo Mock / Offline)..."
	cd packages/ai-vision && PYTHONPATH=. python3 src/adapters/inbound/cli/pipeline.py --mock --output ../../output/run

run:
	@echo "🚀 Executando Pipeline de IA & Visão com suas fotos e roteiro..."
	cd packages/ai-vision && PYTHONPATH=. python3 src/adapters/inbound/cli/pipeline.py --inputs ../../inputs --prompt-file ../../inputs/roteiro.txt --output ../../output/run
	@echo "🎥 Renderizando vídeo final com o Remotion..."
	cd packages/video-render && node dist/adapters/inbound/cli/index.js --manifest=../../output/run/manifest.json --out=out/meu_video.mp4
	@echo "🎉 Vídeo gerado com sucesso em: packages/video-render/out/meu_video.mp4"

render:
	@echo "🎥 Renderizando vídeo via Worker Video Render..."
	cd packages/video-render && node dist/adapters/inbound/cli/index.js --manifest=../../output/run/manifest.json --out=out/meu_video.mp4

all: test pipeline-mock render
	@echo "🌟 Execução completa finalizada com sucesso!"
