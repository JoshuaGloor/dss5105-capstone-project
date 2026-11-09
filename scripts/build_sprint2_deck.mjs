// Build the Sprint 2 deck. Every metric is read from retained evidence JSON, never typed in.
//
//   mkdir -p .cache/deck-node && npm --prefix .cache/deck-node install pptxgenjs@3.12.0
//   node scripts/build_architecture_diagram.mjs   # only when the architecture changes; see its header
//   node scripts/build_sprint2_deck.mjs
//
// Output: docs/slides/Presentation_Group11_Sprint2.pptx (the exact upload name).
// Sources: docs/evidence/objective-study.json, docs/slides/Sprint2_Video_Script_Group11.txt (speaker
// notes), docs/slides/assets/sprint2/*.png (screenshots of the running app, and architecture.png).
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const nodeDir = process.env.PPTXGENJS_DIR || path.join(root, '.cache', 'deck-node');
const PptxGenJS = createRequire(path.join(nodeDir, 'package.json'))('pptxgenjs');
const out = path.join(root, 'docs', 'slides', 'Presentation_Group11_Sprint2.pptx');
const asset = (name) => path.join(root, 'docs', 'slides', 'assets', 'sprint2', name);

// ---- Team facts to confirm before submitting ------------------------------------------------
const GITHUB = 'github.com/JoshuaGloor/dss5105-capstone-project';
// Empty while recording, so the video shows no placeholder; set it for the deck you submit.
const DEMO_LINK = process.env.DEMO_LINK || '';
const ATTENDANCE = 'Present (in person)'; // per member below if anyone differs
// An absence needs a reason on this slide and an email to the instructors before the session.
const MEMBERS = [
  ['Chen Zepeng', 'A0156784N', ATTENDANCE], ['Duong Thanh Nhan', 'A0296326W', 'Absent: business trip to China'],
  ['Joshua Wesley Gloor', 'A0296944J', ATTENDANCE], ['Sridhar Niyanthri Rajeswari', 'A0351151U', ATTENDANCE],
  ['Sundara Rajan Saadhvika', 'A0352594W', ATTENDANCE], ['Tang Zheling', 'A0352177B', ATTENDANCE],
];
// Generated chat evaluation sets (PRs #16 and #17): behaviour-rubric passes on the first live run.
// Niyanthri: 70 train / 35 test, 67 and 34 passed. Saadhvika: 70 train / 30 test, 67 and 29 passed.
const LANGUAGE = { model: 'gpt-5.6', train: 140, test: 65, trainPassed: 134, testPassed: 63 };
// Feature, owner, status (Done / In progress / Planned). Owners agreed by the team; [TBD] rows are still open.
const EVAL_OWNERS = 'Saadhvika and Niyanthri';
const PROGRESS = [
  ['Voice assistant: speech in and out, slide to book', 'Chen Zepeng', 'Done'],
  ['Long-term memory of confirmed rules, log, profile', 'Chen Zepeng', 'Done'],
  ['Four-objective scorer, presets, objective lab', 'Chen Zepeng', 'Done'],
  ['Capacity questions and workshop checks from chat', 'Chen Zepeng', 'Done'],
  ['Chat-first desk redesign', 'Duong Thanh Nhan', 'Done'],
  ['AWS deployment behind HTTPS (demo site)', 'Joshua Wesley Gloor', 'Done'],
  ['Clarification reliability fixes and 247-assertion benchmark', 'Tang Zheling', 'In progress'],
  ['Evaluation sets: 205 requests, 140 train / 65 test', EVAL_OWNERS, 'Done'],
  ['Independent labels for the 30 inbox requests', EVAL_OWNERS, 'In progress'],
  ['Re-run the 65 test requests on the current intake (v3)', 'Tang Zheling', 'Planned'],
  ['Usability test: two people acting as dispatchers, four tasks', 'Joshua Wesley Gloor', 'Planned'],
];

// ---- Evidence ---------------------------------------------------------------------------------
const study = JSON.parse(fs.readFileSync(path.join(root, 'docs', 'evidence', 'objective-study.json'), 'utf8'));
const rows = study.report.policies;
const seeds = study.report.seeds;
const seedRange = `${seeds[0]}-${seeds[seeds.length - 1]}`;
const N = (name) => rows[name].normal;
const S = (name) => rows[name].shock;
const pct = (x, d = 2) => x.toFixed(d) + '%';
const fewer = (a, b) => Math.round((1 - a / b) * 100);
const hybrid = N('hybrid');
const ef = N('earliest_finish');
const baselines = ['random', 'greedy_biggest', 'cheapest'];
const best = (key) => baselines.reduce((a, b) => (N(a)[key] <= N(b)[key] ? a : b));
const label = { random: 'random', greedy_biggest: 'biggest capacity', cheapest: 'cheapest' };
const checks = study.course_checks;
for (const [name, key] of [['hybrid', 'lateness_beats_all_baselines'], ['defects', 'defects_beats_all_baselines'], ['fairness', 'fairness_matches_random_share']]) {
  if (!checks[name][key]) throw new Error(`Evidence no longer supports the ${name} claim; reword the deck`);
}
if (!(hybrid['% late'] < ef['% late'] && hybrid['late days'] < ef['late days'])) throw new Error('Hybrid no longer beats earliest finish');

// Speaker notes: the script file is the single source, so notes and script cannot drift.
const script = fs.readFileSync(path.join(root, 'docs', 'slides', 'Sprint2_Video_Script_Group11.txt'), 'utf8');
const sections = Object.fromEntries(script.split(/^(?=SLIDE \d+ )/m).filter((p) => p.startsWith('SLIDE')).map((p) => {
  const [heading, ...body] = p.split('Q&A PREPARATION')[0].trim().split('\n');
  return [Number(heading.match(/^SLIDE (\d+)/)[1]), heading + '\n\n' + body.join('\n').trim()];
}));
const qa = script.split('Q&A PREPARATION')[1] || '';

// ---- House style (as Sprint 1) -----------------------------------------------------------------
const C = {
  ink: '1D1B18', inkSoft: '4A463F', muted: '6B665D', paper: 'FAF8F4', card: 'FFFFFF', wash: 'F3EFE7',
  line: 'E4DDD0', camel: 'A3804C', camelText: '7D5E30', camelLight: 'CDB78F', forest: '2F5D46',
  oxblood: '8A2C35', onInk: 'F4EFE6', onInkMuted: 'C9BEAD', amber: '9A6A12',
  // Warm espresso for the dark slides and sand for emphasis cards: softer than near-black ink.
  deep: '3E342B', sand: 'F1E7D6', sandLine: 'E2D3B9',
};
const HEAD = 'Georgia';
const BODY = 'Arial';
const MONO = 'Courier New';
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Group 11';
pres.title = 'StitchFlow: Quick-Response Subcontracting Desk - Sprint 2';
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { color: C.paper },
  objects: [{ text: { text: 'STITCHFLOW  /  QUICK-RESPONSE SUBCONTRACTING DESK  /  GROUP 11  /  SPRINT 2',
    options: { x: 0.6, y: 5.25, w: 7, h: 0.22, fontFace: BODY, fontSize: 7, color: C.muted, charSpacing: 1.5, margin: 0 } } }],
  slideNumber: { x: 8.9, y: 5.25, w: 0.5, h: 0.22, fontFace: BODY, fontSize: 7, color: C.muted, align: 'right' },
});
pres.defineSlideMaster({ title: 'DARK', background: { color: C.deep } });

const T = (slide, text, opts) => slide.addText(text, { fontFace: BODY, color: C.ink, margin: 0, isTextBox: true, valign: 'top', ...opts });
// Section number before the eyebrow, after Niyanthri's redesign.
const frame = (slide, n, eyebrow, title) => {
  T(slide, [{ text: `${String(n).padStart(2, '0')}   `, options: { color: C.ink } }, { text: eyebrow }],
    { x: 0.6, y: 0.34, w: 8.8, h: 0.22, fontSize: 8.5, bold: true, color: C.camelText, charSpacing: 3 });
  T(slide, title, { x: 0.6, y: 0.58, w: 8.8, h: 0.6, fontFace: HEAD, fontSize: 23, valign: 'middle' });
};
const card = (slide, x, y, w, h, fill = C.card, line = C.line, dash) =>
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line, width: 0.75, dashType: dash } });
const kicker = (slide, text, x, y, w, color = C.muted) =>
  T(slide, text, { x, y, w, h: 0.18, fontSize: 7.5, bold: true, color, charSpacing: 1.8 });
const source = (slide, text) => T(slide, text, { x: 0.6, y: 5.0, w: 8.8, h: 0.2, fontSize: 7, italic: true, color: C.muted });
const pngSize = (file) => { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };
const image = (slide, file, x, y, h, alt, shadow = true) => {
  const [w0, h0] = pngSize(file);
  const w = h * (w0 / h0);
  slide.addImage({ path: file, x, y, w, h, altText: alt,
    ...(shadow ? { shadow: { type: 'outer', color: '000000', opacity: 0.18, blur: 10, offset: 3, angle: 90 } } : {}) });
  return w;
};
const tableCell = (text, o = {}) => ({ text, options: { fontFace: BODY, fontSize: 9, color: C.ink, valign: 'middle', margin: [2, 4, 2, 0],
  border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', color: C.line, pt: 0.75 }, { type: 'none' }], ...o } });
const tableHead = (text) => tableCell(text, { fontSize: 7, bold: true, color: C.muted, charSpacing: 1.5,
  border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', color: C.ink, pt: 1 }, { type: 'none' }] });
// Rounded cards and big numbers give each slide one place for the eye to land.
const box = (slide, x, y, w, h, { fill = C.card, line = C.line, radius = 0.08 } = {}) =>
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: radius, fill: { color: fill }, line: { color: line, width: 0.75 } });
const bar = (slide, x, y, h, color) => slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h, fill: { color }, line: { color, width: 0 } });
const stat = (slide, x, y, w, value, label, { color = C.forest, size = 30, labelColor = C.inkSoft } = {}) => {
  T(slide, value, { x, y, w, h: 0.55, fontFace: HEAD, fontSize: size, color, valign: 'bottom' });
  T(slide, label, { x, y: y + 0.6, w, h: 0.5, fontSize: 8.5, color: labelColor });
};
const notes = (slide, n, extra = []) => slide.addNotes([sections[n], ...extra].filter(Boolean).join('\n\n'));

// ---- 1. Cover ------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'SWEATERCO', { x: 0.6, y: 0.42, w: 4, h: 0.3, fontFace: HEAD, fontSize: 13, color: C.onInk, charSpacing: 9 });
  T(s, 'GROUP 11  /  TRACK 2  /  SPRINT 2 REVIEW', { x: 0.6, y: 1.0, w: 6, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'StitchFlow', { x: 0.6, y: 1.25, w: 6.2, h: 0.8, fontFace: HEAD, fontSize: 44, color: C.onInk, valign: 'middle' });
  T(s, 'The Quick-Response Subcontracting Desk', { x: 0.6, y: 2.05, w: 6.2, h: 0.36, fontFace: HEAD, fontSize: 17, color: C.onInk, valign: 'middle' });
  T(s, 'Say the order. StitchFlow finds the right workshop.', { x: 0.6, y: 2.44, w: 6.2, h: 0.36, fontFace: HEAD, fontSize: 13, italic: true, color: C.onInkMuted, valign: 'middle' });
  [['PRIMARY  ', 'MINIMISE LATENESS'], ['SECONDARY  ', 'MINIMISE DEFECTS']].forEach(([k, v], i) => {
    const x = 0.6 + i * 2.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.04, w: 2.6, h: 0.36, rectRadius: 0.18, fill: { color: C.deep }, line: { color: C.camel, width: 1 } });
    T(s, [{ text: k, options: { color: C.camel, bold: true } }, { text: v, options: { color: C.onInk, bold: true } }],
      { x, y: 3.04, w: 2.6, h: 0.36, fontSize: 8.5, charSpacing: 1.2, align: 'center', valign: 'middle' });
  });
  MEMBERS.forEach(([name, id, status], i) => {
    const x = i < 3 ? 0.6 : 3.55, y = 3.56 + (i % 3) * 0.34;
    T(s, `${name} (${id})`, { x, y, w: 2.9, h: 0.17, fontSize: 8, color: C.onInk });
    T(s, status, { x, y: y + 0.15, w: 2.9, h: 0.15, fontSize: 7, color: C.onInkMuted });
  });
  T(s, [{ text: 'GITHUB  ', options: { bold: true, color: C.camel } }, { text: GITHUB, options: { color: C.onInk } }],
    { x: 0.6, y: 4.6, w: 6.2, h: 0.2, fontSize: 8.5, charSpacing: 0.5 });
  if (DEMO_LINK) {
    T(s, [{ text: 'DEMO VIDEO  ', options: { bold: true, color: C.camel } }, { text: DEMO_LINK, options: { color: C.onInk } }],
      { x: 0.6, y: 4.84, w: 6.2, h: 0.2, fontSize: 8.5, charSpacing: 0.5 });
  }
  T(s, 'DSS5105 CAPSTONE  /  30 OCTOBER 2026', { x: 0.6, y: 5.2, w: 6, h: 0.2, fontSize: 7, color: C.onInkMuted, charSpacing: 2 });
  const [pw, ph] = pngSize(asset('phone-welcome.png'));
  image(s, asset('phone-welcome.png'), 9.45 - 4.75 * pw / ph, 0.45, 4.75, 'The dispatch assistant on a phone: a greeting, the eight workshops with their queue rings, and example requests');
  notes(s, 1);
}

// ---- 2. User, problem, and what changed ----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 2, 'OBJECTIVE AND FOCUS', 'The dispatcher decides on the factory floor, in seconds');
  box(s, 0.6, 1.3, 3.95, 1.55, { fill: C.sand, line: C.sandLine });
  bar(s, 0.6, 1.3, 1.55, C.camel);
  kicker(s, 'A REAL REQUEST FROM THE INBOX', 0.85, 1.45, 3.5, C.camelText);
  T(s, '"ORD-109, 500 vests for Harbor Knits, due Apr 13. ...and keep it away from BudgetWorks, the last batch came back rough."',
    { x: 0.85, y: 1.68, w: 3.5, h: 0.85, fontFace: HEAD, fontSize: 13.5, italic: true, color: C.ink });
  T(s, 'Mei, 09:53, request R25', { x: 0.85, y: 2.55, w: 3.5, h: 0.18, fontSize: 8, color: C.muted });
  kicker(s, 'THE USER', 0.6, 3.0, 3.95, C.camelText);
  T(s, 'The production dispatcher at SweaterCo', { x: 0.6, y: 3.18, w: 3.95, h: 0.28, fontFace: HEAD, fontSize: 14 });
  T(s, 'On the floor with a phone. Most requests are messy: missing dates, vague orders, banned workshops.',
    { x: 0.6, y: 3.47, w: 3.95, h: 0.34, fontSize: 9, color: C.inkSoft });
  ['A safe workshop, its date and why, in seconds', 'The constraint kept, and who asked recorded', 'One deliberate step to commit; a record after'].forEach((t, i) => {
    const y = 3.9 + i * 0.35;
    box(s, 0.6, y, 3.95, 0.29);
    T(s, String(i + 1), { x: 0.72, y, w: 0.2, h: 0.29, fontFace: HEAD, fontSize: 12, color: C.camel, valign: 'middle' });
    T(s, t, { x: 0.95, y, w: 3.55, h: 0.29, fontSize: 9, valign: 'middle' });
  });
  kicker(s, 'WHAT CHANGED SINCE SPRINT 1', 4.85, 1.3, 4.55);
  const tiles = [
    [`${fewer(hybrid['late days'], ef['late days'])}%`, `fewer late days than earliest finish, which tied us in Sprint 1 (${pct(hybrid['% late'])} late vs ${pct(ef['% late'])})`],
    [pct(N('defects')['% def pcs']), `defective pieces with the defects setting, vs ${pct(N('greedy_biggest')['% def pcs'])} for biggest capacity, which won in Sprint 1`],
    [pct(N('fairness')['max share'], 1), `largest workshop share with the fairness setting, vs ${pct(N('random')['max share'], 1)} for random; not tuned in Sprint 1`],
  ];
  tiles.forEach(([value, label], i) => {
    const x = 4.85 + i * 1.55;
    box(s, x, 1.52, 1.45, 1.6);
    stat(s, x + 0.14, 1.6, 1.2, value, label, { size: 26 });
  });
  [['NEW', 'Voice on the phone: answers read aloud, and one slide to book'],
    ['NEW', 'Memory: confirmed constraints come back, with who said them']].forEach(([tag, text], i) => {
    const y = 3.27 + i * 0.66;
    box(s, 4.85, y, 4.55, 0.56);
    bar(s, 4.85, y, 0.56, C.forest);
    T(s, tag, { x: 5.05, y, w: 0.5, h: 0.56, fontSize: 7.5, bold: true, color: C.forest, charSpacing: 1.5, valign: 'middle' });
    T(s, text, { x: 5.55, y, w: 3.75, h: 0.56, fontSize: 9.5, bold: true, valign: 'middle' });
  });
  source(s, `Course simulator, mean of ${seeds.length} normal runs (seeds ${seedRange}); presets chosen on development seeds first. docs/OBJECTIVE_STUDY.md`);
  notes(s, 2);
}

// ---- 3. User journey ------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 3, 'THE USER JOURNEY  /  THINK LIKE THE USER', 'Say it, check it, slide to book, and it remembers');
  const steps = [
    ['phone-welcome.png', 'Ask', 'Hold the mic: order, date and any constraint, in plain words.'],
    ['phone-answer.png', 'Answer', 'Best workshop, arrival and spare days, and why. Read aloud.'],
    ['phone-confirm.png', 'Confirm', '"Book it" opens one sheet. One slide books it, with a name on it.'],
    ['phone-receipt.png', 'Remember', 'It offers to keep the constraint for this customer.'],
    ['phone-memory.png', 'Reuse', 'Next order: the rule is applied, and the card says so.'],
  ];
  const [pw, ph] = pngSize(asset('phone-welcome.png'));
  const h = 3.0, w = h * (pw / ph), gap = (8.8 - 5 * w) / 4;
  steps.forEach(([file, title, text], i) => {
    const x = 0.6 + i * (w + gap);
    image(s, asset(file), x, 1.3, h, `${title}: ${text}`);
    T(s, String(i + 1), { x: x - 0.02, y: 4.36, w: 0.3, h: 0.32, fontFace: HEAD, fontSize: 18, color: C.camel });
    T(s, title, { x: x + 0.27, y: 4.38, w: w, h: 0.24, fontFace: HEAD, fontSize: 12 });
    T(s, text, { x: x - 0.02, y: 4.66, w: w + 0.2, h: 0.36, fontSize: 7.5, color: C.inkSoft });
  });
  source(s, 'Live screenshots of the running app (local plan, model: the one set in .env). Voice proposes; only the slide commits.');
  notes(s, 3);
}

// ---- 4. Architecture --------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 4, 'ARCHITECTURE AS BUILT', 'The model reads, Python computes, a person commits');
  // Hand-drawn diagram from scripts/build_architecture_diagram.mjs; run that first when it changes.
  const [dw, dh] = pngSize(asset('architecture.png'));
  image(s, asset('architecture.png'), 0.6 + (8.8 - 3.95 * dw / dh) / 2, 1.2, 3.95,
    'Architecture: phone app and router, LLM intake and quote check, deterministic tools, reply card, slide to confirm, ' +
    'plan ledger, memory store and course data, with the simulator and inbox evaluation', false);
  notes(s, 4);
}

// ---- 5. Key choices ---------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 5, 'KEY CHOICES', 'Each choice, against the alternative we considered');
  // The four choices the brief names (model, retrieval, data store, tools) lead, on sand cards.
  const choices = [
    ['MODEL', 'One hosted model, named in .env', 'a fine-tuned or local model', 'It only extracts quoted fields, so no training is needed; swapping it is one line.'],
    ['RETRIEVAL', 'Exact lookup by order ID', 'embedding retrieval (RAG)', 'Orders have keys; an exact match cannot fetch the wrong order.'],
    ['DATA STORE', 'SQLite for records and memory', 'a vector store', 'A rule must apply exactly, with who said it, auditable in one local file.'],
    ['TOOLS', "The course's eligible_workshops()", 'our own eligibility rule', 'Our checks and the course simulator can never disagree.'],
    ['ORCHESTRATION', 'One fixed workflow', 'a ReAct agent loop', 'Every request needs the same checks in order: testable, cheaper, no tool-choice errors.'],
    ['REPLIES', 'Python templates', 'model-written replies', 'No model arithmetic: dates and costs are copied from tool outputs.'],
    ['SPEECH', 'Browser speech recognition', 'server speech-to-text', 'Free, live words while speaking, no extra key; typing always works.'],
    ['COMMIT', 'Slide to confirm', 'booking on a spoken "yes"', 'A misheard "yes" on a noisy floor cannot send work out.'],
  ];
  const cw = (8.8 - 3 * 0.12) / 4, ch = 1.68;
  choices.forEach(([k, chose, over, because], i) => {
    const x = 0.6 + (i % 4) * (cw + 0.12), y = 1.3 + Math.floor(i / 4) * (ch + 0.12);
    const dark = i < 4;
    box(s, x, y, cw, ch, dark ? { fill: C.sand, line: C.sandLine } : {});
    if (dark) bar(s, x, y, ch, C.camel);
    kicker(s, k, x + 0.15, y + 0.13, cw - 0.3, C.camelText);
    T(s, chose, { x: x + 0.15, y: y + 0.33, w: cw - 0.3, h: 0.5, fontFace: HEAD, fontSize: 12.5, color: C.ink });
    T(s, `over ${over}`, { x: x + 0.15, y: y + 0.84, w: cw - 0.3, h: 0.2, fontSize: 8, italic: true, color: C.muted });
    T(s, because, { x: x + 0.15, y: y + 1.08, w: cw - 0.3, h: 0.52, fontSize: 8, color: C.inkSoft });
  });
  source(s, 'Highlighted: the four choices the brief asks us to justify. The model call is the only thing that leaves the machine; it never sees costs, queues or defect rates.');
  notes(s, 5);
}

// ---- 6. Progress ------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 6, 'PROGRESS SINCE THE SPRINT 1 ROADMAP', 'Every feature, its owner and its status');
  const tone = { Done: C.forest, 'In progress': C.amber, Planned: C.muted };
  const count = (status) => PROGRESS.filter((r) => r[2] === status).length;
  // Headline count, after Niyanthri's redesign, then a board with one column per status.
  T(s, [{ text: String(count('Done')), options: { color: C.forest } }, { text: `/${PROGRESS.length}` }],
    { x: 0.6, y: 1.35, w: 1.9, h: 1.0, fontFace: HEAD, fontSize: 56, valign: 'middle' });
  T(s, 'features done this sprint', { x: 0.6, y: 2.4, w: 1.9, h: 0.28, fontSize: 10.5, bold: true });
  T(s, 'Each card names its owner. Code and pull requests are linked below.', { x: 0.6, y: 2.75, w: 1.75, h: 0.5, fontSize: 8.5, color: C.inkSoft });
  const columns = [['Done', 3.4], ['In progress', 1.6], ['Planned', 1.6]];
  let x = 2.6;
  columns.forEach(([status, w]) => {
    const items = PROGRESS.filter((r) => r[2] === status);
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.3, w, h: 0.28, rectRadius: 0.14, fill: { color: tone[status] }, line: { color: tone[status], width: 0 } });
    T(s, `${status.toUpperCase()}  ${items.length}`, { x, y: 1.3, w, h: 0.28, fontSize: 8, bold: true, color: C.card, charSpacing: 1.5, align: 'center', valign: 'middle' });
    const h = status === 'Done' ? 0.42 : 0.72;
    items.forEach(([feature, owner], i) => {
      const y = 1.66 + i * (h + 0.04);
      box(s, x, y, w, h);
      bar(s, x, y, h, tone[status]);
      T(s, feature, { x: x + 0.14, y: y + 0.04, w: w - 0.2, h: h - 0.2, fontSize: 8, bold: true });
      T(s, owner, { x: x + 0.14, y: y + h - 0.17, w: w - 0.2, h: 0.14, fontSize: 7, color: owner.startsWith('[') ? C.oxblood : C.muted });
    });
    x += w + 0.1;
  });
  source(s, `Code: ${GITHUB}. PRs: #15 and #18 this sprint, #16 and #17 evaluation sets, #14 clarification reliability.`);
  notes(s, 6);
}

// ---- 7. Validation plan ----------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 7, 'VALIDATION PLAN', 'What we measure, against what, and the hard cases');
  const tw = (8.8 - 3 * 0.12) / 4;
  const heroes = [
    [pct(hybrid['% late']), `late batches (our objective), vs ${pct(ef['% late'])} for earliest finish`],
    [hybrid['late days'].toFixed(3), `mean late days, vs ${ef['late days'].toFixed(3)} for earliest finish`],
    [pct(N('defects')['% def pcs']), `defective pieces, vs ${pct(N(best('% def pcs'))['% def pcs'])} for ${label[best('% def pcs')]}`],
    [pct(100 * LANGUAGE.testPassed / LANGUAGE.test, 1), `of ${LANGUAGE.test} held-out requests passed (${LANGUAGE.testPassed}/${LANGUAGE.test}); train ${pct(100 * LANGUAGE.trainPassed / LANGUAGE.train, 1)}`],
  ];
  heroes.forEach(([value, text], i) => {
    const x = 0.6 + i * (tw + 0.12);
    box(s, x, 1.28, tw, 1.12, i === 3 ? { fill: C.sand, line: C.sandLine } : {});
    if (i === 3) bar(s, x, 1.28, 1.12, C.camel);
    stat(s, x + 0.15, 1.3, tw - 0.3, value, text, { size: 28 });
  });
  const cw = (8.8 - 2 * 0.12) / 3;
  const plan = [
    ['WHAT WE MEASURE, AND WHY', "Late batches and late days (our objective), defective pieces, largest share and the change under a closure: the course simulator's own metrics. Language: the right behaviour per request, every number traced to a tool."],
    ['HOW THE EVALUATION SET IS BUILT', `${'30'} inbox requests by kind, plus ${LANGUAGE.train + LANGUAGE.test} generated by ${EVAL_OWNERS}: ${LANGUAGE.train} to tune on, ${LANGUAGE.test} held out with new wording. Labels come from how each request was built, never from a model.`],
    ['BASELINE AND TRACK MINIMUM', 'Random, biggest capacity and cheapest, plus earliest finish. Minimum: beat all three baselines on late batches and late days, and handle all 30 inbox requests by kind.'],
  ];
  plan.forEach(([k, t], i) => {
    const x = 0.6 + i * (cw + 0.12);
    box(s, x, 2.52, cw, 1.12, { fill: C.wash, line: C.wash });
    kicker(s, k, x + 0.15, 2.62, cw - 0.3, C.camelText);
    T(s, t, { x: x + 0.15, y: 2.82, w: cw - 0.3, h: 0.78, fontSize: 8, color: C.inkSoft });
  });
  kicker(s, 'HARD CASES AND HOW WE HANDLE THEM', 0.6, 3.76, 8.8);
  const hard = [
    ['Impossible date', 'Earliest date, days late and a two-shop split; nothing is booked'],
    ['Workshop that cannot take it', 'Refused with the reason, plus the best permitted alternative'],
    ['Misheard order on the floor', 'Order, customer and pieces read back from orders.csv; a slide commits'],
  ];
  hard.forEach(([h, t], i) => {
    const x = 0.6 + i * (cw + 0.12);
    box(s, x, 3.96, cw, 0.92);
    T(s, String(i + 1), { x: x + 0.15, y: 4.02, w: 0.35, h: 0.5, fontFace: HEAD, fontSize: 26, color: C.camel });
    T(s, h, { x: x + 0.55, y: 4.08, w: cw - 0.7, h: 0.22, fontSize: 9.5, bold: true });
    T(s, t, { x: x + 0.55, y: 4.32, w: cw - 0.7, h: 0.5, fontSize: 8, color: C.inkSoft });
  });
  source(s, `Allocation: course seeds ${seedRange}, presets chosen on seeds 6000-6029 (OBJECTIVE_STUDY.md). Language: one ${LANGUAGE.model} run; a rubric pass rate, not model accuracy.`);
  notes(s, 7);
}

// ---- 8. Demo -----------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, [{ text: '08   ', options: { color: C.onInk } }, { text: 'DEMO' }], { x: 0.6, y: 0.55, w: 4, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'Charles, as the dispatcher', { x: 0.6, y: 0.8, w: 5, h: 0.6, fontFace: HEAD, fontSize: 28, color: C.onInk });
  T(s, `Presented by ${MEMBERS[0][0]} (${MEMBERS[0][1]}), who goes by Charles`, { x: 0.6, y: 1.36, w: 5, h: 0.22, fontSize: 9.5, color: C.onInkMuted });
  const demo = [
    'Says a real inbox request out loud',
    'Hears the best workshop and why',
    'Says "book it" and slides to confirm',
    'Lets it remember the constraint',
    'A new order: the rule is applied',
    'Hard case: a workshop that cannot take it, and an impossible date',
    'Behind the answer: what the model read, what Python computed',
  ];
  demo.forEach((t, i) => {
    T(s, String(i + 1), { x: 0.6, y: 1.65 + i * 0.44, w: 0.3, h: 0.32, fontFace: HEAD, fontSize: 15, color: C.camel });
    T(s, t, { x: 0.98, y: 1.69 + i * 0.44, w: 4.3, h: 0.3, fontSize: 10.5, color: C.onInk });
  });
  const [tw, th] = pngSize(asset('assistant-with-trace.png'));
  const traceH = Math.min(4.1, 3.95 * th / tw);
  image(s, asset('assistant-with-trace.png'), 5.5, 0.72 + (4.1 - traceH) / 2, traceH, 'The assistant beside its Behind the answer panel, showing a remembered rule applied to a new order');
  notes(s, 8);
}

// ---- 9. Thank you ------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'STITCHFLOW', { x: 0.6, y: 0.5, w: 4, h: 0.3, fontFace: HEAD, fontSize: 13, color: C.onInk, charSpacing: 9 });
  T(s, 'Thank you.', { x: 0.6, y: 1.6, w: 8.8, h: 0.9, fontFace: HEAD, fontSize: 40, color: C.onInk });
  T(s, 'Questions are welcome.', { x: 0.6, y: 2.5, w: 8.8, h: 0.5, fontFace: HEAD, fontSize: 18, italic: true, color: C.onInkMuted });
  T(s, [{ text: 'GITHUB  ', options: { bold: true, color: C.camel } }, { text: GITHUB, options: { color: C.onInk } }],
    { x: 0.6, y: 3.55, w: 8.8, h: 0.22, fontSize: 10 });
  if (DEMO_LINK) {
    T(s, [{ text: 'DEMO VIDEO  ', options: { bold: true, color: C.camel } }, { text: DEMO_LINK, options: { color: C.onInk } }],
      { x: 0.6, y: 3.85, w: 8.8, h: 0.22, fontSize: 10 });
  }
  T(s, 'SAY THE ORDER  /  PYTHON CHECKS  /  A PERSON COMMITS', { x: 0.6, y: 4.5, w: 8.8, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'GROUP 11  /  DSS5105 CAPSTONE  /  30 OCTOBER 2026', { x: 0.6, y: 5.15, w: 8.8, h: 0.2, fontSize: 7.5, color: C.onInkMuted, charSpacing: 2 });
  notes(s, 9, ['Q&A PREPARATION' + qa.replace(/\n+$/, '')]);
}

fs.mkdirSync(path.dirname(out), { recursive: true });
// pptxgenjs repeats <a:pPr> before every run of a mixed-format paragraph. The schema allows one, first;
// strip the repeats so strict PowerPoint builds open the deck without a repair prompt.
const JSZip = createRequire(path.join(nodeDir, 'package.json'))('jszip');
const zip = await JSZip.loadAsync(await pres.write({ outputType: 'nodebuffer' }));
for (const name of Object.keys(zip.files).filter((n) => /^ppt\/slides\/slide\d+\.xml$/.test(n))) {
  const xml = await zip.file(name).async('string');
  zip.file(name, xml.replace(/(<\/a:r>)<a:pPr\b[^>]*?(?:\/>|>.*?<\/a:pPr>)/g, '$1'));
}
fs.writeFileSync(out, await zip.generateAsync({ type: 'nodebuffer', compression: 'DEFLATE' }));
console.log('Saved', path.relative(root, out));
