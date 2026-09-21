.PHONY: help test test-ai test-video pipeline-mock render all clean

help:
	@echo "=========================================================="
	@echo "🎬 Motion Quest — Monorepo Automation (SPEC-002 v3)"
	@echo "=========================================================="
	@echo "Comandos disponíveis:"
	@echo "  make test          - Executa os testes automatizados de ambos os workers"
	@echo "  make test-ai       - Executa os testes do Worker de IA (Python)"
	@echo "  make test-video    - Executa os testes do Worker de Vídeo (Remotion/Node)"
	@echo "  make pipeline-mock - Roda o pipeline de IA em modo mock e gera manifest.json"
	@echo "  make render        - Renderiza o vídeo a partir do manifest.json gerado"
	@echo "  make all           - Executa o fluxo completo (testes + pipeline + render)"
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

render:
	@echo "🎥 Renderizando vídeo via Worker Video Render..."
	cd packages/video-render && node -e " \
		import('./dist/application/use-cases/RenderFromManifestUseCase.js').then(({ RenderFromManifestUseCase }) => { \
			import('./dist/adapters/outbound/RemotionRendererAdapter.js').then(({ RemotionRendererAdapter }) => { \
				const uc = new RenderFromManifestUseCase(new RemotionRendererAdapter()); \
				uc.execute('../../output/run/manifest.json', 'out/final_video.mp4') \
				  .then(res => console.log('🎉 Vídeo final pronto em: packages/video-render/' + res)); \
			}); \
		}); \
	"

all: test pipeline-mock render
	@echo "🌟 Execução completa finalizada com sucesso!"
