// Build the hand-drawn architecture diagram for the Sprint 2 deck (slide 4).
//
//   npm --prefix .cache/deck-node install roughjs@4.6.6 @resvg/resvg-js@2.6.2 lucide-static@0.460.0
//   node scripts/build_architecture_diagram.mjs
//
// Output: docs/slides/assets/sprint2/architecture.png. Boxes are rough.js sketches, icons are Lucide
// (ISC licence), text is macOS Chalkboard SE. resvg renders it to PNG, so the deck needs no extra font.
// Every box is a module that exists; keep it that way when the code changes.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const nodeDir = process.env.PPTXGENJS_DIR || path.join(root, '.cache', 'deck-node');
const req = createRequire(path.join(nodeDir, 'package.json'));
const rough = req('roughjs/bundled/rough.cjs.js');
const { Resvg } = req('@resvg/resvg-js');
const ICONS = path.join(nodeDir, 'node_modules', 'lucide-static', 'icons');
const FONTS = ['/System/Library/Fonts/Supplemental/ChalkboardSE.ttc', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'];
const out = path.join(root, 'docs', 'slides', 'assets', 'sprint2', 'architecture.png');

// Units are hundredths of an inch: the diagram fills 8.8 x 3.95 in on the slide.
const W = 880;
const H = 395;
const C = {
  ink: '#1D1B18', soft: '#4A463F', muted: '#6B665D', paper: '#FAF8F4', camel: '#A3804C', camelText: '#7D5E30',
  oxblood: '#8A2C35', white: '#FFFFFF', core: '#F3E6CF', blue: '#DCE7F3', green: '#DDEBDD', lilac: '#E7DFF3',
  peach: '#F6DDCB', butter: '#F5ECCB',
};
const ARROW = ` ${String.fromCharCode(0x2192)} `;
const gen = rough.generator();
const parts = [];
let seed = 7;

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const emit = (drawable, dash) => {
  for (const p of gen.toPaths(drawable)) {
    const stroked = p.stroke && p.stroke !== 'none';
    parts.push(`<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill || 'none'}" ` +
      `stroke-linecap="round" stroke-linejoin="round"${dash && stroked ? ` stroke-dasharray="${dash}"` : ''}/>`);
  }
};
const rrect = (x, y, w, h, r) =>
  `M${x + r},${y} H${x + w - r} Q${x + w},${y} ${x + w},${y + r} V${y + h - r} Q${x + w},${y + h} ${x + w - r},${y + h} ` +
  `H${x + r} Q${x},${y + h} ${x},${y + h - r} V${y + r} Q${x},${y} ${x + r},${y} Z`;
const shape = (x, y, w, h, { fill = 'none', stroke = C.ink, width = 1.5, dash, r = 9, roughness = 1.1, single = false } = {}) =>
  emit(gen.path(rrect(x, y, w, h, r), {
    seed: seed++, stroke, strokeWidth: width, fill, fillStyle: 'solid', roughness, bowing: 0.8,
    preserveVertices: true, disableMultiStroke: single,
  }), dash);
const text = (x, y, s, { size = 9, weight = 'normal', color = C.ink, anchor = 'middle', halo = false, spacing = 0 } = {}) =>
  parts.push(`<text x="${x}" y="${y}" font-family="Chalkboard SE, Arial Unicode MS" font-size="${size}" font-weight="${weight}" ` +
    `fill="${color}" text-anchor="${anchor}"${spacing ? ` letter-spacing="${spacing}"` : ''}` +
    `${halo ? ` stroke="${C.paper}" stroke-width="3.4" stroke-linejoin="round" paint-order="stroke"` : ''}>${esc(s)}</text>`);
const icon = (name, cx, y, size = 16, color = C.ink) => {
  const svg = fs.readFileSync(path.join(ICONS, `${name}.svg`), 'utf8');
  const inner = svg.slice(svg.indexOf('>', svg.indexOf('<svg')) + 1, svg.lastIndexOf('</svg>'));
  parts.push(`<g transform="translate(${cx - size / 2},${y}) scale(${size / 24})" fill="none" stroke="${color}" ` +
    `stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">${inner}</g>`);
};
const box = (x, y, w, h, { title, lines = [], icon: name, fill = C.white, dash } = {}) => {
  shape(x, y, w, h, { fill, dash });
  icon(name, x + w / 2, y + 8);
  text(x + w / 2, y + 37, title, { size: 11.5, weight: 'bold' });
  lines.forEach((line, i) => text(x + w / 2, y + 49 + i * 10, line, { size: 8.4, color: C.soft }));
};
const layer = (x, y, w, h, label, labelX = x + w / 2) => {
  shape(x, y, w, h, { dash: '5 4', width: 1.3, r: 14, roughness: 0.9, single: true });
  text(labelX, y + 14, label, { size: 10.5, weight: 'bold', spacing: 0.8 });
};
const arrow = (pts, { label, at, dash, color = C.ink } = {}) => {
  const opts = { seed: seed++, stroke: color, strokeWidth: 1.4, roughness: 0.8, bowing: 1, disableMultiStroke: !!dash };
  emit(pts.length > 2 ? gen.curve(pts, opts) : gen.line(...pts[0], ...pts[1], opts), dash);
  const [a, b] = pts.slice(-2);
  const angle = Math.atan2(b[1] - a[1], b[0] - a[0]);
  const wing = (turn) => [b[0] - 7 * Math.cos(angle + turn), b[1] - 7 * Math.sin(angle + turn)];
  emit(gen.linearPath([wing(0.45), b, wing(-0.45)], { ...opts, seed: seed++, disableMultiStroke: true }));
  if (label) text(at[0], at[1], label, { size: 8.6, color: C.soft, halo: true });
};
const chip = (x, y, label, fill) => {
  const w = label.length * 4.5 + 12;
  shape(x, y, w, 15, { fill, r: 7, width: 1.1, roughness: 0.7 });
  text(x + w / 2, y + 10.8, label, { size: 7.8 });
  return w;
};

// ---- Top row: input, understanding, output ----------------------------------------------------
layer(0, 0, 250, 112, 'INPUT');
box(10, 24, 108, 78, { title: 'Phone app', icon: 'mic', lines: ['hold to talk, or type', 'speech to text in browser'] });
box(140, 24, 100, 78, { title: 'Router', icon: 'git-fork', lines: ['commands, memory and', 'workshop questions:', 'no model'] });
arrow([[118, 63], [140, 63]]);

layer(285, 0, 270, 112, 'UNDERSTAND');
box(295, 24, 122, 78, { title: 'LLM intake', icon: 'sparkles', fill: C.blue, dash: '4 3',
  lines: ['one structured-output', 'call: a typed patch'] });
box(435, 24, 110, 78, { title: 'Quote check', icon: 'quote', lines: ['every field must quote', 'the message, or Python', 'rejects it'] });
arrow([[417, 63], [435, 63]]);
arrow([[240, 63], [295, 63]], { label: 'the rest', at: [267, 82] });
text(356, 125, 'the only call that leaves the machine', { size: 8.2, color: C.oxblood });

layer(590, 0, 290, 112, 'OUTPUT');
box(600, 24, 130, 78, { title: 'Reply card + voice', icon: 'message-square-text', fill: C.green,
  lines: ['a Python template;', 'numbers copied from tools'] });
box(742, 24, 128, 78, { title: 'Behind the answer', icon: 'list-checks', lines: ['what the model read,', 'what Python computed'] });

// ---- Middle row: the human gate, the deterministic core, evaluation ---------------------------
box(10, 150, 160, 92, { title: 'Slide to confirm', icon: 'hand', fill: C.peach,
  lines: ['"book it" opens one sheet;', 'name + slide, recomputed,', 'refused if anything changed'] });
arrow([[172, 102], [152, 124], [128, 150]], { label: '"book it"', at: [190, 132] });

shape(205, 140, 410, 122, { stroke: C.camel, width: 2.6, r: 16, roughness: 0.9 });
shape(211, 146, 398, 110, { fill: C.core, stroke: C.camel, width: 1.2, r: 12, roughness: 0.9, single: true });
icon('workflow', 410, 153, 20, C.camelText);
text(410, 190, 'Deterministic tools', { size: 15, weight: 'bold' });
text(410, 205, ['order lookup', 'remembered rules', 'eligibility', 'estimates', 'rank'].join(ARROW), { size: 9, color: C.soft });
const chips = [['orders.csv', C.green], ['eligible_workshops()', C.blue], ['estimates', C.butter], ['5 weights', C.peach],
  ['split', C.lilac]];
const chipW = chips.reduce((sum, [label]) => sum + label.length * 4.5 + 12, 0) + 6 * (chips.length - 1);
chips.reduce((x, [label, fill]) => x + chip(x, 214, label, fill) + 6, 410 - chipW / 2);
text(410, 245, 'weights from the Priorities sliders; the model never sees costs or queues', { size: 8, color: C.muted });

arrow([[490, 102], [482, 124], [470, 146]], { label: 'typed patch', at: [526, 128] });
arrow([[600, 146], [628, 126], [660, 104]], { label: 'ranked options', at: [700, 126] });
arrow([[170, 196], [205, 196]], { dash: '4 3', label: 'recompute', at: [187, 214] });

layer(648, 135, 232, 127, 'EVALUATION');
box(656, 157, 104, 96, { title: 'Simulator', icon: 'gauge', lines: ['simulate.py, normal', 'and with a closure,', 'vs 3 baselines'] });
box(768, 157, 104, 96, { title: 'Inbox eval', icon: 'clipboard-check', lines: ['30 inbox requests', '+ 50 held-out,', 'labelled apart'] });
arrow([[648, 198], [616, 198]], { dash: '4 3', label: 'replays', at: [632, 214] });

// ---- Bottom row: what the tools read and what a booking writes --------------------------------
layer(0, 285, 615, 110, 'KNOWLEDGE', 432);
box(10, 307, 180, 78, { title: 'Plan ledger', icon: 'database', lines: ['bookings + reserved capacity', 'SQLite (records.py)'] });
box(215, 307, 180, 78, { title: 'Memory store', icon: 'brain', fill: C.lilac,
  lines: ['rules from confirmed bookings,', 'with who said it (SQLite)'] });
box(420, 307, 185, 78, { title: 'Course data', icon: 'file-spreadsheet', fill: C.green,
  lines: ['orders.csv, workshops.csv', 'read only'] });
arrow([[60, 242], [60, 307]], { label: 'saves', at: [36, 276] });
arrow([[140, 242], [196, 276], [262, 308]], { label: 'learns the rule', at: [252, 270] });
arrow([[330, 307], [336, 262]], { label: 'applies rules', at: [374, 276] });
arrow([[510, 307], [502, 262]], { label: 'feeds', at: [530, 276] });

text(765, 312, 'Every number on screen', { size: 10.5, weight: 'bold', color: C.camelText });
text(765, 328, 'or in speech comes', { size: 10.5, weight: 'bold', color: C.camelText });
text(765, 344, 'from the tools,', { size: 10.5, weight: 'bold', color: C.camelText });
text(765, 360, 'never from the model.', { size: 10.5, weight: 'bold', color: C.camelText });
arrow([[700, 298], [654, 284], [624, 264]], { color: C.camel });

// A small margin keeps the outer dashed borders off the image edge.
const M = 4;
const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W + 2 * M}" height="${H + 2 * M}" viewBox="0 0 ${W + 2 * M} ${H + 2 * M}">` +
  `<rect width="100%" height="100%" fill="${C.paper}"/><g transform="translate(${M},${M})">${parts.join('')}</g></svg>`;
const png = new Resvg(svg, {
  fitTo: { mode: 'zoom', value: 3 },
  font: { fontFiles: FONTS, loadSystemFonts: false, defaultFontFamily: 'Chalkboard SE' },
}).render().asPng();
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, png);
console.log(`Saved ${path.relative(root, out)}`);
