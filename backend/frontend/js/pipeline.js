import { AGENTS, agentIconSVG } from './agents-data.js';

/**
 * Renders the "The pipeline" section — a connected horizontal
 * film-strip on desktop, a vertical timeline on mobile.
 * Ported 1:1 from PipelineSection.jsx.
 */
export function renderPipelineSection() {
  const desktop = document.getElementById('pipeline-desktop');
  const mobile = document.getElementById('pipeline-mobile');
  if (!desktop || !mobile) return;

  desktop.innerHTML = `
    <div class="flex items-center justify-center">
      ${AGENTS.map((agent, i) => `
        <div class="flex items-center flex-1 min-w-0">
          <div class="pipeline-agent flex flex-col items-center text-center w-full" data-stage="${i}">
            <div class="pipeline-agent-icon w-14 h-14 rounded-xl flex items-center justify-center mb-3 surface-interactive transition-all duration-200"
                 style="color: var(--scope-teal-light);" role="img" aria-label="${agent.name} agent">
              ${agentIconSVG(agent.id, 26)}
            </div>
            <span class="text-xs font-mono mb-0.5" style="color: var(--text-muted);">${String(agent.stageId).padStart(2, '0')}</span>
            <h3 class="text-sm font-semibold" style="color: var(--text-primary);">${agent.name}</h3>

            <div class="pipeline-agent-details">
              <span class="text-xs font-semibold mb-1 block" style="color: var(--scope-teal-light);">${agent.role}</span>
              <p class="text-xs leading-relaxed mb-2" style="color: var(--text-secondary);">${agent.description}</p>
              <span class="text-[11px] font-mono px-2 py-0.5 rounded-md inline-block" style="background: var(--bay-black); color: var(--text-muted); border: 1px solid var(--bay-border);">${agent.tech}</span>
            </div>
          </div>
          ${i < AGENTS.length - 1 ? `<div class="pipeline-line" data-line="${i}"><span class="pipeline-flow-dot"></span></div>` : ''}
        </div>
      `).join('')}
    </div>
  `;

  mobile.innerHTML = `
    <div class="relative pl-10">
      <div class="pipeline-mobile-line" aria-hidden="true"></div>
      ${AGENTS.map((agent) => `
        <div class="relative pb-10 last:pb-0">
          <div class="absolute left-[-26px] top-0 w-8 h-8 rounded-lg flex items-center justify-center"
               style="background: var(--bay-surface); border: 1px solid var(--bay-border-hover); color: var(--scope-teal-light);"
               role="img" aria-label="${agent.name} agent">
            ${agentIconSVG(agent.id, 18)}
          </div>
          <div class="surface p-5">
            <div class="flex items-center gap-3 mb-2">
              <span class="text-xs font-mono" style="color: var(--text-muted);">${String(agent.stageId).padStart(2, '0')}</span>
              <h3 class="text-sm font-semibold" style="color: var(--text-primary);">${agent.name}</h3>
              <span class="text-xs" style="color: var(--scope-teal-light);">${agent.role}</span>
            </div>
            <p class="text-xs leading-relaxed mb-3" style="color: var(--text-secondary);">${agent.description}</p>
            <span class="text-[11px] font-mono px-2 py-0.5 rounded-md inline-block" style="background: var(--bay-black); color: var(--text-muted); border: 1px solid var(--bay-border);">${agent.tech}</span>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

const checkSVG = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12" /></svg>`;

/**
 * Renders/updates the compact live pipeline progress widget inside
 * the Studio panel. Ported 1:1 from GeneratePanel.jsx's PipelineProgress.
 */
export function renderPipelineProgress({ currentStage, generating }) {
  const container = document.getElementById('pipeline-progress');
  if (!container) return;

  const statusText = generating
    ? `Stage ${currentStage} / 6`
    : currentStage >= 6 ? 'Complete' : 'Standby';
  const statusColor = generating
    ? 'var(--tally-red)'
    : currentStage >= 6 ? 'var(--scope-teal-light)' : 'var(--text-muted)';

  const nodes = AGENTS.map((agent, i) => {
    const isDone = currentStage > agent.stageId;
    const isActive = currentStage === agent.stageId && generating;

    const bg = isActive ? 'var(--tally-red-soft)' : isDone ? 'var(--scope-teal-soft)' : 'var(--bay-black)';
    const border = isActive ? 'var(--tally-red)' : isDone ? 'var(--scope-teal)' : 'var(--bay-border)';
    const color = isActive ? 'var(--tally-red)' : isDone ? 'var(--scope-teal-light)' : 'var(--text-muted)';
    const state = isActive ? 'active' : isDone ? 'complete' : 'pending';

    const connectorClass = isDone ? 'pipeline-connector--complete' : isActive ? 'pipeline-connector--active' : '';

    return `
      <div class="flex items-center flex-1 min-w-0">
        <div class="flex flex-col items-center flex-shrink-0">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center transition-colors duration-300"
               style="background: ${bg}; border: 1px solid ${border}; color: ${color};"
               role="img" aria-label="${agent.name}: ${state}">
            ${isDone ? checkSVG : agentIconSVG(agent.id, 18)}
          </div>
          <span class="text-[10px] mt-1.5 font-medium truncate max-w-[50px] text-center" style="color: ${color};">${agent.name}</span>
        </div>
        ${i < AGENTS.length - 1 ? `<div class="pipeline-connector mx-1 ${connectorClass}"></div>` : ''}
      </div>
    `;
  }).join('');

  container.innerHTML = `
    <div class="flex items-center justify-between mb-4">
      <span class="text-xs font-medium" style="color: var(--text-label);">Pipeline</span>
      <span class="text-xs font-mono" style="color: ${statusColor};">${statusText}</span>
    </div>
    <div class="flex items-center gap-0">${nodes}</div>
  `;
}
