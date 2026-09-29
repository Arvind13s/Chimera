import { getCategories, getVoices, streamGenerate } from './api.js';
import { getCurrentUser, openAuthModal, onAuthChange } from './auth.js';
import { renderPipelineProgress } from './pipeline.js';

const el = (id) => document.getElementById(id);

const SAMPLE_TOPICS = [
  'Deep Ocean Mysteries',
  'Quantum Computing Explained',
  'Cyberpunk Cities of 2099',
  'The Roman Empire Secrets',
  'Artificial Superintelligence',
  'Space Colonization & Mars',
];

let categories = {};
let messageCount = 0;
let generating = false;

function populateCategorySelect() {
  const select = el('category-select');
  select.innerHTML = '<option value="">Any random category</option>' +
    Object.keys(categories).map((cat) => `<option value="${cat}">${cat}</option>`).join('');
}

function updateNicheSelect() {
  const category = el('category-select').value;
  const wrap = el('niche-wrap');
  const select = el('niche-select');

  if (!category) {
    wrap.classList.add('hidden');
    select.innerHTML = '';
    return;
  }

  const niches = categories[category] || [];
  wrap.classList.remove('hidden');
  select.innerHTML = `<option value="">Random niche in ${category}</option>` +
    niches.map((n) => `<option value="${n}">${n}</option>`).join('');
}

function renderTopicChips() {
  el('topic-chips').innerHTML = SAMPLE_TOPICS.map((topic) => `
    <button type="button" class="topic-chip text-[11px] px-2 py-1 rounded-md transition-colors duration-200"
            style="background: var(--bay-black); border: 1px solid var(--bay-border); color: var(--text-secondary);"
            data-topic="${topic}">${topic}</button>
  `).join('');

  el('topic-chips').querySelectorAll('[data-topic]').forEach((btn) => {
    btn.addEventListener('click', () => {
      el('custom-topic').value = btn.dataset.topic;
    });
  });
}

function setGeneratingUI(isGenerating) {
  generating = isGenerating;
  const btn = el('generate-submit');
  const tally = el('settings-tally');

  btn.disabled = isGenerating;
  btn.innerHTML = isGenerating
    ? `<span class="flex items-center justify-center gap-3"><span class="spinner"></span>Rendering…</span>`
    : 'Start rendering';

  tally.classList.toggle('hidden', !isGenerating);
  el('log-tally').classList.toggle('tally-light--active', isGenerating);
  el('log-tally').setAttribute('aria-label', isGenerating ? 'Pipeline running' : 'Pipeline idle');
}

function appendLogMessage(message) {
  const body = el('log-body');
  const idle = el('log-idle');
  if (idle) idle.remove();

  messageCount += 1;
  const color = message.includes('✅') ? 'var(--status-success)'
    : message.includes('❌') ? 'var(--status-error)'
    : message.includes('Stage') ? 'var(--scope-teal-light)'
    : 'var(--text-primary)';

  const line = document.createElement('div');
  line.className = 'fade-in flex items-start gap-2';
  line.innerHTML = `
    <span class="text-[11px] select-none flex-shrink-0" style="color: var(--text-muted); opacity: 0.5;">${String(messageCount).padStart(2, '0')}</span>
    <span style="color: ${color};"></span>
  `;
  line.querySelector('span:last-child').textContent = message;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
}

function resetLog() {
  messageCount = 0;
  el('log-body').innerHTML = `
    <div id="log-idle" class="flex items-center h-full min-h-[180px]">
      <span style="color: var(--text-muted);"><span class="cursor-blink">▌</span></span>
    </div>
  `;
}

function renderVideoOutput(videoPath, metadata) {
  const container = el('video-output');
  if (!videoPath) {
    container.innerHTML = '';
    container.classList.add('hidden');
    return;
  }
  container.classList.remove('hidden');

  const tagsHTML = (metadata?.tags || []).map((tag) => `
    <span class="text-xs px-2 py-0.5 rounded-md font-mono" style="background: var(--bay-black); color: var(--text-secondary); border: 1px solid var(--bay-border);">${tag}</span>
  `).join('');

  container.innerHTML = `
    <div class="surface p-6" style="border-color: var(--scope-teal);">
      <div class="flex items-center justify-between mb-5">
        <div class="flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <h3 class="text-base font-semibold" style="color: var(--text-primary);">Video ready</h3>
        </div>
        <span class="text-xs font-mono px-2.5 py-1 rounded-md flex items-center gap-1.5" style="background: var(--scope-teal-soft); color: var(--scope-teal-light); border: 1px solid var(--scope-teal);" title="Standard Shorts & Reels format (1080×1920 Full HD)">
          <svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="5" y="2" width="14" height="20" rx="3"></rect>
            <path d="M12 18h.01"></path>
          </svg>
          9:16 Short & Reel
        </span>
      </div>
      <div class="flex flex-col md:flex-row gap-8 items-start">
        <!-- 9:16 Short / Reel Phone Screen Container -->
        <div class="w-full max-w-[280px] sm:w-[280px] md:w-[280px] aspect-[9/16] rounded-[24px] overflow-hidden flex-shrink-0 relative shadow-2xl mx-auto md:mx-0" style="background:#050709; border: 2.5px solid var(--bay-border-hover); box-shadow: 0 16px 40px rgba(0,0,0,0.6);">
          <!-- Top phone speaker notch pill -->
          <div class="absolute top-2.5 left-1/2 -translate-x-1/2 w-16 h-3 rounded-full bg-black/80 z-20 pointer-events-none flex items-center justify-center">
            <span class="w-2 h-2 rounded-full bg-slate-900 block mr-2"></span>
            <span class="w-6 h-1 rounded-full bg-slate-800 block"></span>
          </div>

          <!-- Format watermark tag -->
          <span class="absolute top-7 left-3 z-20 text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-gray-300 pointer-events-none">9:16 REEL</span>

          <!-- The video element itself -->
          <video src="${videoPath}" controls autoplay muted loop playsinline class="w-full h-full object-cover rounded-[21px]"></video>

          <!-- Bottom phone home indicator bar -->
          <div class="absolute bottom-1.5 left-1/2 -translate-x-1/2 w-24 h-1 rounded-full bg-white/30 z-20 pointer-events-none"></div>
        </div>
        <div class="flex-1 flex flex-col justify-between w-full min-w-0">
          ${metadata ? `
            <div class="space-y-3 mb-5">
              <div>
                <span class="text-xs font-medium mb-1 block" style="color: var(--text-label);">Title</span>
                <h4 class="font-semibold text-sm" style="color: var(--text-primary);">${metadata.title || ''}</h4>
              </div>
              <div>
                <span class="text-xs font-medium mb-1 block" style="color: var(--text-label);">Description</span>
                <p class="text-xs leading-relaxed" style="color: var(--text-secondary);">${metadata.description || ''}</p>
              </div>
              ${tagsHTML ? `<div class="flex flex-wrap gap-1.5 pt-1">${tagsHTML}</div>` : ''}
            </div>
          ` : ''}
          <div class="flex flex-col sm:flex-row gap-3">
            <a href="${videoPath}" download class="btn-primary text-sm py-3 px-6 flex-1 text-center">Download MP4</a>
            ${metadata ? `<button type="button" id="copy-metadata" class="btn-secondary text-sm py-3 px-4">Copy metadata</button>` : ''}
          </div>
        </div>
      </div>
    </div>
  `;

  if (metadata) {
    el('copy-metadata').addEventListener('click', () => {
      const text = `${metadata.title}\n\n${metadata.description}\n\n${(metadata.tags || []).join(' ')}`;
      navigator.clipboard.writeText(text);
      const btn = el('copy-metadata');
      btn.textContent = 'Copied!';
      setTimeout(() => { btn.textContent = 'Copy metadata'; }, 2000);
    });
  }
}

async function handleGenerateSubmit(e) {
  e.preventDefault();
  if (!getCurrentUser()) {
    openAuthModal();
    return;
  }
  if (generating) return;

  const niche = el('niche-select').value || '';
  const customTopic = el('custom-topic').value.trim();
  const voice = el('voice-select').value;

  setGeneratingUI(true);
  resetLog();
  renderVideoOutput(null, null);
  let currentStage = 0;
  renderPipelineProgress({ currentStage, generating: true });

  await streamGenerate(
    { niche, customTopic, voice },
    (data) => {
      if (data.message) appendLogMessage(data.message);
      if (data.stage && data.stage > 0) {
        currentStage = data.stage;
        renderPipelineProgress({ currentStage, generating: true });
      }
      if (data.video_path) {
        const filename = data.video_path.split(/[/\\]/).pop();
        renderVideoOutput(`/outputs/${filename}`, data.metadata || null);
      }
    },
    (errMessage) => appendLogMessage(`❌ ${errMessage}`),
    () => {
      setGeneratingUI(false);
      renderPipelineProgress({ currentStage, generating: false });
    }
  );
}

export async function initStudio() {
  renderTopicChips();
  renderPipelineProgress({ currentStage: 0, generating: false });
  resetLog();

  const syncAuthNote = (user) => el('auth-note').classList.toggle('hidden', !!user);
  syncAuthNote(getCurrentUser());
  onAuthChange(syncAuthNote);

  el('category-select').addEventListener('change', updateNicheSelect);
  el('generate-form').addEventListener('submit', handleGenerateSubmit);

  try {
    categories = await getCategories();
    populateCategorySelect();
  } catch {
    /* categories endpoint unreachable — leave "Any random category" only */
  }

  try {
    const voices = await getVoices();
    if (voices.length) {
      el('voice-select').innerHTML = voices.map((v) =>
        `<option value="${v}" ${v === 'Christopher (Male, US)' ? 'selected' : ''}>${v}</option>`
      ).join('');
    }
  } catch {
    /* voices endpoint unreachable — leave default option in the HTML */
  }
}
