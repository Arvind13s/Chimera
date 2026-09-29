/**
 * Shared agent data — single source of truth for agent metadata,
 * used by the pipeline section, the studio's live progress widget,
 * and nowhere else.
 */
export const AGENTS = [
  {
    id: 'brain',
    name: 'Brain',
    role: 'Topic discovery',
    description:
      'Discovers viral topics across 60+ niches using Llama 3.3 70B via Groq.',
    tech: 'Groq · Llama 3.3 70B',
    stageId: 1,
  },
  {
    id: 'writer',
    name: 'Writer',
    role: 'Scene scripting',
    description:
      'Crafts scene-by-scene scripts with timing cues, psychological hooks, and visual search tags.',
    tech: 'Structured JSON · Scene timing',
    stageId: 2,
  },
  {
    id: 'speaker',
    name: 'Speaker',
    role: 'Narration',
    description:
      'Synthesizes neural voiceover at 24kHz using Edge-TTS with 8 voice options.',
    tech: 'Edge-TTS · Neural 24kHz',
    stageId: 3,
  },
  {
    id: 'dj',
    name: 'DJ',
    role: 'Soundtrack',
    description:
      'Sources mood-matched royalty-free music from Jamendo and Freesound APIs.',
    tech: 'Jamendo · Freesound',
    stageId: 4,
  },
  {
    id: 'eyes',
    name: 'Eyes',
    role: 'Footage',
    description:
      'Parallel search across Pexels and Pixabay for vertical HD stock footage with smart fallbacks.',
    tech: 'Pexels · Pixabay · 9:16',
    stageId: 5,
  },
  {
    id: 'editor',
    name: 'Editor',
    role: 'Post-production',
    description:
      'Composites clips, voiceover, and music into a finished 9:16 Short / Reel MP4 with audio balancing.',
    tech: 'MoviePy · 9:16 Reels & Shorts',
    stageId: 6,
  },
];

/**
 * Returns an inline SVG markup string for the given agent id.
 * All icons share a 24×24 viewBox, 1.5px stroke, and use currentColor
 * so color is controlled entirely via CSS/inline style on the parent.
 */
export function agentIconSVG(agentId, size = 24) {
  const attrs = `width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"`;

  const paths = {
    brain: `
      <circle cx="12" cy="10" r="6" />
      <path d="M9 16v1.5a3 3 0 0 0 6 0V16" />
      <line x1="12" y1="4" x2="12" y2="7" />
      <line x1="9.5" y1="10" x2="14.5" y2="10" />
      <line x1="10" y1="13" x2="14" y2="13" />
    `,
    writer: `
      <path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
    `,
    speaker: `
      <line x1="4" y1="12" x2="4" y2="12.01" />
      <line x1="8" y1="8" x2="8" y2="16" />
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="16" y1="8" x2="16" y2="16" />
      <line x1="20" y1="10" x2="20" y2="14" />
    `,
    dj: `
      <path d="M9 18V5l12-2v13" />
      <circle cx="6" cy="18" r="3" />
      <circle cx="18" cy="16" r="3" />
    `,
    eyes: `
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" />
      <circle cx="12" cy="12" r="3" />
    `,
    editor: `
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <line x1="2" y1="8" x2="22" y2="8" />
      <line x1="2" y1="16" x2="22" y2="16" />
      <line x1="6" y1="4" x2="6" y2="8" />
      <line x1="10" y1="4" x2="10" y2="8" />
      <line x1="14" y1="4" x2="14" y2="8" />
      <line x1="18" y1="4" x2="18" y2="8" />
      <line x1="6" y1="16" x2="6" y2="20" />
      <line x1="10" y1="16" x2="10" y2="20" />
      <line x1="14" y1="16" x2="14" y2="20" />
      <line x1="18" y1="16" x2="18" y2="20" />
    `,
  };

  const checkPath = `<polyline points="20 6 9 17 4 12" />`;

  const inner = agentId === 'check' ? checkPath : (paths[agentId] || '');
  return `<svg ${attrs}>${inner}</svg>`;
}
