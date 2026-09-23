import * as fs from "node:fs/promises";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { VideoManifest } from "../../domain/entities/Manifest.js";
import { VideoRendererPort } from "../../application/ports/VideoRendererPort.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export class RemotionRendererAdapter implements VideoRendererPort {
  async renderVideo(manifest: VideoManifest, outputPath: string): Promise<string> {
    console.log(`🎥 [RemotionRenderer] Iniciando montagem para o projeto ${manifest.projectId}...`);
    console.log(`📐 Resolução: ${manifest.resolution.width}x${manifest.resolution.height} @ ${manifest.fps}fps`);
    console.log(`🎬 Duração Total: ${manifest.totalDurationSeconds}s (${manifest.scenes.length} cenas)`);

    // 1. Garantir que a pasta de destino exista
    const resolvedOutput = path.resolve(outputPath);
    const outDir = path.dirname(resolvedOutput);
    await fs.mkdir(outDir, { recursive: true });

    // 2. Tentar empacotar e renderizar MP4 com Remotion
    let renderSuccess = false;
    try {
      console.log(`📦 Empacotando composições Remotion...`);
      // Aponta para o entry point index.ts ou index.js
      let entryPoint = path.resolve(__dirname, "../../infrastructure/remotion/index.js");
      try {
        await fs.stat(entryPoint);
      } catch {
        entryPoint = path.resolve(__dirname, "../../infrastructure/remotion/index.ts");
      }

      // Sanitiza o manifest para o Remotion (valida existência de arquivos e formata file://)
      const sanitizedScenes = await Promise.all(
        manifest.scenes.map(async (scene) => {
          let clipPath = scene.clipPath;
          if (clipPath) {
            try {
              const stat = await fs.stat(clipPath);
              if (!stat.isFile() || stat.size < 10) clipPath = undefined;
            } catch {
              clipPath = undefined;
            }
          }

          let imagePath = scene.imagePath;
          if (imagePath) {
            try {
              const stat = await fs.stat(imagePath);
              if (!stat.isFile() || stat.size < 10) imagePath = undefined;
            } catch {
              imagePath = undefined;
            }
          }

          if (imagePath && !imagePath.startsWith("http") && !imagePath.startsWith("file://")) {
            imagePath = `file://${path.resolve(imagePath)}`;
          }
          if (clipPath && !clipPath.startsWith("http") && !clipPath.startsWith("file://")) {
            clipPath = `file://${path.resolve(clipPath)}`;
          }

          return {
            ...scene,
            clipPath,
            imagePath,
          };
        })
      );

      const sanitizedManifest: VideoManifest = {
        ...manifest,
        scenes: sanitizedScenes,
      };

      const bundled = await bundle({
        entryPoint,
        webpackOverride: (config) => config,
      });

      console.log(`🎬 Selecionando composição 'PersonaStory'...`);
      const composition = await selectComposition({
        serveUrl: bundled,
        id: "PersonaStory",
        inputProps: { manifest: sanitizedManifest },
      });

      // Sobrescreve duração e fps de acordo com o manifest
      const updatedComposition = {
        ...composition,
        durationInFrames: Math.round(sanitizedManifest.totalDurationSeconds * sanitizedManifest.fps),
        fps: sanitizedManifest.fps,
        width: sanitizedManifest.resolution.width,
        height: sanitizedManifest.resolution.height,
      };

      console.log(`⏳ Renderizando frames do MP4 (Codec H.264)...`);
      await renderMedia({
        composition: updatedComposition,
        serveUrl: bundled,
        codec: "h264",
        outputLocation: resolvedOutput,
        inputProps: { manifest: sanitizedManifest },
      });

      console.log(`✅ Arquivo de vídeo MP4 binário gerado com sucesso!`);
      renderSuccess = true;
    } catch (err) {
      console.error(`⚠️ Falha ao renderizar MP4 via Remotion Chromium: ${(err as Error).message}`);
      console.log(`ℹ️  Gerando manifesto de mídia no arquivo de saída...`);
      const summary = [
        `Motion Quest Video Render Artifact`,
        `Projeto: ${manifest.title} (${manifest.projectId})`,
        `Cenas: ${manifest.scenes.length}`,
        `Duração: ${manifest.totalDurationSeconds}s`,
        `Resolução: ${manifest.resolution.width}x${manifest.resolution.height}`,
        `Gerado em: ${new Date().toISOString()}`
      ].join("\n");
      await fs.writeFile(resolvedOutput, summary, "utf-8");
    }

    // 3. Gerar Player HTML Interativo e Cinematográfico
    const playerHtmlPath = path.join(outDir, "player.html");
    const playerHtml = this._generateInteractivePlayer(manifest);
    await fs.writeFile(playerHtmlPath, playerHtml, "utf-8");

    console.log(`💾 Arquivo de vídeo em: ${resolvedOutput}`);
    console.log(`🌐 Player visual animado pronto em: ${playerHtmlPath}`);
    console.log(`✨ Renderização concluída!`);
    return resolvedOutput;
  }

  private _generateInteractivePlayer(manifest: VideoManifest): string {
    const scenesWithRelativePaths = manifest.scenes.map(s => ({
      ...s,
      imagePath: s.imagePath && s.imagePath.includes("/output/run/") 
        ? "../../output/run/" + s.imagePath.split("/output/run/")[1]
        : (s.imagePath || ""),
      clipPath: s.clipPath && s.clipPath.includes("/output/run/")
        ? "../../output/run/" + s.clipPath.split("/output/run/")[1]
        : (s.clipPath || "")
    }));

    const charactersWithRelativePaths = manifest.characters.map(c => ({
      ...c,
      headshotPath: c.headshotPath && c.headshotPath.includes("/output/run/")
        ? "../../output/run/" + c.headshotPath.split("/output/run/")[1]
        : c.headshotPath,
      fullbodyPath: c.fullbodyPath && c.fullbodyPath.includes("/output/run/")
        ? "../../output/run/" + c.fullbodyPath.split("/output/run/")[1]
        : c.fullbodyPath
    }));

    const scenesJson = JSON.stringify(scenesWithRelativePaths);
    const charactersJson = JSON.stringify(charactersWithRelativePaths);
    const title = manifest.title;

    return `<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Motion Quest — ${title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #060913;
      color: #f8fafc;
      font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 24px 16px;
    }
    .header {
      text-align: center;
      margin-bottom: 20px;
    }
    .header h1 {
      font-size: 26px;
      font-weight: 800;
      background: linear-space, linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }
    .header p {
      font-size: 14px;
      color: #94a3b8;
    }
    /* 9:16 Vertical Video Frame */
    .video-frame {
      width: 380px;
      height: 675px;
      max-width: 92vw;
      max-height: 82vh;
      background: #000;
      border-radius: 32px;
      overflow: hidden;
      position: relative;
      box-shadow: 0 30px 80px rgba(0, 0, 0, 0.9), 0 0 0 2px rgba(255, 255, 255, 0.08);
      display: flex;
      flex-direction: column;
    }
    .scene-canvas {
      width: 100%;
      height: 100%;
      position: relative;
      background: #090d16;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .scene-img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      position: absolute;
      inset: 0;
      opacity: 0;
      transform: scale(1.0);
      transition: opacity 0.6s ease-in-out, transform 5.5s cubic-bezier(0.25, 1, 0.5, 1);
    }
    .scene-img.active {
      opacity: 1;
    }
    .scene-img.animating {
      transform: scale(1.10) translateY(-10px);
    }
    .vignette {
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 25%, rgba(0,0,0,0.15) 60%, rgba(0,0,0,0.92) 100%);
      pointer-events: none;
      z-index: 5;
    }
    /* Top Bar: Progress Bars (Stories Style) + Badges */
    .top-section {
      position: absolute;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      z-index: 10;
    }
    .stories-bars {
      display: flex;
      gap: 4px;
      width: 100%;
      height: 4px;
    }
    .story-bar-segment {
      flex: 1;
      height: 100%;
      background: rgba(255, 255, 255, 0.25);
      border-radius: 2px;
      overflow: hidden;
      position: relative;
    }
    .story-bar-fill {
      height: 100%;
      background: #38bdf8;
      width: 0%;
      border-radius: 2px;
      transition: width 0.1s linear;
    }
    .story-bar-segment.done .story-bar-fill {
      width: 100%;
    }
    .top-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .badge {
      background: rgba(15, 23, 42, 0.82);
      backdrop-filter: blur(14px);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.5px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .char-badge {
      color: #38bdf8;
      border-color: rgba(56, 189, 248, 0.35);
    }
    .char-badge img {
      width: 22px;
      height: 22px;
      border-radius: 50%;
      object-fit: cover;
      border: 1px solid #38bdf8;
    }
    /* Subtitle Overlay */
    .subtitle-box {
      position: absolute;
      bottom: 24px;
      left: 16px;
      right: 16px;
      background: rgba(10, 15, 29, 0.85);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 22px;
      padding: 16px 20px;
      box-shadow: 0 15px 40px rgba(0,0,0,0.6);
      z-index: 10;
    }
    .subtitle-text {
      font-size: 15px;
      line-height: 1.5;
      font-weight: 600;
      text-align: center;
      color: #ffffff;
      letter-spacing: 0.2px;
    }
    /* Controls Bar */
    .controls {
      display: flex;
      gap: 12px;
      margin-top: 18px;
      align-items: center;
    }
    button {
      background: #1e293b;
      color: #f8fafc;
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 10px 18px;
      border-radius: 20px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    }
    button:hover {
      background: #334155;
      transform: translateY(-1px);
    }
    button.primary {
      background: #38bdf8;
      color: #090d16;
      border: none;
    }
    button.primary:hover {
      background: #7dd3fc;
    }
    /* Detail Prompt Box (Collapsible) */
    .prompt-preview {
      width: 380px;
      max-width: 92vw;
      margin-top: 14px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.08);
      padding: 14px 16px;
      border-radius: 16px;
      font-size: 12px;
      color: #94a3b8;
      line-height: 1.5;
    }
    .prompt-preview strong {
      color: #cbd5e1;
      display: block;
      margin-bottom: 4px;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🎬 ${title}</h1>
    <p>${manifest.scenes.length} cenas • ${manifest.totalDurationSeconds}s • Resolução 1080x1920 (9:16)</p>
  </div>

  <div class="video-frame" id="videoFrame" onclick="togglePlay()">
    <div class="vignette"></div>

    <div class="top-section">
      <div class="stories-bars" id="storiesBars"></div>
      <div class="top-meta">
        <span class="badge" id="sceneBadge">Cena 1 / ${manifest.scenes.length}</span>
        <span class="badge char-badge" id="charBadge">
          <span id="charAvatar">👤</span>
          <span id="charName">Cleber</span>
        </span>
      </div>
    </div>

    <div class="scene-canvas" id="sceneCanvas">
      <!-- Imagens de cena serão injetadas e animadas aqui -->
    </div>

    <div class="subtitle-box">
      <p class="subtitle-text" id="subtitleText">Iniciando jornada...</p>
    </div>
  </div>

  <div class="controls">
    <button onclick="prevScene(event)">⏮️ Anterior</button>
    <button onclick="togglePlay(event)" id="playBtn" class="primary">⏸️ Pausar</button>
    <button onclick="nextScene(event)">⏭️ Próxima</button>
    <button onclick="toggleAudio(event)" id="audioBtn">🔊 Voz</button>
  </div>

  <div class="prompt-preview">
    <strong>Prompt Visual da Cena:</strong>
    <p id="promptDetailText"></p>
  </div>

  <script>
    const scenes = ${scenesJson};
    const characters = ${charactersJson};
    let currentIndex = 0;
    let isPlaying = true;
    let voiceEnabled = false;
    const sceneDuration = 5000;
    let elapsed = 0;
    let intervalId = null;

    // Constrói as barras de progresso (Stories)
    const storiesBarsContainer = document.getElementById('storiesBars');
    scenes.forEach((_, idx) => {
      const seg = document.createElement('div');
      seg.className = 'story-bar-segment';
      seg.id = 'story-segment-' + idx;
      const fill = document.createElement('div');
      fill.className = 'story-bar-fill';
      fill.id = 'story-fill-' + idx;
      seg.appendChild(fill);
      storiesBarsContainer.appendChild(seg);
    });

    function renderScene(index) {
      if (index < 0) index = 0;
      if (index >= scenes.length) index = 0;
      currentIndex = index;

      const scene = scenes[currentIndex];
      document.getElementById('sceneBadge').textContent = 'Cena ' + scene.sceneNumber + ' / ' + scenes.length;
      document.getElementById('subtitleText').textContent = scene.narrationText;
      document.getElementById('promptDetailText').textContent = scene.visualPrompt;

      // Atualiza Personagem
      const char = characters.find(c => (scene.characterIds || []).includes(c.id)) || characters[0];
      if (char) {
        document.getElementById('charName').textContent = char.name;
        if (char.headshotPath) {
          document.getElementById('charAvatar').innerHTML = '<img src="' + char.headshotPath + '" alt="' + char.name + '">';
        } else {
          document.getElementById('charAvatar').textContent = '👤';
        }
      }

      // Renderiza Imagem com Ken-Burns Zoom
      const canvas = document.getElementById('sceneCanvas');
      canvas.innerHTML = '';
      
      const img = document.createElement('img');
      img.className = 'scene-img';
      img.src = scene.imagePath;
      img.alt = 'Cena ' + scene.sceneNumber;
      
      img.onload = () => {
        img.classList.add('active');
        setTimeout(() => img.classList.add('animating'), 50);
      };
      img.onerror = () => {
        // Fallback elegante com gradiente cósmico
        canvas.innerHTML = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#38bdf8;padding:24px;text-align:center;"><div style="font-size:48px;margin-bottom:12px;">🚀</div><h3 style="font-size:18px;">Cena ' + scene.sceneNumber + '</h3><p style="color:#94a3b8;font-size:13px;margin-top:6px;">' + scene.narrationText + '</p></div>';
      };
      canvas.appendChild(img);

      // Narração por Voz (Web Speech API)
      if (voiceEnabled && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(scene.narrationText);
        utter.lang = 'pt-BR';
        utter.rate = 1.05;
        window.speechSynthesis.speak(utter);
      }

      elapsed = 0;
      updateBars();
    }

    function updateBars() {
      scenes.forEach((_, idx) => {
        const seg = document.getElementById('story-segment-' + idx);
        const fill = document.getElementById('story-fill-' + idx);
        if (idx < currentIndex) {
          seg.className = 'story-bar-segment done';
          fill.style.width = '100%';
        } else if (idx === currentIndex) {
          seg.className = 'story-bar-segment';
          const pct = Math.min(100, (elapsed / sceneDuration) * 100);
          fill.style.width = pct + '%';
        } else {
          seg.className = 'story-bar-segment';
          fill.style.width = '0%';
        }
      });
    }

    function tick() {
      if (!isPlaying) return;
      elapsed += 100;
      updateBars();
      if (elapsed >= sceneDuration) {
        if (currentIndex < scenes.length - 1) {
          renderScene(currentIndex + 1);
        } else {
          renderScene(0);
        }
      }
    }

    function togglePlay(e) {
      if (e) e.stopPropagation();
      isPlaying = !isPlaying;
      document.getElementById('playBtn').textContent = isPlaying ? '⏸️ Pausar' : '▶️ Reproduzir';
    }

    function nextScene(e) {
      if (e) e.stopPropagation();
      renderScene(currentIndex + 1);
    }

    function prevScene(e) {
      if (e) e.stopPropagation();
      renderScene(currentIndex - 1);
    }

    function toggleAudio(e) {
      if (e) e.stopPropagation();
      voiceEnabled = !voiceEnabled;
      document.getElementById('audioBtn').textContent = voiceEnabled ? '🔊 Voz Ativa' : '🔇 Sem Voz';
      if (voiceEnabled) {
        renderScene(currentIndex);
      } else if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    }

    renderScene(0);
    intervalId = setInterval(tick, 100);
  </script>
</body>
</html>`;
  }
}
