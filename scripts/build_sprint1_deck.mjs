// Build the Sprint 1 deck. Every metric is read from retained evidence JSON, never typed in.
//
//   mkdir -p .cache/deck-node && npm --prefix .cache/deck-node install pptxgenjs@3.12.0
//   node scripts/build_sprint1_deck.mjs
//
// Output: docs/slides/reviewed/Presentation_Group11_Sprint1.pptx (the exact upload name).
// Sources: docs/evidence/data-v3.json, margin-study.json, defects-frontier.json, track2/data/workshops.csv.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const nodeDir = process.env.PPTXGENJS_DIR || path.join(root, '.cache', 'deck-node');
const PptxGenJS = createRequire(path.join(nodeDir, 'package.json'))('pptxgenjs');
const out = path.join(root, 'docs', 'slides', 'reviewed', 'Presentation_Group11_Sprint1.pptx');
const readJson = (name) => JSON.parse(fs.readFileSync(path.join(root, 'docs', 'evidence', name), 'utf8'));

// ---- Evidence ---------------------------------------------------------------------------
const v3 = readJson('data-v3.json');
const margin = readJson('margin-study.json');
const frontier = readJson('defects-frontier.json');
const normal = v3.paired_normal_metrics;   // mean of 10 normal runs, seeds 5105-5114
const shock = v3.shock_metrics;            // mean of the same 10 seeds with --shock
const seeds = v3.seeds;
const buffered = margin.report.normal['selected_' + margin.selected];
const defectName = frontier.selected;
const defectRow = frontier.course.normal[defectName];
const workshopsCsv = fs.readFileSync(path.join(root, 'track2', 'data', 'workshops.csv'), 'utf8').trim().split(/\r?\n/);
const header = workshopsCsv[0].split(',');
const workshops = workshopsCsv.slice(1).map((line) => {
  const cells = line.match(/("[^"]*"|[^,]*)(,|$)/g).map((c) => c.replace(/,$/, '').replace(/^"|"$/g, ''));
  return Object.fromEntries(header.map((h, i) => [h, cells[i]]));
});
const trial = workshops.find((w) => w.max_batch_pieces);
const trialCap = trial.max_batch_pieces;
const suspended = workshops.find((w) => w.status === 'SUSPENDED');
const fastest = workshops.find((w) => /fastest/i.test(w.notes));
const topsOnly = workshops.filter((w) => w.makes === 'TOPS').length;
const WORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
const inWords = (n) => (Number.isInteger(+n) && WORDS[+n] ? WORDS[+n] : String(n));
const capital = (s) => s[0].toUpperCase() + s.slice(1);
// The inbox mix, from the course data dictionary's table of request kinds.
const dictionary = fs.readFileSync(path.join(root, 'track2', 'data', 'data_dictionary.md'), 'utf8')
  .split('## `dispatch_requests.txt`')[1].split('\n## ')[0];
const kinds = Object.fromEntries([...dictionary.matchAll(/^\| ([^|]+?) \| (\d+) \|/gm)].map((m) => [m[1], +m[2]]));
const inboxTotal = Object.values(kinds).reduce((a, b) => a + b, 0);
const plainRequests = kinds['Complete and meetable'];
const inboxLines = fs.readFileSync(path.join(root, 'track2', 'data', 'dispatch_requests.txt'), 'utf8').match(/^R\d+ /gm).length;
if (inboxTotal !== inboxLines || !plainRequests) throw new Error('Data dictionary request kinds do not match the inbox');
const BATCHES = 120; // orders.csv rows replayed by the simulator
const parseCsv = (file) => {
  const lines = fs.readFileSync(path.join(root, 'track2', 'data', file), 'utf8').trim().split(/\r?\n/);
  const cols = lines[0].split(',');
  return lines.slice(1).map((line) => Object.fromEntries(line.split(',').map((v, i) => [cols[i], v])));
};
// MARGIN_STUDY.md names the lateness preset's late batches; their size and category come from orders.csv.
const lateIds = [...fs.readFileSync(path.join(root, 'docs', 'MARGIN_STUDY.md'), 'utf8')
  .match(/two late batches: (ORD-\d+) and (ORD-\d+)/).slice(1)];
const lateOrders = parseCsv('orders.csv').filter((o) => lateIds.includes(o.order_id));
if (lateOrders.length !== 2 || lateOrders[0].pieces !== lateOrders[1].pieces || lateOrders[0].category !== lateOrders[1].category) {
  throw new Error('The two late batches no longer share a size and category; reword slide 6');
}
const lateSize = Number(lateOrders[0].pieces).toLocaleString('en-US');
const lateKind = lateOrders[0].category.toLowerCase();
const SPRINT2_TARGET = 27; // team target for the live inbox run, judged by request kind; a proposal, not a result
const TESTS = process.env.DECK_TEST_COUNT || '300'; // `uv run pytest` on 2026-10-15; override when it changes

const pct = (x, d = 1) => x.toFixed(d) + '%';
const num = (x) => Math.round(x).toLocaleString('en-US');
const kilo = (x) => '$' + (x / 1000).toFixed(1) + 'k';
const late = (row) => pct(row['% late']);
const relChange = (a, b) => Math.round((Math.abs(a - b) / b) * 100);
const lateBatches = (row) => Math.round((row['% late'] / 100) * BATCHES);
const costRatio = normal.lateness.cost / normal.cheapest.cost;
const extraLatePerTen = Math.round(((buffered['% late'] - normal.lateness['% late']) / 100) * BATCHES * 10);
const seedRange = `${seeds[0]}-${seeds[seeds.length - 1]}`;

// Speaker notes: the script file is the single source, so notes and script cannot drift.
const scriptText = fs.readFileSync(path.join(root, 'docs', 'slides', 'reviewed', 'Opening_Script_Group11.txt'), 'utf8');
const scriptSections = Object.fromEntries(
  scriptText.split(/^(?=SLIDE \d+ )/m).filter((part) => part.startsWith('SLIDE')).map((part) => {
    const [heading, ...body] = part.trim().split('\n');
    return [Number(heading.match(/^SLIDE (\d+)/)[1]), heading + '\n\n' + body.join(' ').replace(/\s+/g, ' ').trim()];
  }),
);
const notesFor = (n, extra = []) => [scriptSections[n], ...extra].filter(Boolean).join('\n\n');

// ---- House style ------------------------------------------------------------------------
const C = {
  ink: '1D1B18', inkSoft: '4A463F', muted: '6B665D', paper: 'FAF8F4', card: 'FFFFFF', wash: 'F3EFE7',
  line: 'E4DDD0', camel: 'A3804C', camelText: '7D5E30', camelLight: 'CDB78F', forest: '2F5D46',
  oxblood: '8A2C35', onInk: 'F4EFE6', onInkMuted: 'B9AF9F',
};
const HEAD = 'Georgia';
const BODY = 'Arial';
const pres = new PptxGenJS();
pres.layout = 'LAYOUT_16x9'; // 10 x 5.625 in, as the course template
pres.author = 'Group 11';
pres.title = 'Quick-Response Subcontracting Desk - Sprint 1';
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };

pres.defineSlideMaster({
  title: 'CONTENT',
  background: { color: C.paper },
  objects: [
    { text: { text: 'SWEATERCO  /  QUICK-RESPONSE SUBCONTRACTING DESK  /  GROUP 11',
      options: { x: 0.6, y: 5.2, w: 7, h: 0.25, fontFace: BODY, fontSize: 7, color: C.muted, charSpacing: 1.5, margin: 0 } } },
  ],
  slideNumber: { x: 8.9, y: 5.2, w: 0.5, h: 0.25, fontFace: BODY, fontSize: 7, color: C.muted, align: 'right' },
});
pres.defineSlideMaster({ title: 'DARK', background: { color: C.ink } });

const T = (slide, text, opts) => slide.addText(text, { fontFace: BODY, color: C.ink, margin: 0, isTextBox: true, valign: 'top', ...opts });
function frame(slide, eyebrow, title) {
  T(slide, eyebrow, { x: 0.6, y: 0.38, w: 8.8, h: 0.22, fontSize: 8.5, bold: true, color: C.camelText, charSpacing: 3 });
  T(slide, title, { x: 0.6, y: 0.62, w: 8.8, h: 0.62, fontFace: HEAD, fontSize: 24, valign: 'middle' });
}
function card(slide, x, y, w, h, fill = C.card, line = C.line) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: line, width: 0.75 } });
}
function numeral(slide, n, x, y, color = C.camel, size = 22) {
  T(slide, String(n), { x, y, w: 0.4, h: 0.4, fontFace: HEAD, fontSize: size, color, valign: 'top' });
}
function source(slide, text) {
  T(slide, text, { x: 0.6, y: 4.93, w: 8.8, h: 0.22, fontSize: 7.5, color: C.muted, italic: true });
}

// ---- 1. Cover ---------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'SWEATERCO', { x: 0.6, y: 0.5, w: 4, h: 0.3, fontFace: HEAD, fontSize: 13, color: C.onInk, charSpacing: 9 });
  T(s, 'GROUP 11  /  TRACK 2  /  SPRINT 1 REVIEW', { x: 0.6, y: 1.32, w: 6, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'The Quick-Response\nSubcontracting Desk', { x: 0.6, y: 1.6, w: 6.3, h: 1.45, fontFace: HEAD, fontSize: 38, color: C.onInk, valign: 'middle' });
  T(s, 'Who should make this batch? Answered in minutes, with the reasoning on record.',
    { x: 0.6, y: 3.12, w: 5.8, h: 0.6, fontFace: HEAD, fontSize: 15, italic: true, color: C.onInkMuted });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 3.92, w: 4.1, h: 0.4, rectRadius: 0.2, fill: { color: C.ink }, line: { color: C.camel, width: 1 } });
  T(s, [{ text: 'PRIMARY OBJECTIVE   ', options: { color: C.camel, bold: true } }, { text: 'MINIMISE LATENESS', options: { color: C.onInk, bold: true } }],
    { x: 0.6, y: 3.92, w: 4.1, h: 0.4, fontSize: 9, charSpacing: 1.5, align: 'center', valign: 'middle' });
  // Alphabetical by name, in the attendance format the course asks for.
  const members = [
    ['Chen Zepeng', 'A0156784N'], ['Duong Thanh Nhan', 'A0296326W'], ['Joshua Wesley Gloor', 'A0296944J'],
    ['Sridhar Niyanthri Rajeswari', 'A0351151U'], ['Sundara Rajan Saadhvika', 'A0352594W'], ['Tang Zheling', 'A0352177B'],
  ];
  members.forEach(([name, id], i) => T(s, `${name} (${id}) \u2014 Present (in person)`,
    { x: i < 3 ? 0.6 : 4.85, y: 4.47 + (i % 3) * 0.19, w: 4.2, h: 0.18, fontSize: 8.5, color: C.onInk }));
  T(s, 'DSS5105 CAPSTONE  /  16 OCTOBER 2026', { x: 0.6, y: 5.16, w: 8.8, h: 0.2, fontSize: 7.5, color: C.onInkMuted, charSpacing: 2 });
  // The network, set like a collection line-up. The restricted workshops are named beneath it, from workshops.csv.
  T(s, 'THE NETWORK', { x: 7.0, y: 1.32, w: 2.4, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3, align: 'right' });
  T(s, workshops.map((w) => ({ text: w.name, options: { breakLine: true, color: w.status === 'ACTIVE' ? C.onInk : '6E675C' } })),
    { x: 6.6, y: 1.62, w: 2.8, h: 2.7, fontFace: HEAD, fontSize: 15, italic: true, align: 'right', paraSpaceAfter: 2.5 });
  T(s, `${suspended.name} suspended. ${trial.name} on trial, max ${trialCap}.`,
    { x: 5.9, y: 3.84, w: 3.5, h: 0.22, fontFace: HEAD, fontSize: 9.5, italic: true, color: C.camel, align: 'right' });
  s.addNotes(notesFor(1));
}

// ---- 2. Problem -------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'THE PROBLEM', 'Today, one chat message is the whole decision');
  card(s, 0.6, 1.45, 4.3, 1.55);
  T(s, '\u201C', { x: 0.82, y: 1.47, w: 0.5, h: 0.5, fontFace: HEAD, fontSize: 40, color: C.camel });
  T(s, '@Chen - order 042, 1,500 crewnecks. Send it to QuickStitch, need it back by the 19th.',
    { x: 0.85, y: 1.86, w: 3.85, h: 0.8, fontFace: HEAD, fontSize: 15, italic: true });
  T(s, 'HOW ALLOCATION IS DECIDED TODAY  /  COURSE BRIEF', { x: 0.85, y: 2.72, w: 3.9, h: 0.2, fontSize: 7, color: C.muted, charSpacing: 1.5 });
  T(s, 'Everything behind it lives in one dispatcher\u2019s head. Nobody can check it, and nothing is written down.',
    { x: 0.6, y: 3.14, w: 4.3, h: 0.45, fontSize: 12, color: C.inkSoft });
  // The inbox mix: why a language model is needed at all.
  s.addShape(pres.shapes.LINE, { x: 0.6, y: 3.7, w: 4.3, h: 0, line: { color: C.line, width: 0.75 } });
  T(s, `${plainRequests} of ${inboxTotal}`, { x: 0.6, y: 3.8, w: 1.3, h: 0.45, fontFace: HEAD, fontSize: 26, color: C.camel, valign: 'middle' });
  T(s, `requests in this morning\u2019s inbox are plain allocations. The other ${inboxTotal - plainRequests} need a question, a refusal, a constraint or bad news.`,
    { x: 1.95, y: 3.8, w: 2.95, h: 0.5, fontSize: 10, color: C.inkSoft, valign: 'middle' });
  T(s, 'THREE QUESTIONS, EVERY TIME', { x: 5.4, y: 1.45, w: 4, h: 0.22, fontSize: 8.5, bold: true, color: C.muted, charSpacing: 2 });
  const qs = [
    ['Can they make it?', `${capital(inWords(topsOnly))} of the ${inWords(workshops.length)} make tops only, so they cannot take a scarf order.`],
    ['Can they take it now?', `${fastest.name}, \u201C${fastest.notes.split(';')[0]}\u201D, already has ${inWords(fastest.current_queue_days.replace(/\.0$/, ''))} days of work queued.`],
    ['Are they allowed to?', `${suspended.name} is suspended after an audit. ${trial.name} is on trial, capped at ${trialCap} pieces.`],
  ];
  qs.forEach(([q, a], i) => {
    const y = 1.8 + i * 0.78;
    numeral(s, i + 1, 5.4, y - 0.04);
    T(s, q, { x: 5.9, y, w: 3.5, h: 0.3, fontFace: HEAD, fontSize: 15 });
    T(s, a, { x: 5.9, y: y + 0.3, w: 3.5, h: 0.4, fontSize: 10.5, color: C.inkSoft });
  });
  T(s, 'Get one wrong and the batch bounces back a day later. In a ten-day cycle, that is the margin gone.',
    { x: 0.6, y: 4.5, w: 8.8, h: 0.4, fontFace: HEAD, fontSize: 14, italic: true, color: C.oxblood });
  s.addNotes(notesFor(2));
}

// ---- 3. Solution and architecture -------------------------------------------------------
// The implemented components and their interfaces, named as in src/dss5105. The dashed line is the
// trust boundary: the model call is the only thing that leaves the machine.
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'OUR SOLUTION AND ARCHITECTURE', 'The model reads. Python calculates. A person approves.');
  const MONO = 'Courier New';
  const OUTSIDE = { x: 0.6, w: 1.45 };
  const IN = { x: 2.45, w: 2.0 }, CORE = { x: 4.7, w: 2.3 }, OUT = { x: 7.25, w: 2.15 };
  const DESK = { y: 1.5, h: 0.56 }, SVC = { y: 2.34, h: 1.32 }, DATA = { y: 3.96, h: 0.62 };
  const arrow = (x1, y1, x2, y2, dash) => s.addShape(pres.shapes.LINE, {
    x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1),
    line: { color: C.ink, width: 1, dashType: dash, [x2 < x1 || y2 < y1 ? 'beginArrowType' : 'endArrowType']: 'triangle' },
  });
  const flow = (text, x, y, w = 1.6, mono = false) =>
    T(s, text, { x, y, w, h: 0.15, fontSize: mono ? 6.5 : 7, fontFace: mono ? MONO : BODY, italic: !mono, color: C.muted });
  const external = (y, h) => s.addShape(pres.shapes.RECTANGLE, {
    x: OUTSIDE.x, y, w: OUTSIDE.w, h, fill: { color: C.wash }, line: { color: C.muted, width: 0.75, dashType: 'dash' },
  });
  const zone = { fontSize: 6.5, bold: true, color: C.muted, charSpacing: 1.5 };
  T(s, 'OUTSIDE', { x: OUTSIDE.x, y: 1.3, w: OUTSIDE.w, h: 0.14, ...zone });
  T(s, 'OUR MACHINE  /  ONE PYTHON PROCESS: LOCAL ON 127.0.0.1, OR ON EC2 BEHIND CADDY', { x: IN.x, y: 1.3, w: 6.95, h: 0.14, ...zone });
  s.addShape(pres.shapes.LINE, { x: 2.25, y: 1.3, w: 0, h: DATA.y + DATA.h - 1.3, line: { color: C.camel, width: 1.25, dashType: 'dash' } });

  // Where requests come from, and the one external call.
  external(DESK.y, DESK.h);
  T(s, 'Group chat', { x: OUTSIDE.x + 0.1, y: DESK.y + 0.07, w: 1.25, h: 0.22, fontFace: HEAD, fontSize: 11 });
  T(s, 'the request as typed', { x: OUTSIDE.x + 0.1, y: DESK.y + 0.3, w: 1.25, h: 0.18, fontSize: 7.5, color: C.inkSoft });
  external(SVC.y, SVC.h);
  T(s, 'EXTERNAL', { x: OUTSIDE.x + 0.1, y: SVC.y + 0.09, w: 1.25, h: 0.15, fontSize: 7, bold: true, charSpacing: 1.5, color: C.camelText });
  T(s, 'LLM provider', { x: OUTSIDE.x + 0.1, y: SVC.y + 0.26, w: 1.25, h: 0.2, fontFace: HEAD, fontSize: 11 });
  T(s, 'Called through LangChain, model set by LLM_MODEL. Sees the message, earlier turns, the draft and names. Never prices, queues or defect rates.',
    { x: OUTSIDE.x + 0.1, y: SVC.y + 0.5, w: 1.27, h: 0.66, fontSize: 7.5, color: C.inkSoft });
  T(s, 'TRUST BOUNDARY', { x: OUTSIDE.x, y: DATA.y + 0.04, w: OUTSIDE.w, h: 0.15, fontSize: 7, bold: true, charSpacing: 1.5, color: C.camelText });
  T(s, 'The model call is the app\u2019s only outbound call. Streamlit telemetry is off.',
    { x: OUTSIDE.x, y: DATA.y + 0.22, w: OUTSIDE.w, h: 0.4, fontSize: 7.5, color: C.inkSoft });

  // The desk the dispatcher works in.
  card(s, IN.x, DESK.y, 6.95, DESK.h);
  T(s, 'STREAMLIT DESK', { x: IN.x + 0.12, y: DESK.y + 0.08, w: 1.2, h: 0.15, fontSize: 7, bold: true, charSpacing: 1.5, color: C.camelText });
  T(s, 'web_app.py  chat_ui.py  replies.py', { x: IN.x + 1.3, y: DESK.y + 0.075, w: 3, h: 0.16, fontFace: MONO, fontSize: 8, bold: true });
  T(s, 'The dispatcher\u2019s screen: chat, ranked options, delivery chart and Confirm. Session state is the short-term memory: turns, draft and open questions go back to the model each turn. Replies are built from tool output.',
    { x: IN.x + 0.12, y: DESK.y + 0.26, w: 6.7, h: 0.27, fontSize: 8, color: C.inkSoft });

  // The three steps of the title, as the modules that implement them.
  const services = [
    [IN, '1  LLM, VIA LANGCHAIN', 'intake.py', 'Structured output fills a typed patch. A value is kept only if its exact quote is in the message; a gap gets a fixed Python question.', 'out: DispatchInput', false],
    [CORE, '2  DETERMINISTIC TOOLS', 'dispatch.py  allocator.py', 'Order lookup, eligibility check, queue check, delivery estimator, overload probe and split planner, then a ranking by configured weights.', 'out: preview, reasons, hashes', true],
    [OUT, '3  HUMAN IN THE LOOP', 'records.py', 'Confirm opens one SQLite transaction: recompute the preview, reject it if anything changed, then save the record and queues.', 'out: one audit record', false],
  ];
  services.forEach(([col, step, module, body, output, core]) => {
    const x = col.x + 0.12, w = col.w - 0.24;
    card(s, col.x, SVC.y, col.w, SVC.h, core ? C.ink : C.card, core ? C.ink : C.line);
    T(s, step, { x, y: SVC.y + 0.09, w, h: 0.15, fontSize: 7, bold: true, charSpacing: 1.5, color: core ? C.camelLight : C.camelText });
    T(s, module, { x, y: SVC.y + 0.27, w, h: 0.18, fontFace: MONO, fontSize: 9, bold: true, color: core ? C.onInk : C.ink });
    T(s, body, { x, y: SVC.y + 0.49, w, h: 0.5, fontSize: 8, color: core ? C.onInk : C.inkSoft });
    T(s, output, { x, y: SVC.y + SVC.h - 0.22, w, h: 0.15, fontFace: MONO, fontSize: 7.5, color: core ? C.camelLight : C.camelText });
  });

  // Data and shared code.
  const stores = [
    [IN.x, IN.w, 'evaluate.py', `Offline: ${BATCHES} orders x ${seeds.length} seeds, normal and closure runs. Same allocator, no model.`],
    [CORE.x, 1.1, 'harness.py', 'The course simulate.py, unmodified'],
    [CORE.x + 1.2, 1.1, 'track2/data', 'orders.csv and workshops.csv, read-only'],
    [OUT.x, OUT.w, 'runtime/ SQLite', 'Long-term memory: audit records and the planning queues later previews read.'],
  ];
  stores.forEach(([x, w, name, body]) => {
    card(s, x, DATA.y, w, DATA.h, C.wash);
    T(s, name, { x: x + 0.1, y: DATA.y + 0.07, w: w - 0.2, h: 0.16, fontFace: MONO, fontSize: 8, bold: true });
    T(s, body, { x: x + 0.1, y: DATA.y + 0.25, w: w - 0.2, h: 0.36, fontSize: 7.5, color: C.inkSoft });
  });

  // Data flows.
  const mid = SVC.y + 0.6;
  arrow(OUTSIDE.x + OUTSIDE.w, DESK.y + DESK.h / 2, IN.x, DESK.y + DESK.h / 2);
  arrow(IN.x, SVC.y + 0.48, OUTSIDE.x + OUTSIDE.w, SVC.y + 0.48);
  arrow(OUTSIDE.x + OUTSIDE.w, SVC.y + 0.74, IN.x, SVC.y + 0.74);
  arrow(IN.x + 0.45, DESK.y + DESK.h, IN.x + 0.45, SVC.y);
  flow('message', IN.x + 0.52, DESK.y + DESK.h + 0.07);
  arrow(CORE.x + 0.45, SVC.y, CORE.x + 0.45, DESK.y + DESK.h);
  flow('preview for review', CORE.x + 0.52, DESK.y + DESK.h + 0.07);
  arrow(OUT.x + 0.45, DESK.y + DESK.h, OUT.x + 0.45, SVC.y);
  flow('Confirm, name, retry key', OUT.x + 0.52, DESK.y + DESK.h + 0.07);
  arrow(IN.x + IN.w, mid, CORE.x, mid);
  arrow(OUT.x, mid, CORE.x + CORE.w, mid, 'dash');
  arrow(CORE.x + 0.55, SVC.y + SVC.h, CORE.x + 0.55, DATA.y);
  arrow(CORE.x + 1.75, SVC.y + SVC.h, CORE.x + 1.75, DATA.y);
  arrow(OUT.x + 0.45, SVC.y + SVC.h, OUT.x + 0.45, DATA.y);
  flow('BEGIN IMMEDIATE', OUT.x + 0.52, SVC.y + SVC.h + 0.09, 1.4, true);
  arrow(IN.x + IN.w, DATA.y + DATA.h / 2, CORE.x, DATA.y + DATA.h / 2);

  T(s, 'Agent pattern today: one well-tooled dispatcher, run as a workflow. The model never picks a tool or does arithmetic.',
    { x: 0.6, y: 4.68, w: 8.8, h: 0.26, fontFace: HEAD, fontSize: 11, italic: true });
  s.addNotes(notesFor(3, [
    'Q&A on the agent pattern: a workflow agent, which the track calls a single well-tooled dispatcher: the LLM and the tools run on a fixed code path. Not ReAct: every request needs the same checks in the same order, so letting the model choose tools in a loop adds cost and nondeterminism without accuracy. Not multi-agent: the track says a plain dispatcher with excellent tools beats a multi-agent conversation. Sprint 2 adds tool selection for read-only capacity questions only; Python still runs the tool and writes the answer.',
    'Q&A on LangChain and memory: llm.py builds the model with LangChain init_chat_model (provider-agnostic, LLM_MODEL); intake.py calls with_structured_output against a JSON schema. No LangGraph: a fixed pipeline needs no graph runtime. Short-term memory is Streamlit session state (turns, draft, open questions, provenance, model traces; 16 turns per conversation). Long-term memory is SQLite: audit records and planning queues. No vector store: the data is small and structured, so tools query it directly.',
    'Q&A: one structured-output call per chat turn, not autonomous agents. The model returns a typed patch; each value must appear inside an exact quotation from the latest message, or Python rejects the turn (intake.py). Clarifying questions are fixed Python text, not model prose. get_model() reads LLM_MODEL from .env, with a 30 s timeout and no retries.',
    'Q&A: locally the app binds to 127.0.0.1. On AWS it runs in a container behind Caddy with a password, and its secrets come from Parameter Store, never the repo or GitHub. Streamlit telemetry is off in both (.streamlit/config.toml). The only outbound call the app makes is the model call in intake.py. Its payload is the latest message, earlier user turns, the draft so far, and the workshop, customer and product names. Each turn records the model name, a prompt hash and the returned patch.',
    'Q&A on controls: in banking terms this is maker-checker. The model proposes fields, Python checks them, and a person confirms; the record keeps who set each constraint and who confirmed. The confirming name is self-declared, not authenticated yet.',
    'Q&A: confirming recomputes the preview inside a SQLite BEGIN IMMEDIATE transaction and compares its fingerprint; a changed queue revision or forged estimate is rejected, and an idempotency key makes a double click save once (records.py).',
  ]));
}

// ---- 4. Objective -----------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'PRIMARY OBJECTIVE', 'We declare: minimise lateness');
  const why = [
    ['Why', 'Quick response sells speed. A defect can be reworked; a missed reorder date loses the sale.'],
    ['Measured by', 'The share of batches that arrive late, and the average days late, from the course simulator.'],
    ['Bar to clear', 'Beat random, biggest-capacity and cheapest on both measures, in normal runs and in the closure test.'],
  ];
  why.forEach(([h, b], i) => {
    const y = 1.45 + i * 1.08;
    T(s, h.toUpperCase(), { x: 0.6, y, w: 3.3, h: 0.2, fontSize: 8, bold: true, color: C.camelText, charSpacing: 2 });
    T(s, b, { x: 0.6, y: y + 0.24, w: 3.3, h: 0.75, fontSize: 11.5, color: C.ink });
  });
  T(s, 'ALL FOUR COURSE OBJECTIVES: WINS AND LOSSES', { x: 4.3, y: 1.45, w: 5.1, h: 0.2, fontSize: 8, bold: true, color: C.muted, charSpacing: 2 });
  const rows = [
    ['Minimise lateness', `${late(normal.lateness)} late, vs ${late(normal.random)} for random`, 'Beats all three baselines', C.forest],
    ['Minimise defects', `${pct(defectRow['% def pcs'])} defective pieces, ${late(defectRow)} late`,
      `Biggest-capacity still wins (${pct(frontier.course.normal.greedy_biggest['% def pcs'])})`, C.oxblood],
    ['Robust to failure', `Closure adds ${v3.paired_deltas.lateness['% late'].toFixed(2)} points late; random adds ${v3.paired_deltas.random['% late'].toFixed(1)}`,
      `Steadier than random and biggest. Cheapest stays ${Math.round(normal.cheapest['% late'])}% late either way`, C.camelText],
    ['Fair allocation', `Not tuned yet: the busiest workshop takes ${pct(normal.lateness['max share'])} of pieces`,
      `Random spreads work more evenly (${pct(normal.random['max share'])})`, C.oxblood],
  ];
  const cell = (text, o = {}) => ({ text, options: { fontFace: BODY, fontSize: 9.5, color: C.ink, valign: 'middle', margin: [3, 4, 3, 0],
    border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', color: C.line, pt: 0.75 }, { type: 'none' }], ...o } });
  const head = (text) => cell(text, { fontSize: 7, bold: true, color: C.muted, charSpacing: 1.5,
    border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', color: C.ink, pt: 1 }, { type: 'none' }] });
  s.addTable([
    [head('OBJECTIVE'), head('OUR BEST SETTING'), head('VERDICT')],
    ...rows.map(([o, m, v, color]) => [cell(o, { fontFace: HEAD, fontSize: 11 }), cell(m), cell(v, { bold: true, color })]),
  ], { x: 4.3, y: 1.75, w: 5.1, colW: [1.35, 1.95, 1.8], rowH: [0.3, 0.62, 0.62, 0.62, 0.62] });
  source(s, `Course simulator, mean of 10 runs (seeds ${seedRange}). The defects setting was chosen on separate development seeds before this run.`);
  s.addNotes(notesFor(4, [`Q&A: defects setting ${defectName} was picked on development seeds 6000-6009, then run once on the course seeds. It beat biggest-capacity on only ${frontier.course.selected_seed_wins_vs_greedy_biggest_normal} of 10 course seeds. Evidence: docs/evidence/defects-frontier.json.`]));
}

// ---- 5. Business value ------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  const fewer = Math.round((1 - normal.lateness['% late'] / normal.random['% late']) * 100);
  frame(s, 'BUSINESS VALUE', `${fewer}% fewer late batches than random allocation`);
  card(s, 0.6, 1.45, 3.4, 3.3, C.ink, C.ink);
  T(s, late(normal.lateness), { x: 0.85, y: 1.6, w: 3, h: 0.95, fontFace: HEAD, fontSize: 58, color: C.onInk, valign: 'middle' });
  T(s, `of batches late, ${lateBatches(normal.lateness)} in ${BATCHES}, when queue, processing and transport are checked before choosing`,
    { x: 0.85, y: 2.6, w: 2.95, h: 0.62, fontSize: 11, color: C.onInk });
  T(s, late(normal.random), { x: 0.85, y: 3.3, w: 3, h: 0.45, fontFace: HEAD, fontSize: 24, color: C.camelLight });
  T(s, `${lateBatches(normal.random)} in ${BATCHES} for a random eligible workshop`, { x: 0.85, y: 3.75, w: 2.95, h: 0.25, fontSize: 10, color: C.onInkMuted });
  T(s, 'Course simulator, 10 runs. Not a factory result.', { x: 0.85, y: 4.35, w: 2.95, h: 0.22, fontSize: 8, italic: true, color: C.onInkMuted });
  const items = [
    ['Operational efficiency & risk reduction', 'No bounced batches: the course\u2019s own eligibility rule runs before anything is recommended.'],
    ['Transparency & auditability', 'A full record of the request, every option, the estimates, who set each constraint and who approved.'],
    ['Proactive exception management', 'An impossible date gets the earliest achievable date and the options: split, accept late, escalate.'],
    ['Transparent cost-speed trade-offs', `${kilo(normal.lateness.cost)} per run, against ${kilo(normal.cheapest.cost)} for always-cheapest (late on ${Math.round(normal.cheapest['% late'])}% of batches) and ${kilo(normal.random.cost)} for random.`],
  ];
  items.forEach(([h, b], i) => {
    const y = 1.45 + i * 0.83;
    numeral(s, i + 1, 4.4, y - 0.04, i === 3 ? C.oxblood : C.camel, 20);
    T(s, h, { x: 4.85, y, w: 4.55, h: 0.28, fontFace: HEAD, fontSize: 14 });
    T(s, b, { x: 4.85, y: y + 0.29, w: 4.55, h: 0.48, fontSize: 10.5, color: C.inkSoft });
  });
  s.addNotes(notesFor(5, [`Q&A: cost per replay ${num(normal.lateness.cost)} for our desk, ${num(normal.random.cost)} for random, ${num(normal.cheapest.cost)} for cheapest; ratio to cheapest ${costRatio.toFixed(2)} (shown as $; the data gives cost per piece with no currency, so say so if asked).`]));
}

// ---- 6. Progress: evidence and deployment ------------------------------------------------
// The deployment half is what infra/ and .github/workflows/deploy.yaml on main do; see docs/DEPLOYMENT.md there.
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'SPRINT 1 PROGRESS', 'Working allocator, working deployment pipeline');
  // One bar per policy: the normal run, with the closure test's extra lateness in ink after it.
  const policies = [['random', 'Random'], ['greedy_biggest', 'Biggest capacity'], ['cheapest', 'Cheapest'], ['earliest_finish', 'Earliest finish'], ['lateness', 'Our desk']];
  T(s, '% OF BATCHES LATE, MEAN OF 10 RUNS. LOWER IS BETTER', { x: 0.6, y: 1.42, w: 4.8, h: 0.18, fontSize: 7.5, bold: true, color: C.muted, charSpacing: 1.5 });
  [['Normal run', C.camelLight], ['Added by the closure test', C.ink]].forEach(([label, color], i) => {
    const x = 0.6 + i * 1.2;
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.68, w: 0.12, h: 0.12, fill: { color }, line: { color } });
    T(s, label, { x: x + 0.17, y: 1.65, w: 1.6, h: 0.18, fontSize: 7.5, color: C.inkSoft, valign: 'middle' });
  });
  const barX = 1.75, barMax = 2.75;
  policies.forEach(([key, label], i) => {
    const y = 1.94 + i * 0.21;
    const ours = key === 'lateness';
    const n = normal[key]['% late'], k = shock[key]['% late'];
    const wn = Math.max(0.03, (n / 100) * barMax), wk = Math.max(wn, (k / 100) * barMax);
    T(s, label, { x: 0.6, y, w: 1.1, h: 0.16, fontSize: 8.5, bold: ours, color: ours ? C.forest : C.ink, valign: 'middle' });
    s.addShape(pres.shapes.RECTANGLE, { x: barX, y: y + 0.01, w: wk, h: 0.14, fill: { color: C.ink }, line: { color: C.ink, width: 0 } });
    s.addShape(pres.shapes.RECTANGLE, { x: barX, y: y + 0.01, w: wn, h: 0.14, fill: { color: C.camelLight }, line: { color: C.camelLight, width: 0 } });
    T(s, `${n.toFixed(1)} / ${k.toFixed(1)}`, { x: barX + wk + 0.07, y, w: 0.9, h: 0.16, fontSize: 8, bold: ours, color: C.ink, valign: 'middle' });
  });
  card(s, 5.65, 1.42, 3.75, 0.72);
  T(s, 'HONEST FINDING', { x: 5.82, y: 1.5, w: 3.4, h: 0.16, fontSize: 7.5, bold: true, color: C.oxblood, charSpacing: 2 });
  T(s, `Earliest finish ties us. Lateness is near its floor: two batches of ${lateSize} ${lateKind} cannot be made in their window.`,
    { x: 5.82, y: 1.7, w: 3.45, h: 0.4, fontSize: 9, color: C.ink });
  card(s, 5.65, 2.22, 3.75, 0.8);
  T(s, 'WHAT OUR ALLOCATOR ADDS', { x: 5.82, y: 2.3, w: 3.4, h: 0.16, fontSize: 7.5, bold: true, color: C.forest, charSpacing: 2 });
  if (!(buffered.cost < normal.random.cost)) throw new Error('The buffered setting is no longer cheaper than random; reword slide 6');
  const costCut = ((1 - buffered.cost / normal.lateness.cost) * 100).toFixed(1);
  T(s, `The same code, re-weighted: a ${margin.selected_weights.deadline_buffer_days}-day buffer cuts cost ${costCut}%, below random\u2019s, and late days ${relChange(buffered['late days'], normal.lateness['late days'])}%, for about ${inWords(extraLatePerTen)} more late batch per ten runs.`,
    { x: 5.82, y: 2.5, w: 3.45, h: 0.5, fontSize: 9, color: C.ink });

  // Joshua's pipeline diagram, in the house colours. Sized from the PNG header so a re-export keeps its shape.
  const deployPng = path.join(root, 'docs', 'slides', 'reviewed', 'sprint-1-progress-deploy-diagram.png');
  const deployHead = fs.readFileSync(deployPng);
  const deployRatio = deployHead.readUInt32BE(16) / deployHead.readUInt32BE(20);
  const deployH = Math.min(1.8, 8.8 / deployRatio), deployW = deployH * deployRatio;
  s.addImage({ path: deployPng, x: 0.6 + (8.8 - deployW) / 2, y: 3.1, w: deployW, h: deployH,
    altText: 'Deployment pipeline: on merge, GitHub Actions runs CI, builds an image and pushes it to ECR. On demand, the Deploy workflow sends a script over SSM to EC2, which reads secrets from Parameter Store, pulls the image and starts Caddy in front of Streamlit. GitHub reaches AWS through OIDC. All AWS resources are provisioned with OpenTofu.' });

  source(s, `Course simulator, seeds ${seedRange}; buffer chosen on seeds 6000-6009 first. Sources: docs/V3_EVALUATION.md, docs/MARGIN_STUDY.md, docs/DEPLOYMENT.md (main).`);
  s.addNotes(notesFor(6, [
    `Q&A: buffer cuts cost ${costCut}% and late days ${relChange(buffered['late days'], normal.lateness['late days'])}%; % late ${late(buffered)} vs ${late(normal.lateness)}. The late batches are ${lateIds.join(' and ')}.`,
    'Q&A on deployment: a push to main builds an image and pushes it to ECR. The manual Deploy workflow finds the instance by tag and sends a script over SSM, so there is no SSH. The instance reads its secrets from Parameter Store, pulls the image and runs docker compose: Caddy with a password in front of Streamlit. GitHub assumes an AWS role through OIDC, so no AWS key is stored anywhere, and a curl check confirms the site answers. Confirmed allocations persist in a docker volume. The instance is stopped when unused; the Power workflow starts it.',
  ]));
}

// ---- 7. Progress: the product -----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'SPRINT 1 PROGRESS  /  THE DESK TODAY', 'Candidates, estimates and the choice, at a glance');
  // Size the screenshot from its PNG header, so a re-capture never stretches it.
  const png = fs.readFileSync(path.join(root, 'docs', 'slides', 'assets', 'desk-r25.png'));
  const imgW = 4.6, imgH = imgW * (png.readUInt32BE(20) / png.readUInt32BE(16));
  s.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.4, w: imgW, h: imgH, fill: { color: C.card }, line: { color: C.line, width: 0.75 },
    shadow: { type: 'outer', color: '000000', opacity: 0.12, blur: 8, offset: 3, angle: 90 } });
  s.addImage({ path: path.join(root, 'docs', 'slides', 'assets', 'desk-r25.png'), x: 0.6, y: 1.4, w: imgW, h: imgH, altText: 'Dispatch desk showing request R25 and the recommended workshop with the reasons for it' });
  const x = 0.6 + imgW + 0.35, w = 9.4 - x;
  const points = [
    ['The message stays in view', 'Request R25: "keep it away from BudgetWorks". The exclusion is applied and recorded against Mei, who asked.'],
    ['It says why, in Python\u2019s words', 'Earliest of the permitted workshops, days to spare, and how the next option compares. No model writes these lines.'],
    ['Where the days go', 'A chart splits each option into queue, processing, transport and rework, so a busy \u201Cfast\u201D workshop shows up.'],
    ['Review before anything is saved', 'Confirming rechecks the queues first, then writes one audit record.'],
  ];
  points.forEach(([h, b], i) => {
    const y = 1.4 + i * 0.78;
    numeral(s, i + 1, x, y - 0.04, C.camel, 18);
    T(s, h, { x: x + 0.38, y, w: w - 0.38, h: 0.27, fontFace: HEAD, fontSize: 13 });
    T(s, b, { x: x + 0.38, y: y + 0.28, w: w - 0.38, h: 0.46, fontSize: 9.5, color: C.inkSoft });
  });
  T(s, 'ALSO WORKING', { x: 0.6, y: 4.8, w: 1.4, h: 0.2, fontSize: 8, bold: true, color: C.muted, charSpacing: 2 });
  T(s, `All 30 inbox requests reach the right outcome from hand-checked inputs  /  live chat that asks when unsure  /  stale-safe saved plan  /  ${TESTS} offline tests`,
    { x: 2.05, y: 4.8, w: 7.35, h: 0.2, fontSize: 7.5, color: C.inkSoft });
  s.addNotes(notesFor(7));
}

// ---- 8. Risks and assumptions -----------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  frame(s, 'RISKS AND KEY ASSUMPTIONS', 'What could go wrong, and what we assume');
  const risks = [
    ['The model misreads a request', 'High', 'High', 'Every field must quote the message; Python checks it and asks when unsure. First live run: one needless question blocked a refusal.'],
    ['A message tries to bend the rules', 'Medium', 'High', 'Eligibility is a Python check the model cannot switch off. A suspended workshop is refused; exclusions cannot be relaxed mid-chat.'],
    ['A number no tool produced', 'Medium', 'High', 'Tools format every number, and an automatic check compares each figure on screen with tool output.'],
    ['Tuning to the 120 supplied orders', 'Medium', 'Medium', 'Choose settings on separate development seeds, then run the course seeds once.'],
    ['The simulator is simpler than a factory', 'Certain', 'Medium', 'Say so, keep its default run as the yardstick, and test the desk with dispatchers.'],
  ];
  const tone = { High: C.oxblood, Medium: C.camelText, Certain: C.ink };
  T(s, 'RISK', { x: 0.6, y: 1.42, w: 1.85, h: 0.2, fontSize: 7, bold: true, color: C.muted, charSpacing: 1.5 });
  T(s, 'CHANCE / IMPACT', { x: 2.5, y: 1.42, w: 1.3, h: 0.2, fontSize: 7, bold: true, color: C.muted, charSpacing: 1.5 });
  T(s, 'WHAT WE DO ABOUT IT', { x: 3.9, y: 1.42, w: 2.45, h: 0.2, fontSize: 7, bold: true, color: C.muted, charSpacing: 1.5 });
  s.addShape(pres.shapes.LINE, { x: 0.6, y: 1.66, w: 5.75, h: 0, line: { color: C.ink, width: 1 } });
  risks.forEach(([r, l, im, m], i) => {
    const y = 1.74 + i * 0.64;
    T(s, r, { x: 0.6, y, w: 1.72, h: 0.5, fontFace: HEAD, fontSize: 11 });
    T(s, [{ text: l, options: { color: tone[l], bold: true } }, { text: ' / ', options: { color: C.muted } }, { text: im, options: { color: tone[im], bold: true } }],
      { x: 2.5, y: y + 0.02, w: 1.3, h: 0.3, fontSize: 8.5 });
    T(s, m, { x: 3.9, y: y + 0.01, w: 2.45, h: 0.55, fontSize: 8.5, color: C.inkSoft });
    if (i < risks.length - 1) s.addShape(pres.shapes.LINE, { x: 0.6, y: y + 0.58, w: 5.75, h: 0, line: { color: C.line, width: 0.75 } });
  });
  T(s, 'KEY ASSUMPTIONS', { x: 6.75, y: 1.42, w: 2.65, h: 0.2, fontSize: 8, bold: true, color: C.camelText, charSpacing: 2 });
  const assumptions = [
    'Each inbox request is judged on the 1 April queues, on its own.',
    'A defect means half the batch is redone, as in the simulator.',
    'Workshop prices are our subcontract cost, not the customer\u2019s price, so price questions are declined.',
    'A person confirms every allocation. No workshop is contacted automatically.',
  ];
  assumptions.forEach((a, i) => {
    const y = 1.72 + i * 0.77;
    card(s, 6.75, y, 2.65, 0.66, C.wash, C.wash);
    T(s, a, { x: 6.9, y: y + 0.08, w: 2.4, h: 0.52, fontSize: 9, valign: 'middle' });
  });
  s.addNotes(notesFor(8));
}

// ---- 9. Roadmap -------------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'CONTENT' });
  // The AI-native items are a team proposal: docs/AI_NATIVE_PLAN.md.
  frame(s, 'SPRINT 2 ROADMAP  /  DUE 30 OCTOBER', 'From working tools to an AI-native desk');
  const plan = [
    ['Evaluation set first', '30+ questions checked against the data, 10 held out, 5+ injection and bait items'],
    [`Live chat on all ${inboxTotal} inbox requests`, 'Labels two teammates write independently; decision and explanation scored apart'],
    ['Tool calling for questions', '"Who can take 1,500 crewnecks?": the model picks a read-only tool, Python answers'],
    ['Grounded explanations and replies', 'The model writes with placeholders; Python fills every number, nothing auto-sends'],
    ['LLM judge, checked against people', 'Agreement with both human labellers reported; people stay the ground truth'],
    ['Freeze the second objective and hybrid', 'Weights fixed on development seeds, metrics on a common scale, one course run'],
    ['Demo video', 'Request, clarify, refuse, impossible date, confirm'],
  ];
  const cell = (text, o = {}) => ({ text, options: { fontFace: BODY, fontSize: 9.5, color: C.ink, valign: 'middle', margin: [2, 4, 2, 0],
    border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', color: C.line, pt: 0.75 }, { type: 'none' }], ...o } });
  const head = (text) => cell(text, { fontSize: 7, bold: true, color: C.muted, charSpacing: 1.5,
    border: [{ type: 'none' }, { type: 'none' }, { type: 'solid', color: C.ink, pt: 1 }, { type: 'none' }] });
  s.addTable([
    [head(''), head('WORK'), head('SUCCESS CRITERION')],
    ...plan.map(([w, c], i) => [cell(String(i + 1), { fontFace: HEAD, fontSize: 13, color: C.camel }), cell(w, { fontFace: HEAD, fontSize: 11 }), cell(c, { color: C.inkSoft })]),
  ], { x: 0.6, y: 1.42, w: 8.8, colW: [0.35, 3.0, 5.45], rowH: [0.28, ...plan.map(() => 0.36)] });
  card(s, 0.6, 4.3, 8.8, 0.55, C.ink, C.ink);
  T(s, [{ text: 'OUR SUCCESS CRITERION   ', options: { bold: true, color: C.camelLight, charSpacing: 1.5, fontSize: 8 } },
    { text: `Live chat gets the right behaviour on at least ${SPRINT2_TARGET} of ${inboxTotal} inbox requests against independent labels, with no number on screen that lacks a tool source, while the desk still beats all three baselines.`, options: { color: C.onInk } }],
  { x: 0.8, y: 4.3, w: 8.4, h: 0.55, fontSize: 10, valign: 'middle' });
  s.addNotes(notesFor(9));
}

// ---- 10. Questions ----------------------------------------------------------------------
{
  const s = pres.addSlide({ masterName: 'DARK' });
  T(s, 'SWEATERCO', { x: 0.6, y: 0.5, w: 4, h: 0.3, fontFace: HEAD, fontSize: 13, color: C.onInk, charSpacing: 9 });
  T(s, 'Thank you.', { x: 0.6, y: 1.7, w: 8.8, h: 0.9, fontFace: HEAD, fontSize: 40, color: C.onInk });
  T(s, 'Questions are welcome.', { x: 0.6, y: 2.6, w: 8.8, h: 0.5, fontFace: HEAD, fontSize: 18, italic: true, color: C.onInkMuted });
  T(s, 'THE MODEL READS  /  PYTHON CALCULATES  /  A PERSON APPROVES', { x: 0.6, y: 4.2, w: 8.8, h: 0.22, fontSize: 8.5, bold: true, color: C.camel, charSpacing: 3 });
  T(s, 'GROUP 11  /  DSS5105 CAPSTONE  /  16 OCTOBER 2026', { x: 0.6, y: 5.16, w: 8.8, h: 0.2, fontSize: 7.5, color: C.onInkMuted, charSpacing: 2 });
  s.addNotes(notesFor(10, [
    'Q&A preparation. Keep each answer to one or two sentences, then offer the evidence.',
    `Why use an LLM at all? The input is chat, and only ${plainRequests} of the ${inboxTotal} inbox requests are plain allocations; the rest need a question, a refusal, a constraint or bad news. The model extracts fields and flags what is missing; it never decides numbers. The allocator itself has no LLM call.`,
    'What if the model hallucinates? Model output is a typed patch; every value must appear inside an exact quotation from the message, or Python rejects the turn (fails closed, no repair). Every number on screen is formatted by a tool, and we check that automatically.',
    'What does the model provider see? The chat text, earlier turns in that conversation, and the lists of workshop, customer and product names. Never prices, queues, defect rates or order quantities (intake.py builds the payload).',
    'What if the provider is down? The desk says the model is unavailable and asks for a retry: 30-second timeout, no silent retries. Inbox examples, the workshop register and the simulator keep working with no key.',
    'Is it AI-native? The conversation is the main interface and the model does the language work: it understands, asks, and from Sprint 2 chooses a read-only tool, explains and drafts the reply. Tools own every number; a person owns every commitment. We deliberately skip RAG (8 workshop cards and 120 rows are better served by exact tools), fine-tuning (30 labels is too few) and an LLM inside the allocator (the track forbids it). Plan: docs/AI_NATIVE_PLAN.md.',
    'Why not a multi-agent design? The course says a plain dispatcher with good tools beats a transcript. One structured-output call per turn keeps every decision in deterministic, testable Python.',
    'Scale and security? Single-node SQLite and a self-declared dispatcher name: right for a prototype, not production. Next: real authentication and a server database behind the same record contract.',
    'Earliest finish ties you, so what do you add? Chat intake, enforced constraints with who imposed them, a confirmation and audit trail, and a configurable objective that can trade cost against lateness. On lateness alone the simple rule is as good, and we say so.',
    `Why not defects? Chasing quality sends work to small, slow workshops. Pure defects is ${late(normal.defects)} late. Our best defects setting still loses to biggest-capacity on defective pieces.`,
    `Robustness? Closure raises our late rate by ${v3.paired_deltas.lateness['% late'].toFixed(2)} points. A cheating oracle that knows the closure only improves on us by about one batch in ten runs, so stall detection is not worth building for this simulator.`,
    'Cost and latency of the model? One structured-output call per chat turn. The first live run (pre-v3, docs/CHAT_EVALUATION_RESULTS.md) used 34,516 tokens and 135.5 seconds summed over 30 requests: about 1,150 tokens and 4.5 seconds each. Examples mode and the simulator need no API key at all.',
    'Audit six weeks later? Each saved allocation stores the request, constraints and who set them, every candidate estimate, weights, data hashes, who confirmed, and when.',
  ]));
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
