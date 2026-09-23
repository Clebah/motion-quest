// Motion Quest — Web UI local (SPEC-003). Vanilla JS, no build step, no framework.
(() => {
  "use strict";

  const MIN_ROTEIRO_LENGTH = 20;
  const MAX_PHOTOS_PER_TYPE = 5;
  const POLL_INTERVAL_MS = 2000;

  const state = {
    characters: [],
    templates: [],
    selectedTemplateId: null,
    currentJobId: null,
    pollHandle: null,
    // Native <input type="file"> replaces its FileList on every selection instead of
    // appending to it, so picking photos "aos poucos" (a folder, then one more) would
    // silently drop the earlier ones. These arrays are the real source of truth; the
    // inputs are kept in sync just so their native "N files" readout stays honest.
    pendingHeadshots: [],
    pendingFullbody: [],
  };

  const el = {
    modeBadge: document.getElementById("mode-badge"),
    characterForm: document.getElementById("character-form"),
    characterName: document.getElementById("character-name"),
    characterDescription: document.getElementById("character-description"),
    characterHeadshots: document.getElementById("character-headshots"),
    characterFullbody: document.getElementById("character-fullbody"),
    headshotsStaged: document.getElementById("headshots-staged"),
    fullbodyStaged: document.getElementById("fullbody-staged"),
    characterSubmit: document.getElementById("character-submit"),
    characterError: document.getElementById("character-error"),
    characterList: document.getElementById("character-list"),
    templateGrid: document.getElementById("template-grid"),
    roteiroTextarea: document.getElementById("roteiro-textarea"),
    roteiroCount: document.getElementById("roteiro-count"),
    generateButton: document.getElementById("generate-button"),
    generateHint: document.getElementById("generate-hint"),
    generateError: document.getElementById("generate-error"),
    progressSection: document.getElementById("progress-section"),
    progressBarFill: document.getElementById("progress-bar-fill"),
    progressMessage: document.getElementById("progress-message"),
    resultSection: document.getElementById("result-section"),
    resultVideo: document.getElementById("result-video"),
    resultDownload: document.getElementById("result-download"),
  };

  function showError(node, message) {
    node.textContent = message;
    node.hidden = !message;
  }

  async function loadMode() {
    try {
      const res = await fetch("/api/mode");
      const data = await res.json();
      el.modeBadge.textContent = data.isLive ? "⚡ Modo LIVE (Gemini)" : "🧪 Modo MOCK (offline)";
      el.modeBadge.className = "badge " + (data.isLive ? "badge--live" : "badge--mock");
    } catch (err) {
      el.modeBadge.textContent = "Modo indisponível";
    }
  }

  async function loadTemplates() {
    const res = await fetch("/api/templates");
    state.templates = await res.json();
    renderTemplates();
  }

  function renderTemplates() {
    el.templateGrid.innerHTML = "";
    for (const tpl of state.templates) {
      const card = document.createElement("div");
      card.className = "template-card" + (tpl.id === state.selectedTemplateId ? " selected" : "");
      card.innerHTML = `
        <div class="genre">${tpl.genre}</div>
        <div class="title">${tpl.title}</div>
        <div class="synopsis">${tpl.synopsis}</div>
      `;
      card.addEventListener("click", () => selectTemplate(tpl));
      el.templateGrid.appendChild(card);
    }
  }

  function selectTemplate(tpl) {
    state.selectedTemplateId = tpl.id;
    el.roteiroTextarea.value = tpl.promptText;
    renderTemplates();
    updateRoteiroCount();
    updateGenerateButtonState();
  }

  async function loadCharacters() {
    const res = await fetch("/api/characters");
    state.characters = await res.json();
    renderCharacters();
    updateGenerateButtonState();
  }

  function renderCharacters() {
    el.characterList.innerHTML = "";
    for (const c of state.characters) {
      const card = document.createElement("div");
      card.className = "character-card";
      card.innerHTML = `
        <button type="button" class="remove-btn" title="Remover" data-id="${c.id}">×</button>
        <img src="${c.headshotPreviewUrl}" alt="${c.name}">
        <div class="name">${c.name}</div>
      `;
      card.querySelector(".remove-btn").addEventListener("click", () => removeCharacter(c.id));
      el.characterList.appendChild(card);
    }
  }

  async function removeCharacter(id) {
    await fetch(`/api/characters/${id}`, { method: "DELETE" });
    await loadCharacters();
  }

  function filesToFileList(files) {
    const dt = new DataTransfer();
    files.forEach((f) => dt.items.add(f));
    return dt.files;
  }

  function fileKey(file) {
    return `${file.name}__${file.size}__${file.lastModified}`;
  }

  // Merges a fresh selection from the OS file picker into the accumulated list for
  // that photo type, instead of replacing it — this is what lets the user add photos
  // one folder / one file at a time.
  function handlePhotoInputChange(inputEl, pendingKey, stagedListEl) {
    const existingKeys = new Set(state[pendingKey].map(fileKey));
    const incoming = Array.from(inputEl.files).filter((f) => !existingKeys.has(fileKey(f)));
    const merged = [...state[pendingKey], ...incoming];

    const overflow = merged.length - MAX_PHOTOS_PER_TYPE;
    state[pendingKey] = merged.slice(0, MAX_PHOTOS_PER_TYPE);
    inputEl.files = filesToFileList(state[pendingKey]);
    renderStagedFiles(stagedListEl, pendingKey);
    updateGenerateButtonState();

    if (overflow > 0) {
      showError(el.characterError, `Máximo de ${MAX_PHOTOS_PER_TYPE} fotos por tipo — ${overflow} foto(s) extra(s) não foram adicionadas.`);
    }
  }

  function renderStagedFiles(listEl, pendingKey) {
    listEl.innerHTML = "";
    state[pendingKey].forEach((file, idx) => {
      const chip = document.createElement("span");
      chip.className = "file-chip";
      chip.innerHTML = `${file.name} <button type="button" aria-label="Remover ${file.name}">×</button>`;
      chip.querySelector("button").addEventListener("click", () => removeStagedFile(pendingKey, idx));
      listEl.appendChild(chip);
    });
  }

  function removeStagedFile(pendingKey, idx) {
    state[pendingKey].splice(idx, 1);
    const inputEl = pendingKey === "pendingHeadshots" ? el.characterHeadshots : el.characterFullbody;
    const stagedListEl = pendingKey === "pendingHeadshots" ? el.headshotsStaged : el.fullbodyStaged;
    inputEl.files = filesToFileList(state[pendingKey]);
    renderStagedFiles(stagedListEl, pendingKey);
  }

  function resetCharacterFormState() {
    el.characterForm.reset();
    state.pendingHeadshots = [];
    state.pendingFullbody = [];
    el.characterHeadshots.value = "";
    el.characterFullbody.value = "";
    renderStagedFiles(el.headshotsStaged, "pendingHeadshots");
    renderStagedFiles(el.fullbodyStaged, "pendingFullbody");
  }

  async function submitCharacterForm(evt) {
    evt.preventDefault();
    showError(el.characterError, "");

    if (state.pendingHeadshots.length === 0 || state.pendingFullbody.length === 0) {
      showError(el.characterError, "Adicione ao menos 1 foto de rosto e 1 foto de corpo inteiro.");
      return;
    }

    const formData = new FormData();
    formData.append("name", el.characterName.value.trim());
    formData.append("description", el.characterDescription.value.trim());
    for (const file of state.pendingHeadshots) formData.append("headshots", file);
    for (const file of state.pendingFullbody) formData.append("fullbody", file);

    el.characterSubmit.disabled = true;
    try {
      const res = await fetch("/api/characters", { method: "POST", body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Erro ao cadastrar personagem (HTTP ${res.status})`);
      }
      resetCharacterFormState();
      await loadCharacters();
    } catch (err) {
      showError(el.characterError, err.message);
    } finally {
      el.characterSubmit.disabled = false;
    }
  }

  function updateRoteiroCount() {
    const len = el.roteiroTextarea.value.trim().length;
    el.roteiroCount.textContent = `${len} caracteres` + (len < MIN_ROTEIRO_LENGTH ? ` (mínimo ${MIN_ROTEIRO_LENGTH})` : "");
  }

  function updateGenerateButtonState() {
    const hasCharacters = state.characters.length >= 1;
    const roteiroOk = el.roteiroTextarea.value.trim().length >= MIN_ROTEIRO_LENGTH;

    if (!hasCharacters) {
      el.generateHint.textContent = "Cadastre ao menos um personagem primeiro.";
    } else if (!roteiroOk) {
      el.generateHint.textContent = `Escreva ou escolha um roteiro (mínimo ${MIN_ROTEIRO_LENGTH} caracteres).`;
    } else {
      el.generateHint.textContent = "";
    }

    el.generateButton.disabled = !(hasCharacters && roteiroOk) || state.currentJobId !== null;
  }

  async function startGeneration() {
    showError(el.generateError, "");
    el.resultSection.hidden = true;

    const payload = {
      characterIds: state.characters.map((c) => c.id),
      roteiro: el.roteiroTextarea.value.trim(),
    };

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (res.status === 409) {
          throw new Error("Já existe uma geração em andamento. Aguarde terminar.");
        }
        throw new Error(body.detail || `Erro ao iniciar geração (HTTP ${res.status})`);
      }

      state.currentJobId = body.jobId;
      updateGenerateButtonState();
      el.progressSection.hidden = false;
      pollJobStatus();
    } catch (err) {
      showError(el.generateError, err.message);
    }
  }

  function pollJobStatus() {
    if (state.pollHandle) clearInterval(state.pollHandle);

    const tick = async () => {
      const jobId = state.currentJobId;
      if (!jobId) return;

      const res = await fetch(`/api/jobs/${jobId}`);
      if (!res.ok) return;
      const job = await res.json();

      renderProgress(job);

      if (job.status === "completed" || job.status === "failed") {
        clearInterval(state.pollHandle);
        state.pollHandle = null;
        state.currentJobId = null;
        updateGenerateButtonState();

        if (job.status === "completed") {
          el.resultVideo.src = job.videoUrl;
          el.resultDownload.href = job.videoUrl;
          el.resultSection.hidden = false;
        } else {
          showError(el.generateError, job.error || "A geração falhou.");
        }
      }
    };

    tick();
    state.pollHandle = setInterval(tick, POLL_INTERVAL_MS);
  }

  function renderProgress(job) {
    const pct = job.sceneProgress && job.sceneProgress.total
      ? Math.round((job.sceneProgress.current / job.sceneProgress.total) * 100)
      : job.status === "completed" ? 100 : 5;
    el.progressBarFill.style.width = `${pct}%`;
    el.progressMessage.textContent = job.message || job.stage;
  }

  el.characterForm.addEventListener("submit", submitCharacterForm);
  el.characterHeadshots.addEventListener("change", () =>
    handlePhotoInputChange(el.characterHeadshots, "pendingHeadshots", el.headshotsStaged));
  el.characterFullbody.addEventListener("change", () =>
    handlePhotoInputChange(el.characterFullbody, "pendingFullbody", el.fullbodyStaged));
  el.roteiroTextarea.addEventListener("input", () => {
    updateRoteiroCount();
    updateGenerateButtonState();
  });
  el.generateButton.addEventListener("click", startGeneration);

  loadMode();
  loadTemplates();
  loadCharacters();
  updateRoteiroCount();
})();
