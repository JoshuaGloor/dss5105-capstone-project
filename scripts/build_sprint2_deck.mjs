// Build the Sprint 2 deck. Every metric is read from retained evidence JSON, never typed in.
//
//   mkdir -p .cache/deck-node && npm --prefix .cache/deck-node install pptxgenjs@3.12.0
//   node scripts/build_sprint2_deck.mjs
//
// Output: docs/slides/Presentation_Group11_Sprint2.pptx (the exact upload name).
// Sources: docs/evidence/objective-study.json, docs/slides/Sprint2_Video_Script_Group11.txt (speaker
// notes), docs/slides/assets/sprint2/*.png (screenshots of the running app).
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
const DEMO_LINK = process.env.DEMO_LINK || '[YouTube link: add after upload]';
const ATTENDANCE = 'Present (in person)'; // per member below if anyone differs
const MEMBERS = [
  ['Chen Zepeng', 'A0156784N', ATTENDANCE], ['Duong Thanh Nhan', 'A0296326W', ATTENDANCE],
  ['Joshua Wesley Gloor', 'A0296944J', ATTENDANCE], ['Sridhar Niyanthri Rajeswari', 'A0351151U', ATTENDANCE],
  ['Sundara Rajan Saadhvika', 'A0352594W', ATTENDANCE], ['Tang Zheling', 'A0352177B', ATTENDANCE],
];
// Feature, owner, status (Done / In progress / Planned). Owners from git history; TBD rows need the team.
const PROGRESS = [
  ['Voice assistant: phone UI, speech in and out, slide to book', 'Chen Zepeng', 'Done'],
  ['Long-term memory: rules from confirmed bookings, log, profile', 'Chen Zepeng', 'Done'],
  ['Four-objective scorer, frozen presets, objective lab', 'Chen Zepeng', 'Done'],
  ['Capacity questions and workshop checks from chat', 'Chen Zepeng', 'Done'],
  ['Chat-first desk redesign', 'Duong Thanh Nhan', 'Done'],
  ['AWS deployment behind HTTPS (demo site)', 'Joshua Wesley Gloor', 'Done'],
  ['Clarification reliability fixes and 247-assertion benchmark', 'Tang Zheling', 'In progress'],
  ['Live run on all 30 inbox requests, two independent labellers', '[TBD]', 'In progress'],
  ['Held-out rewordings and prompt-injection items', '[TBD]', 'Planned'],
  ['Usability test: two people acting as dispatchers, four tasks', '[TBD]', 'Planned'],
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
  oxblood: '8A2C35', onInk: 'F4EFE6', onInkMuted: 'B9AF9F', amber: '9A6A12',
};
const HEAD = 'Georgia';
const BODY = 'Arial';
const MONO = 'Courier New';
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9';
pres.author = 'Group 11';
pres.title = 'Quick-Response Subcontracting Desk - Sprint 2';
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };
pres.defineSlideMaster({
  title: 'CONTENT',
  background: { color: C.paper },
  objects: [{ text: { text: 'SWEATERCO  /  QUICK-RESPONSE SUBCONTRACTING DESK  /  GROUP 11  /  SPRINT 2',
    options: { x: 0.6, y: 5.25, w: 7, h: 0.22, fontFace: BODY, fontSize: 7, color: C.muted, charSpacing: 1.5, margin: 0 } } }],
  slideNumber: { x: 8.9, y: 5.25, w: 0.5, h: 0.22, fontFace: BODY, fontSize: 7, color: C.muted, align: 'right' },
});
pres.defineSlideMaster({ title: 'DARK', background: { color: C.ink } });

const T = (slide, text, opts) => slide.addText(text, { fontFace: BODY, color: C.ink, margin: 0, isTextBox: true, valign: 'top', ...opts });
const frame = (slide, eyebrow, title) => {
  T(slide, eyebrow, { x: 0.6, y: 0.34, w: 8.8, h: 0.22, fontSize: 8.5, bold: true, color: C.camelText, charSpacing: 3 });
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
const notes = (slide, n, extra = []) => slide.addNotes([sections[n], ...extra].filter(Boolean).join('\n\n'));

// ---- 1. Cover ------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'SWEATERCO', { x: 0.6, y: 0.42, w: 4, h: 0.3, fontFace: HEAD, fontSize: 13, color: C.onInk, charSpacing: 9 });
  T(s, 'GROUP 11  /  TRACK 2  /  SPRINT 2 REVIEW', { x: 0.6, y: 1.0, w: 6, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'The Quick-Response\nSubcontracting Desk', { x: 0.6, y: 1.25, w: 6.2, h: 1.25, fontFace: HEAD, fontSize: 34, color: C.onInk, valign: 'middle' });
  T(s, 'Ravi talks. Python checks. A person commits.', { x: 0.6, y: 2.52, w: 6, h: 0.4, fontFace: HEAD, fontSize: 15, italic: true, color: C.onInkMuted });
  [['PRIMARY  ', 'MINIMISE LATENESS'], ['SECONDARY  ', 'MINIMISE DEFECTS']].forEach(([k, v], i) => {
    const x = 0.6 + i * 2.75;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 3.04, w: 2.6, h: 0.36, rectRadius: 0.18, fill: { color: C.ink }, line: { color: C.camel, width: 1 } });
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
  T(s, [{ text: 'DEMO VIDEO  ', options: { bold: true, color: C.camel } }, { text: DEMO_LINK, options: { color: C.onInk } }],
    { x: 0.6, y: 4.84, w: 6.2, h: 0.2, fontSize: 8.5, charSpacing: 0.5 });
  T(s, 'DSS5105 CAPSTONE  /  30 OCTOBER 2026', { x: 0.6, y: 5.2, w: 6, h: 0.2, fontSize: 7, color: C.onInkMuted, charSpacing: 2 });
  image(s, asset('phone-welcome.png'), 7.15, 0.45, 4.75, 'The dispatch assistant on a phone: a greeting, the eight workshops with their queue rings, and example requests');
  notes(s, 1);
}

// ---- 2. User, problem, and what changed ----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'OBJECTIVE AND FOCUS', 'Ravi decides on the factory floor, in seconds');
  card(s, 0.6, 1.35, 3.85, 1.15);
  kicker(s, 'THE USER', 0.8, 1.47, 3.4, C.camelText);
  T(s, 'Ravi, production dispatcher at SweaterCo', { x: 0.8, y: 1.68, w: 3.5, h: 0.3, fontFace: HEAD, fontSize: 13.5 });
  T(s, 'On the floor with a phone, not at a desk. Requests arrive in a group chat, and most are messy: missing dates, vague orders, banned workshops.',
    { x: 0.8, y: 1.98, w: 3.5, h: 0.5, fontSize: 9, color: C.inkSoft });
  kicker(s, 'A REAL REQUEST FROM THE INBOX', 0.6, 2.68, 3.85);
  T(s, '"ORD-109, 500 vests for Harbor Knits, due Apr 13. ...and keep it away from BudgetWorks, the last batch came back rough."',
    { x: 0.6, y: 2.9, w: 3.85, h: 0.65, fontFace: HEAD, fontSize: 12, italic: true });
  kicker(s, 'WHAT HE NEEDS', 0.6, 3.68, 3.85);
  ['A safe workshop, its arrival date and why, in seconds', 'The constraint honoured, and who asked recorded', 'One deliberate step to commit; a record afterwards'].forEach((t, i) =>
    T(s, `${i + 1}   ${t}`, { x: 0.6, y: 3.9 + i * 0.27, w: 3.85, h: 0.25, fontSize: 9.5, color: C.ink }));
  kicker(s, 'WHAT CHANGED SINCE SPRINT 1', 4.85, 1.35, 4.55);
  const changes = [
    ['Earliest finish tied us on lateness', `Default beats it: ${pct(hybrid['% late'])} late vs ${pct(ef['% late'])}, ${fewer(hybrid['late days'], ef['late days'])}% fewer late days`],
    ['Biggest capacity won on defects', `Defects setting wins: ${pct(N('defects')['% def pcs'])} defective pieces vs ${pct(N('greedy_biggest')['% def pcs'])}`],
    ['Fairness not tuned', `Fairness setting: largest share ${pct(N('fairness')['max share'], 1)} vs random ${pct(N('random')['max share'], 1)}`],
    ['Typing at a desk only', 'Voice on the phone, read aloud, slide to book'],
    ['No memory between requests', 'Remembers confirmed constraints, and says when it applies one'],
  ];
  s.addTable([[tableHead('SPRINT 1'), tableHead('SPRINT 2')],
    ...changes.map(([a, b]) => [tableCell(a, { color: C.muted }), tableCell(b, { bold: true, color: C.forest })])],
  { x: 4.85, y: 1.6, w: 4.55, colW: [1.75, 2.8], rowH: [0.26, 0.5, 0.5, 0.5, 0.5, 0.5] });
  source(s, `Course simulator, mean of ${seeds.length} normal runs (seeds ${seedRange}); presets chosen on development seeds first. docs/OBJECTIVE_STUDY.md`);
  notes(s, 2);
}

// ---- 3. User journey ------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'THE USER JOURNEY  /  THINK LIKE THE USER', 'Say it, check it, slide to book, and it remembers');
  const steps = [
    ['phone-welcome.png', 'Ask', 'Hold the mic: order, date and any constraint, in his words.'],
    ['phone-answer.png', 'Answer', 'Best workshop, arrival and spare days, and why. Read aloud.'],
    ['phone-confirm.png', 'Confirm', '"Book it" opens one sheet. He slides, with his name on it.'],
    ['phone-receipt.png', 'Remember', 'It offers to keep his constraint for this customer.'],
    ['phone-memory.png', 'Reuse', 'Next order: the rule is applied, and the card says so.'],
  ];
  const h = 3.0, w = h * (336 / 692), gap = (8.8 - 5 * w) / 4;
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
  frame(s, 'ARCHITECTURE AS BUILT  /  KEY CHOICES', 'The model reads, Python computes, a person commits');
  const boxes = [
    ['PHONE APP', 'Browser', 'Speech to text, cards, voice, slide to book', 'assets/assistant', 'card'],
    ['ROUTER', 'Python', '"book it", memory and workshop questions: no model', 'assistant.py', 'card'],
    ['LLM', 'Structured output', 'Typed patch; every field must quote the message', 'intake.py', 'external'],
    ['TOOLS', 'Deterministic', 'Order lookup, remembered rules, eligibility, estimates, ranking', 'dispatch.py  allocator.py', 'core'],
    ['REPLY', 'Python template', 'Card and speech from tool strings only', 'assistant.py', 'card'],
    ['CONFIRM + STORE', 'SQLite', 'Recompute, save the record, learn the rule', 'records.py  memory.py', 'card'],
  ];
  const bw = 1.33, bh = 1.32, by = 1.42, gapX = (8.8 - 6 * bw) / 5;
  boxes.forEach(([title, kind, body, mod, style], i) => {
    const x = 0.6 + i * (bw + gapX);
    const core = style === 'core', ext = style === 'external';
    card(s, x, by, bw, bh, core ? C.ink : ext ? C.wash : C.card, core ? C.ink : ext ? C.muted : C.line, ext ? 'dash' : undefined);
    T(s, title, { x: x + 0.09, y: by + 0.08, w: bw - 0.18, h: 0.16, fontSize: 7, bold: true, charSpacing: 1.2, color: core ? C.camelLight : C.camelText });
    T(s, kind, { x: x + 0.09, y: by + 0.25, w: bw - 0.18, h: 0.2, fontFace: HEAD, fontSize: 10.5, color: core ? C.onInk : C.ink });
    T(s, body, { x: x + 0.09, y: by + 0.48, w: bw - 0.18, h: 0.6, fontSize: 7.5, color: core ? C.onInk : C.inkSoft });
    T(s, mod.replace(/  /g, '\n'), { x: x + 0.09, y: by + bh - 0.3, w: bw - 0.18, h: 0.26, fontFace: MONO, fontSize: 6.5, color: core ? C.camelLight : C.camelText, valign: 'bottom' });
    if (i < boxes.length - 1) {
      s.addShape(pres.shapes.LINE, { x: x + bw + 0.02, y: by + bh / 2, w: gapX - 0.04, h: 0, line: { color: C.ink, width: 1, endArrowType: 'triangle' } });
    }
  });
  const llmX = 0.6 + 2 * (bw + gapX);
  T(s, 'Trust boundary: the model call is the only thing that leaves the machine. It never sees costs, queues or defect rates.',
    { x: llmX - 0.6, y: by + bh + 0.06, w: bw + 1.2, h: 0.3, fontSize: 7, italic: true, color: C.muted, align: 'center' });
  kicker(s, 'KEY CHOICES, AGAINST THE ALTERNATIVE WE CONSIDERED', 0.6, 3.15, 8.8);
  const choices = [
    ['One workflow', 'A ReAct agent loop', 'Every request needs the same checks in order: testable, cheaper, no tool-choice errors'],
    ['Browser speech recognition', 'Server speech-to-text', 'Free, live words as he speaks, no extra key; typing always works'],
    ['Python templates for replies', 'Model-written replies', 'No model arithmetic: dates and costs are copied from tools'],
    ['Exact rules in SQLite', 'A vector-store memory', 'A constraint must apply exactly, with who said it, and be auditable'],
    ['Slide to confirm', 'Book on a spoken "yes"', 'A misheard "yes" on a noisy floor cannot send work out'],
  ];
  s.addTable([[tableHead('WE CHOSE'), tableHead('OVER'), tableHead('BECAUSE')],
    ...choices.map(([a, b, c]) => [tableCell(a, { bold: true }), tableCell(b, { color: C.muted }), tableCell(c, { color: C.inkSoft })])],
  { x: 0.6, y: 3.36, w: 8.8, colW: [2.0, 1.85, 4.95], rowH: [0.24, 0.27, 0.27, 0.27, 0.27, 0.27] });
  notes(s, 4);
}

// ---- 5. Progress ------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'PROGRESS SINCE THE SPRINT 1 ROADMAP', 'Every feature, its owner and its status');
  const tone = { Done: C.forest, 'In progress': C.amber, Planned: C.muted };
  s.addTable([[tableHead('FEATURE'), tableHead('OWNER'), tableHead('STATUS')],
    ...PROGRESS.map(([f, o, st]) => [tableCell(f), tableCell(o, { color: o.startsWith('[') ? C.oxblood : C.inkSoft }),
      tableCell(st, { bold: true, color: tone[st] })])],
  { x: 0.6, y: 1.32, w: 8.8, colW: [5.6, 2.0, 1.2], rowH: [0.24, ...PROGRESS.map(() => 0.31)] });
  const done = PROGRESS.filter((r) => r[2] === 'Done').length;
  source(s, `${done} of ${PROGRESS.length} done. Code: ${GITHUB} (PR #15 for this sprint, PR #14 for clarification reliability).`);
  notes(s, 5);
}

// ---- 6. Validation plan ----------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'VALIDATION PLAN', 'What we measure, against what, and the hard cases');
  const plan = [
    ['WHAT WE MEASURE, AND WHY', 'Late batches and late days (our objective), defective pieces, largest share, change under a closure: the course simulator\'s own metrics. For language: the right behaviour on each request, and every number traced to a tool.'],
    ['HOW THE EVALUATION SET IS BUILT', 'All 30 inbox requests, grouped by the 7 kinds in the data dictionary; held-out rewordings and bait items; two teammates label separately, then agree. A model judge is used only where it agrees with them.'],
    ['BASELINE AND TRACK MINIMUM', 'Random, biggest capacity and cheapest, plus the earliest-finish rule. Minimum: beat all three baselines on late batches and late days, and handle all 30 requests by kind.'],
  ];
  plan.forEach(([k, t], i) => {
    const y = 1.32 + i * 0.86;
    kicker(s, k, 0.6, y, 4.2, C.camelText);
    T(s, t, { x: 0.6, y: y + 0.2, w: 4.2, h: 0.62, fontSize: 8.5, color: C.inkSoft });
  });
  kicker(s, `TODAY, COURSE SEEDS ${seedRange}, NORMAL RUNS`, 5.1, 1.32, 4.3);
  const results = [
    ['Lateness (primary)', `${pct(hybrid['% late'])} late, ${hybrid['late days'].toFixed(3)} late days`, `earliest finish ${pct(ef['% late'])}, ${ef['late days'].toFixed(3)}`, 'Beats all'],
    ['Defects', `${pct(N('defects')['% def pcs'])} defective pieces`, `${label[best('% def pcs')]} ${pct(N(best('% def pcs'))['% def pcs'])}`, 'Beats all'],
    ['Fairness', `largest share ${pct(N('fairness')['max share'], 1)}`, `random ${pct(N('random')['max share'], 1)}`, 'Beats random'],
    ['Robustness', `+${rows.robustness.delta['% late'].toFixed(3)} pts late under closure`, `random +${rows.random.delta['% late'].toFixed(3)}`, 'Steadier'],
  ];
  s.addTable([[tableHead('OBJECTIVE'), tableHead('OURS'), tableHead('BEST REFERENCE'), tableHead('')],
    ...results.map(([o, a, b, v]) => [tableCell(o, { fontFace: HEAD, fontSize: 9.5 }), tableCell(a, { fontSize: 8.5 }), tableCell(b, { fontSize: 8.5, color: C.muted }),
      tableCell(v, { bold: true, color: C.forest, fontSize: 8.5 })])],
  { x: 5.1, y: 1.52, w: 4.3, colW: [1.05, 1.45, 1.1, 0.7], rowH: [0.22, 0.38, 0.38, 0.38, 0.38] });
  kicker(s, 'HARD CASES AND HOW WE HANDLE THEM', 5.1, 3.48, 4.3);
  const hard = [
    ['Impossible date', 'Earliest date, days late, a two-shop split; no booking'],
    ['Workshop that cannot take it', 'Refused with the reason, plus the best alternative'],
    ['Misheard order on the floor', 'Order, customer, pieces read back from orders.csv; slide to commit'],
  ];
  hard.forEach(([h, t], i) => {
    const y = 3.7 + i * 0.4;
    T(s, String(i + 1), { x: 5.1, y, w: 0.25, h: 0.3, fontFace: HEAD, fontSize: 15, color: C.camel });
    T(s, h, { x: 5.38, y, w: 4.0, h: 0.18, fontSize: 9, bold: true });
    T(s, t, { x: 5.38, y: y + 0.17, w: 4.0, h: 0.2, fontSize: 8, color: C.inkSoft });
  });
  source(s, 'Presets chosen on development seeds 6000-6029; the course seeds were run twice, as disclosed in docs/OBJECTIVE_STUDY.md.');
  notes(s, 6);
}

// ---- 7. Demo -----------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'DEMO', { x: 0.6, y: 0.55, w: 4, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'Ravi, on the floor', { x: 0.6, y: 0.8, w: 5, h: 0.6, fontFace: HEAD, fontSize: 28, color: C.onInk });
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
  image(s, asset('assistant-with-trace.png'), 5.5, 0.72, 4.1, 'The assistant beside its Behind the answer panel, showing a remembered rule applied to a new order');
  notes(s, 7);
}

// ---- 8. Thank you ------------------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'SWEATERCO', { x: 0.6, y: 0.5, w: 4, h: 0.3, fontFace: HEAD, fontSize: 13, color: C.onInk, charSpacing: 9 });
  T(s, 'Thank you.', { x: 0.6, y: 1.6, w: 8.8, h: 0.9, fontFace: HEAD, fontSize: 40, color: C.onInk });
  T(s, 'Questions are welcome.', { x: 0.6, y: 2.5, w: 8.8, h: 0.5, fontFace: HEAD, fontSize: 18, italic: true, color: C.onInkMuted });
  T(s, [{ text: 'GITHUB  ', options: { bold: true, color: C.camel } }, { text: GITHUB, options: { color: C.onInk } }],
    { x: 0.6, y: 3.55, w: 8.8, h: 0.22, fontSize: 10 });
  T(s, [{ text: 'DEMO VIDEO  ', options: { bold: true, color: C.camel } }, { text: DEMO_LINK, options: { color: C.onInk } }],
    { x: 0.6, y: 3.85, w: 8.8, h: 0.22, fontSize: 10 });
  T(s, 'RAVI TALKS  /  PYTHON CHECKS  /  A PERSON COMMITS', { x: 0.6, y: 4.5, w: 8.8, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'GROUP 11  /  DSS5105 CAPSTONE  /  30 OCTOBER 2026', { x: 0.6, y: 5.15, w: 8.8, h: 0.2, fontSize: 7.5, color: C.onInkMuted, charSpacing: 2 });
  notes(s, 8, ['Q&A PREPARATION' + qa.replace(/\n+$/, '')]);
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
