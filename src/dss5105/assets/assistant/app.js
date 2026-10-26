// SweaterCo dispatch assistant (Streamlit custom component, v2).
// Python sends `data` (thread, workshops, priorities, memory) and receives one trigger, `event`.
// Every text value from Python is rendered with textContent, never as HTML: cards can quote
// user messages. Only the constant icons below are inserted as markup.

const ICONS = {
  mic: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="2.5" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0"/><path d="M12 18v3.5"/></svg>',
  send: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="m5 12 7-7 7 7"/></svg>',
  sliders: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2.2"/><circle cx="10" cy="17" r="2.2"/></svg>',
  brain: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M12 5v13"/></svg>',
  check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>',
  x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m13 6 6 6-6 6"/></svg>',
  shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M12 3 5 6v5c0 4.4 3 8.3 7 10 4-1.7 7-5.6 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4" stroke-linecap="round"/></svg>',
  spark: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.5l1.9 5.6L19.5 10l-5.6 1.9L12 17.5l-1.9-5.6L4.5 10l5.6-1.9L12 2.5Z"/></svg>',
  alert: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
  help: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.3a2.6 2.6 0 0 1 5 .9c0 1.7-2.5 2.4-2.5 2.4M12 16.8h.01"/></svg>',
  ear: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8.5a6 6 0 1 1 12 0c0 3.5-3 4.3-3 7.5a3 3 0 0 1-6 0"/><path d="M9.5 8.5a2.5 2.5 0 1 1 5 0"/></svg>',
  file: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5"/></svg>',
  gauge: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 18a8 8 0 1 1 16 0"/><path d="m12 18 4-6"/></svg>',
  scale: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v16M7 20h10M5 8h14"/><path d="m5 8-3 6a3 3 0 0 0 6 0Zm14 0-3 6a3 3 0 0 0 6 0Z"/></svg>',
  chat: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="M4 5h16v11H9l-5 4z"/></svg>',
  keyboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h.01M11 10h.01M15 10h.01M7 14h10"/></svg>',
};
const STAGE_ICONS = {
  Heard: "ear",
  Understand: "spark",
  Validate: "shield",
  Request: "file",
  "Order lookup": "file",
  Eligibility: "shield",
  Estimates: "gauge",
  Memory: "brain",
  Rank: "scale",
  Split: "scale",
  Outcome: "check",
  Reply: "chat",
};
const THINKING = ["Reading your request", "Checking every workshop", "Estimating delivery", "Ranking the options"];
const PALETTE = ["#ff7a45", "#ff3d6e", "#7c4dff", "#2f6fec", "#0f9f55", "#c77700", "#0ea5b7", "#d946ef"];
const SEGMENT_LABELS = { queue: "Queue", processing: "Processing", transport: "Transport", expected_rework: "Expected rework" };

function icon(name) {
  const span = document.createElement("span");
  span.style.display = "contents";
  span.innerHTML = ICONS[name] || "";
  return span.firstElementChild || span;
}

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === null || value === undefined || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "style") node.setAttribute("style", value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function put(node, ...children) {
  for (const child of children.flat()) {
    if (child !== null && child !== undefined && child !== false) node.append(child);
  }
  return node;
}

function hue(id) {
  let sum = 0;
  for (const ch of String(id)) sum = (sum * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTE[sum % PALETTE.length];
}

// Each edit of this file loads as a new module URL; an instance from an older build is replaced.
const BUILD = import.meta.url;

function createApp(root) {
  const $ = (id) => root.querySelector("#" + id);
  for (const id of ["thread", "stories", "pipeline", "behindFoot", "sheetBody"]) $(id).replaceChildren();
  for (const id of ["memoryBtn", "prioritiesBtn", "listenCancel", "listenDone", "micIcon"]) $(id).replaceChildren();
  // Every listener on the persistent markup is removed together when this instance is destroyed.
  const listeners = new AbortController();
  const on = (target, type, handler) => target.addEventListener(type, handler, { signal: listeners.signal });
  const nodes = {
    thread: $("thread"),
    stories: $("stories"),
    input: $("textInput"),
    mic: $("micBtn"),
    micIcon: $("micIcon"),
    listen: $("listen"),
    listenText: $("listenText"),
    listenState: $("listenState"),
    listenHint: $("listenHint"),
    scrim: $("scrim"),
    sheet: $("sheet"),
    sheetBody: $("sheetBody"),
    toast: $("toast"),
    pipeline: $("pipeline"),
    behindTitle: $("behindTitle"),
    behindFoot: $("behindFoot"),
  };
  const state = {
    data: null,
    trigger: null,
    rendered: new Map(),
    initialized: false,
    busy: false,
    waitingFor: null,
    busyTimer: null,
    thinkingTimer: null,
    spoken: new Set(),
    sheet: null,
    sheetData: null,
    bookingKey: null,
    notice: null,
    nonce: 0,
    recognition: null,
    listening: false,
    finalText: "",
    interimText: "",
    pressStart: 0,
    holdMode: false,
    cancelled: false,
    voices: [],
  };

  // Static header buttons and composer --------------------------------------------------
  $("memoryBtn").append(icon("brain"));
  $("prioritiesBtn").append(icon("sliders"));
  $("listenCancel").append(icon("x"));
  $("listenDone").append(icon("check"));
  nodes.micIcon.append(icon("mic"));
  on($("memoryBtn"), "click", () => openSheet("memory"));
  on($("prioritiesBtn"), "click", () => openSheet("priorities"));
  on($("profileBtn"), "click", () => openSheet("profile"));
  on(nodes.scrim, "click", closeSheet);
  on($("composer"), "submit", (event) => {
    event.preventDefault();
    submitText();
  });
  on(nodes.input, "input", syncComposer);
  on($("listenCancel"), "click", () => stopListening(true));
  on($("listenDone"), "click", () => stopListening(false));
  on(root, "keydown", (event) => {
    if (event.key === "Escape") {
      if (state.listening) stopListening(true);
      else closeSheet();
    }
  });

  // Microphone: tap to toggle, or hold and release to send.
  on(nodes.mic, "pointerdown", (event) => {
    if (nodes.input.value.trim()) return;
    if (state.busy) return toast("One moment, still working on the last request.");
    event.preventDefault();
    if (state.listening) return stopListening(false);
    // Keep receiving this press after the listening overlay covers the button.
    nodes.mic.setPointerCapture?.(event.pointerId);
    state.pressStart = performance.now();
    state.holdMode = false;
    startListening();
    clearTimeout(state.holdTimer);
    state.holdTimer = setTimeout(() => {
      state.holdMode = true;
      nodes.listenHint.textContent = "Release to send";
    }, 380);
  });
  const release = () => {
    clearTimeout(state.holdTimer);
    if (state.listening && state.holdMode) stopListening(false);
  };
  on(nodes.mic, "pointerup", release);
  on(nodes.mic, "pointercancel", release);
  on(nodes.mic, "click", (event) => {
    if (nodes.input.value.trim()) {
      event.preventDefault();
      submitText();
    }
  });
  syncComposer();

  if ("speechSynthesis" in window) {
    const loadVoices = () => (state.voices = window.speechSynthesis.getVoices());
    loadVoices();
    on(window.speechSynthesis, "voiceschanged", loadVoices);
  }

  // Events to Python -------------------------------------------------------------------
  function emit(payload) {
    if (!state.trigger) return;
    state.nonce += 1;
    state.trigger("event", { ...payload, nonce: `${Date.now()}-${state.nonce}` });
  }

  function emitAndWait(payload) {
    if (state.busy) return toast("One moment, still working on the last request.");
    setBusy(true);
    emit(payload);
  }

  function sendUtterance(text, channel) {
    const clean = (text || "").trim();
    if (!clean) return;
    if (state.busy) return toast("One moment, still working on the last request.");
    window.speechSynthesis?.cancel();
    appendOptimistic(clean, channel);
    setBusy(true);
    emit({ type: "utterance", text: clean, channel });
  }

  function submitText() {
    const text = nodes.input.value;
    if (!text.trim()) return;
    nodes.input.value = "";
    syncComposer();
    sendUtterance(text, "text");
  }

  function syncComposer() {
    const typing = Boolean(nodes.input.value.trim());
    nodes.micIcon.replaceChildren(icon(typing ? "send" : "mic"));
    nodes.mic.setAttribute("aria-label", typing ? "Send" : "Hold to talk, or tap to start and stop");
  }

  function setBusy(on) {
    state.busy = on;
    nodes.mic.classList.toggle("busy", on);
    clearTimeout(state.busyTimer);
    clearInterval(state.thinkingTimer);
    root.querySelector(".msg.thinking")?.remove();
    if (on) {
      state.waitingFor = state.data ? state.data.v : 0;
      const label = el("span", { text: THINKING[0] });
      const bubble = el("div", { class: "msg thinking" }, el("div", { class: "typing" }, el("div", { class: "dots" }, el("i"), el("i"), el("i")), label));
      nodes.thread.append(bubble);
      let step = 0;
      state.thinkingTimer = setInterval(() => {
        step = Math.min(step + 1, THINKING.length - 1);
        label.textContent = THINKING[step];
      }, 1100);
      scrollDown();
      state.busyTimer = setTimeout(() => {
        setBusy(false);
        toast("That is taking longer than usual. Try again in a moment.");
      }, 90000);
    } else {
      root.querySelectorAll(".msg.pending").forEach((node) => node.remove());
    }
  }

  function appendOptimistic(text, channel) {
    const bubble = el("div", { class: "bubble" + (channel === "voice" ? " voice" : "") }, text);
    if (channel === "voice") bubble.append(el("div", { class: "via" }, icon("mic"), "Spoken"));
    nodes.thread.append(el("div", { class: "msg user pending" }, bubble));
    scrollDown();
  }

  // Speech -------------------------------------------------------------------------------
  function recognitionClass() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }

  function startListening() {
    const Recognition = recognitionClass();
    if (!Recognition) {
      toast("Voice input needs Chrome, Edge or Safari. You can type instead.");
      nodes.input.focus();
      return;
    }
    window.speechSynthesis?.cancel();
    state.finalText = "";
    state.interimText = "";
    state.cancelled = false;
    const recognition = new Recognition();
    recognition.lang = (state.data && state.data.lang) || "en-US";
    recognition.interimResults = true;
    recognition.continuous = true;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const text = event.results[i][0].transcript;
        if (event.results[i].isFinal) state.finalText += text;
        else interim += text;
      }
      state.interimText = interim;
      renderTranscript();
    };
    recognition.onerror = (event) => {
      const messages = {
        "not-allowed": "Microphone access is blocked. Allow it in the browser, or type instead.",
        "service-not-allowed": "Microphone access is blocked. Allow it in the browser, or type instead.",
        "no-speech": "I didn't hear anything. Hold the button and speak.",
        network: "Speech recognition needs a network connection. You can type instead.",
        "audio-capture": "No microphone was found. You can type instead.",
      };
      if (event.error !== "aborted") toast(messages[event.error] || "Voice input stopped. You can type instead.");
      state.cancelled = true;
    };
    recognition.onend = () => {
      const text = (state.finalText + " " + state.interimText).trim();
      const send = !state.cancelled && text;
      state.listening = false;
      state.recognition = null;
      nodes.mic.classList.remove("hot");
      nodes.listen.hidden = true;
      if (send) sendUtterance(text, "voice");
    };
    try {
      recognition.start();
    } catch (error) {
      toast("Voice input could not start. You can type instead.");
      return;
    }
    state.recognition = recognition;
    state.listening = true;
    nodes.mic.classList.add("hot");
    nodes.listen.hidden = false;
    nodes.listenState.textContent = "Listening";
    nodes.listenHint.textContent = "Tap the tick when you're done";
    renderTranscript();
  }

  function stopListening(cancel) {
    if (!state.recognition) return;
    state.cancelled = Boolean(cancel);
    nodes.listenState.textContent = cancel ? "Cancelled" : "Got it";
    try {
      state.recognition.stop();
    } catch (error) {
      state.recognition = null;
    }
  }

  function renderTranscript() {
    const final = state.finalText.trim();
    const interim = state.interimText.trim();
    nodes.listenText.replaceChildren();
    if (!final && !interim) {
      nodes.listenText.append(el("span", { class: "interim", text: "Say an order, a quantity and a date\u2026" }));
      return;
    }
    if (final) nodes.listenText.append(final + " ");
    if (interim) nodes.listenText.append(el("span", { class: "interim", text: interim }));
  }

  function speak(text) {
    if (!text || !("speechSynthesis" in window) || !(state.data && state.data.profile.speak)) return;
    const utterance = new SpeechSynthesisUtterance(text);
    const preferred = state.voices.find((v) => /Samantha|Google US English|Jenny|Aria/i.test(v.name));
    const english = preferred || state.voices.find((v) => v.lang && v.lang.startsWith("en"));
    if (english) utterance.voice = english;
    utterance.rate = 1.04;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  // Rendering -------------------------------------------------------------------------
  function scrollDown() {
    requestAnimationFrame(() => {
      nodes.thread.scrollTop = nodes.thread.scrollHeight;
    });
  }

  function toast(text) {
    nodes.toast.textContent = text;
    nodes.toast.hidden = false;
    clearTimeout(state.toastTimer);
    state.toastTimer = setTimeout(() => (nodes.toast.hidden = true), 4200);
  }

  function renderHeader(data) {
    const name = data.profile.name;
    $("avatarText").textContent = data.profile.initials;
    const hour = new Date().getHours();
    const part = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
    $("helloTitle").textContent = name ? `${part}, ${name}` : part;
    $("helloSub").textContent = `${data.plan.as_of_label} \u00b7 ${data.plan.bookings} booked`;
    const memoryBtn = $("memoryBtn");
    memoryBtn.querySelector(".dot")?.remove();
    if (data.memory.rules.length) memoryBtn.append(el("span", { class: "dot", text: String(data.memory.rules.length) }));
  }

  function renderStories(data) {
    nodes.stories.replaceChildren(
      ...data.workshops.map((w) => {
        const load = Math.max(0.04, Math.min(1, w.load));
        const ring = w.status !== "ACTIVE" ? "#bdb9b2" : load < 0.35 ? "#0f9f55" : load < 0.7 ? "#e59a0b" : "#e5484d";
        const face = el("div", { class: "story-face", style: `--face:${hue(w.id)}` }, w.initials);
        if (w.tag) face.append(el("span", { class: "tag", text: w.tag }));
        return el(
          "button",
          {
            class: "story" + (w.status !== "ACTIVE" ? " off" : ""),
            role: "listitem",
            type: "button",
            "aria-label": `${w.name}: ${w.status === "ACTIVE" ? w.queue + " queued" : w.status.toLowerCase()}`,
            onclick: () => openSheet("workshop", w),
          },
          el("div", { class: "story-ring", style: `--load:${load};--ring:${ring}` }, face),
          el("div", { class: "story-name", text: w.name }),
        );
      }),
    );
  }

  function pill(card) {
    const names = { ok: "check", ask: "help", warn: "alert", bad: "alert", info: "spark" };
    return el("span", { class: "pill" }, icon(names[card.tone] || "spark"), card.label);
  }

  function timeline(tl) {
    if (!tl) return null;
    const span = Math.max(tl.total_days, tl.deadline_days > 0 ? tl.deadline_days : 0) * 1.04 || 1;
    const bar = el("div", { class: "tl-bar", role: "img", "aria-label": `Expected ${tl.total}; deadline marked` });
    for (const seg of tl.segments) {
      if (seg.days <= 0) continue;
      bar.append(el("div", { class: `tl-seg seg-${seg.key}`, style: `width:${(100 * seg.days) / span}%`, title: `${seg.label}: ${seg.shown}` }));
    }
    if (tl.deadline_days > 0) {
      bar.append(el("div", { class: "tl-deadline", style: `left:${(100 * tl.deadline_days) / span}%` }, el("span", { text: "Due" })));
    }
    const legend = el(
      "div",
      { class: "tl-legend" },
      tl.segments.filter((s) => s.days > 0).map((s) => el("span", {}, el("i", { class: `seg-${s.key}` }), `${SEGMENT_LABELS[s.key]} ${s.shown}`)),
    );
    return el("div", { class: "timeline" }, bar, legend);
  }

  function stat(label, value, cls) {
    return el("div", { class: "stat" }, el("div", { class: "stat-k", text: label }), el("div", { class: "stat-v" + (cls ? " " + cls : ""), text: value }));
  }

  function optionCard(option) {
    return el(
      "div",
      { class: "opt" + (option.selected ? " sel" : "") },
      el(
        "div",
        { class: "opt-head" },
        el("div", { class: "ws-avatar", style: `--face:${hue(option.workshop_id)}`, text: option.initials }),
        el("div", {}, el("div", { class: "opt-name", text: option.name }), el("div", { class: "opt-rank", text: option.selected ? `#${option.rank} \u00b7 Recommended` : `#${option.rank}` })),
      ),
      el(
        "div",
        { class: "opt-grid" },
        el("div", {}, el("span", { text: "Arrives " }), el("b", { text: option.eta_day })),
        el("div", {}, el("span", { text: "Takes " }), el("b", { text: option.turnaround })),
        el("div", {}, el("span", { text: "Cost " }), el("b", { text: "$" + option.cost })),
        el("div", {}, el("span", { text: "Defects " }), el("b", { text: option.defects })),
      ),
      el("span", { class: "badge " + (option.on_time ? "ok" : "late"), text: option.on_time ? "Meets the date" : `Late ${option.lateness}` }),
    );
  }

  function details(summary, body, open) {
    const node = el("details", { class: "more" }, el("summary", {}, summary, icon("chevron")), body);
    if (open) node.open = true;
    return node;
  }

  function cardActions(card, message) {
    const row = el("div", { class: "actions" });
    for (const action of card.actions || []) {
      row.append(
        el(
          "button",
          {
            class: "btn " + (action.primary ? "primary brand" : "secondary"),
            type: "button",
            onclick: () => {
              if (action.id === "book") emitAndWait({ type: "book", message: message.id });
              if (action.id === "retry") emitAndWait({ type: "retry" });
            },
          },
          action.id === "book" ? icon("check") : null,
          action.label,
        ),
      );
    }
    return row.childElementCount ? row : null;
  }

  function choicesRow(card) {
    const chips = [];
    for (const choice of card.choices || []) {
      chips.push(
        el("button", { class: "chip", type: "button", onclick: () => {
          appendOptimistic(choice.text, "tap");
          emitAndWait({ type: "choice", choice });
        } }, choice.label),
      );
    }
    for (const text of card.suggestions || []) {
      chips.push(el("button", { class: "chip suggest", type: "button", onclick: () => sendUtterance(text, "chip") }, text));
    }
    return chips.length ? el("div", { class: "choices" }, chips) : null;
  }

  function resultCard(card, message) {
    const order = card.order;
    const meta = order ? [order.order_id, order.customer, order.pieces && `${order.pieces} ${order.product}`].filter(Boolean).join(" \u00b7 ") : "";
    const node = el("article", { class: `card tone-${card.tone}` }, el("div", { class: "card-top" }, pill(card), el("span", { class: "meta", text: meta })));
    node.append(el("h3", { class: "headline", text: card.headline }));
    if (card.sub) node.append(el("p", { class: "sub", text: card.sub }));
    const pick = card.pick;
    if (pick) {
      node.append(
        el(
          "div",
          { class: "pick" },
          el("div", { class: "ws-avatar", style: `--face:${hue(pick.workshop_id)}`, text: pick.initials }),
          el("div", { class: "pick-main" }, el("div", { class: "pick-name", text: pick.name }), el("div", { class: "pick-note", text: pick.notes })),
          el("div", { class: "pick-eta" }, el("div", { class: "eta-day", text: pick.eta_day }), el("div", { class: "eta-sub", text: "Estimated arrival" })),
        ),
        el(
          "div",
          { class: "stats" },
          pick.on_time ? stat("Spare", pick.slack || "On time", "good") : stat("Late by", pick.lateness, "badv"),
          stat("Cost", "$" + pick.cost),
          stat("Defect risk", pick.defects),
        ),
      );
      put(node, timeline(card.timeline));
    }
    for (const memory of card.memory || []) {
      node.append(el("div", { class: "memory-chip" }, icon("brain"), el("div", {}, el("b", { text: "From memory: " }), memory.text, el("small", { text: `${memory.by} \u00b7 "${memory.evidence}"` }))));
    }
    if (card.reasons && card.reasons.length) node.append(el("ul", { class: "reasons" }, card.reasons.map((r) => el("li", { text: r }))));
    if (card.notes && card.notes.length) node.append(el("ul", { class: "notes" }, card.notes.map((n) => el("li", { text: n }))));
    put(node, choicesRow(card));
    if (card.options && card.options.length > 1) {
      node.append(details(`Compare ${card.options.length} workshops`, el("div", { class: "carousel" }, card.options.map(optionCard)), false));
    }
    if (card.excluded && card.excluded.length) {
      node.append(details(`Can't take it (${card.excluded.length})`, el("ul", { class: "excluded" }, card.excluded.map((row) => el("li", {}, el("b", { text: row.name }), el("span", { text: row.reason })))), false));
    }
    put(node, cardActions(card, message));
    node.append(
      el(
        "div",
        { class: "foot" },
        icon("shield"),
        el("span", { text: card.source === "inbox fixture" ? "Inbox example, no model call \u00b7 numbers from Python tools" : "Numbers from Python tools" }),
        card.evidence_id ? el("span", { text: "\u00b7 " + card.evidence_id }) : null,
        card.trace && card.trace.length ? el("button", { type: "button", text: "How?", onclick: () => openSheet("trace", card) }) : null,
      ),
    );
    return node;
  }

  function receiptCard(card) {
    const r = card.receipt;
    const node = el("article", { class: "card receipt tone-ok" }, el("div", { class: "receipt-mark" }, icon("check")), el("h3", { class: "headline", text: card.headline }));
    node.append(
      el(
        "div",
        { class: "facts" },
        [
          ["Arrives", r.eta_day],
          ["Pieces", r.pieces],
          ["Cost", "$" + r.cost],
          ["Reserved", r.reserved],
          ["Confirmed by", r.by],
          ["Reference", r.reference],
        ].map(([k, v]) => el("div", { class: "fact" }, el("span", { text: k }), el("b", { text: v }))),
      ),
      el("div", { class: "foot" }, icon("shield"), el("span", { text: r.effect })),
    );
    for (const offer of card.offers || []) {
      node.append(
        el(
          "div",
          { class: "offer", "data-offer": String(offer.index) },
          el("div", { class: "offer-title" }, icon("brain"), offer.text),
          el("p", { text: `From ${offer.by}: "${offer.evidence.replace(/[.!\s]+$/, "")}"` }),
          el("p", { text: "I'll apply it to this customer's future orders, and show you when I do." }),
          el(
            "div",
            { class: "actions" },
            el("button", { class: "btn secondary", type: "button", onclick: (e) => e.target.closest(".offer").remove() }, "Not now"),
            el("button", { class: "btn primary", type: "button", onclick: () => emitAndWait({ type: "remember", index: offer.index }) }, "Remember"),
          ),
        ),
      );
    }
    return node;
  }

  function infoCard(card, message) {
    const node = el("article", { class: `card tone-${card.tone}` }, el("div", { class: "card-top" }, pill(card)), el("h3", { class: "headline", text: card.headline }));
    if (card.facts) node.append(el("div", { class: "facts" }, card.facts.map(([k, v]) => el("div", { class: "fact" }, el("span", { text: k }), el("b", { text: v })))));
    if (card.bookings && card.bookings.length) {
      node.append(
        el(
          "ul",
          { class: "rows" },
          card.bookings.map((b) =>
            el("li", {}, el("div", { class: "ws-avatar", style: `--face:${hue(b.workshop)};width:34px;height:34px;border-radius:11px;font-size:12px`, text: b.workshop.slice(0, 2).toUpperCase() }), el("div", { class: "grow" }, el("b", { text: `${b.order_id} \u2192 ${b.workshop}` }), el("small", { text: `${b.pieces} ${b.product} for ${b.customer} \u00b7 arrives ${b.eta_day} \u00b7 by ${b.by}` }))),
          ),
        ),
      );
    }
    if (card.rules && card.rules.length) {
      node.append(el("ul", { class: "rows" }, card.rules.map((r) => el("li", {}, el("div", { class: "grow" }, el("b", { text: r.text }), el("small", { text: `${r.by}: "${r.evidence}"` }))))));
    }
    if (card.notes && card.notes.length) node.append(el("ul", { class: "notes" }, card.notes.map((n) => el("li", { text: n }))));
    put(node, choicesRow(card));
    put(node, cardActions(card, message));
    return node;
  }

  function renderMessage(message) {
    if (message.role === "user") {
      const bubble = el("div", { class: "bubble" + (message.channel === "voice" ? " voice" : "") }, message.text);
      const via = { voice: ["mic", "Spoken"], tap: ["check", "Tapped"], chip: ["spark", "Suggestion"] }[message.channel];
      if (via) bubble.append(el("div", { class: "via" }, icon(via[0]), via[1]));
      return el("div", { class: "msg user", "data-id": message.id }, bubble);
    }
    const card = message.card;
    if (card.kind === "divider") return el("div", { class: "divider", "data-id": message.id, text: "New request" });
    let body;
    if (card.kind === "result") body = resultCard(card, message);
    else if (card.kind === "receipt") body = receiptCard(card);
    else body = infoCard(card, message);
    return el("div", { class: "msg assistant", "data-id": message.id }, body);
  }

  function renderThread(data) {
    const ids = new Set(data.thread.map((m) => m.id));
    for (const [id, node] of state.rendered) {
      if (!ids.has(id)) {
        node.remove();
        state.rendered.delete(id);
      }
    }
    const added = [];
    for (const message of data.thread) {
      if (state.rendered.has(message.id)) continue;
      const node = renderMessage(message);
      if (!state.initialized) node.style.animation = "none";
      nodes.thread.append(node);
      state.rendered.set(message.id, node);
      added.push({ message, node });
    }
    // Only the latest answer keeps live buttons; older cards become history.
    const assistants = data.thread.filter((m) => m.role === "assistant");
    const latest = assistants.length ? assistants[assistants.length - 1].id : null;
    for (const message of assistants) {
      state.rendered.get(message.id)?.querySelector(".card")?.classList.toggle("stale", message.id !== latest);
    }
    const thinking = root.querySelector(".msg.thinking");
    if (thinking) nodes.thread.append(thinking);
    if (added.length) {
      // Show what is new from its top: the question if there is one, otherwise the first new card.
      const first = (added.find((item) => item.message.role === "user") || added[0]).node;
      if (state.initialized) requestAnimationFrame(() => (nodes.thread.scrollTop = Math.max(0, first.offsetTop - 12)));
      else scrollDown();
    }
  }

  function renderBehind(data) {
    const latest = [...data.thread].reverse().find((m) => m.role === "assistant" && m.card && m.card.trace && m.card.trace.length);
    const said = latest ? [...data.thread.slice(0, data.thread.indexOf(latest))].reverse().find((m) => m.role === "user") : null;
    nodes.pipeline.replaceChildren();
    if (!latest) {
      nodes.behindTitle.textContent = "Waiting for a request";
      nodes.pipeline.append(el("li", {}, el("div", { class: "step-dot" }, icon("ear")), el("div", {}, el("div", { class: "step-title", text: "Speak or type a request" }), el("div", { class: "step-detail", text: "Each step of the answer appears here: what the model extracted, which tool checked what, and how the workshops were ranked." }))));
    } else {
      nodes.behindTitle.textContent = latest.card.headline;
      const steps = [];
      if (said) steps.push({ stage: "Heard", actor: said.channel === "voice" ? "Browser speech recognition" : said.channel === "tap" ? "Tapped answer" : "Typed", detail: `"${said.text}"` });
      steps.push(...latest.card.trace);
      steps.push({ stage: "Reply", actor: "Python template", detail: latest.card.speak || latest.card.headline });
      steps.forEach((step, i) => {
        const model = step.stage === "Understand" && !/fixture|selection|no model/i.test(step.actor);
        nodes.pipeline.append(
          el(
            "li",
            { style: `animation-delay:${i * 60}ms` },
            el("div", { class: "step-dot" + (model ? " model" : step.stage === "Outcome" ? " done" : "") }, icon(STAGE_ICONS[step.stage] || "spark")),
            el("div", {}, el("div", { class: "step-title" }, step.stage, el("span", { class: "step-actor", text: step.actor })), el("div", { class: "step-detail", text: step.detail })),
          ),
        );
      });
    }
    const w = data.weights;
    nodes.behindFoot.replaceChildren(
      el("div", { text: `Priorities: ${data.preset_label}. Primary objective: minimise lateness; secondary: minimise defects.` }),
      el(
        "div",
        { class: "weights" },
        data.objectives.map((o) => el("span", {}, o.short + " ", el("b", { text: Number(w[o.id]).toFixed(2) }))),
        el("span", {}, "Buffer ", el("b", { text: `${w.deadline_buffer_days} d` })),
        el("span", {}, "Reserve ", el("b", { text: w.capacity_reservation ? "on" : "off" })),
        el("span", {}, "On-time first ", el("b", { text: w.deadline_miss_days ? "on" : "off" })),
      ),
      el("div", { style: "margin-top:10px", text: `Model: ${data.model.label}. Plan revision ${data.plan.revision}; memory holds ${data.memory.rules.length} rule(s) and ${data.memory.episodes.length} recent episode(s).` }),
    );
  }

  // Sheets ---------------------------------------------------------------------------------
  function openSheet(kind, payload) {
    state.sheet = kind;
    state.sheetData = payload || null;
    renderSheet();
    nodes.scrim.hidden = false;
    nodes.sheet.hidden = false;
    nodes.sheet.querySelector("button, input")?.focus({ preventScroll: true });
  }

  function closeSheet() {
    if (state.sheet === "booking" && state.data && state.data.booking) emit({ type: "cancel_booking" });
    state.sheet = null;
    nodes.scrim.hidden = true;
    nodes.sheet.hidden = true;
  }

  function renderSheet() {
    const data = state.data;
    if (!data || !state.sheet) return;
    const body = nodes.sheetBody;
    body.replaceChildren();
    const builders = { priorities: prioritiesSheet, memory: memorySheet, workshop: workshopSheet, booking: bookingSheet, profile: profileSheet, trace: traceSheet };
    const content = builders[state.sheet] && builders[state.sheet](data, state.sheetData);
    if (content) body.append(...[].concat(content));
    else closeSheet();
  }

  function prioritiesSheet(data) {
    const draft = { ...data.weights };
    const outputs = {};
    const sliders = {};
    const presetRow = el("div", { class: "presets" });
    const paint = () => {
      for (const o of data.objectives) {
        const input = sliders[o.id];
        input.value = draft[o.id];
        input.style.setProperty("--fill", `${(100 * draft[o.id]) / o.max}%`);
        outputs[o.id].textContent = Number(draft[o.id]).toFixed(2);
      }
      sliders.buffer.value = draft.deadline_buffer_days;
      sliders.buffer.style.setProperty("--fill", `${(100 * draft.deadline_buffer_days) / 10}%`);
      outputs.buffer.textContent = `${draft.deadline_buffer_days} days`;
      reserve.setAttribute("aria-checked", draft.capacity_reservation > 0 ? "true" : "false");
      onTime.setAttribute("aria-checked", draft.deadline_miss_days > 0 ? "true" : "false");
      for (const button of presetRow.children) {
        const preset = data.presets.find((p) => p.id === button.dataset.id);
        button.classList.toggle("on", Object.keys(preset.weights).every((k) => Number(preset.weights[k]) === Number(draft[k])));
      }
    };
    for (const preset of data.presets) {
      presetRow.append(el("button", { class: "preset", type: "button", "data-id": preset.id, onclick: () => { Object.assign(draft, preset.weights); paint(); } }, el("b", { text: preset.label }), el("small", { text: preset.hint })));
    }
    const rows = data.objectives.map((o) => {
      const output = el("output", {});
      const input = el("input", { type: "range", min: "0", max: String(o.max), step: "0.01", "aria-label": o.label, style: `--track:${o.color}` });
      input.addEventListener("input", () => { draft[o.id] = Number(input.value); paint(); });
      outputs[o.id] = output;
      sliders[o.id] = input;
      return el("div", { class: "slider" }, el("div", { class: "slider-top" }, el("b", { text: o.label }), output), el("small", { text: o.hint }), input);
    });
    const bufferOut = el("output", {});
    const buffer = el("input", { type: "range", min: "0", max: "10", step: "0.5", "aria-label": "Safety buffer in days" });
    buffer.addEventListener("input", () => { draft.deadline_buffer_days = Number(buffer.value); paint(); });
    outputs.buffer = bufferOut;
    sliders.buffer = buffer;
    const reserve = el("button", { class: "switch", type: "button", role: "switch", "aria-label": "Protect scarce shared capacity" });
    reserve.addEventListener("click", () => { draft.capacity_reservation = draft.capacity_reservation > 0 ? 0 : 1; paint(); });
    const onTime = el("button", { class: "switch", type: "button", role: "switch", "aria-label": "On-time first" });
    onTime.addEventListener("click", () => { draft.deadline_miss_days = draft.deadline_miss_days > 0 ? 0 : 7; paint(); });
    const apply = el("button", { class: "btn primary", type: "button", onclick: () => { emitAndWait({ type: "set_weights", weights: draft }); closeSheet(); } }, "Apply and re-rank");
    paint();
    return [
      el("h3", { text: "Priorities" }),
      el("p", { class: "lead", text: "Choose what matters for this desk. Workshop rules always apply; priorities only change the order of permitted options." }),
      presetRow,
      el("div", { class: "section-title", text: "Objectives" }),
      ...rows,
      el("div", { class: "section-title", text: "Lateness settings" }),
      el("div", { class: "slider" }, el("div", { class: "slider-top" }, el("b", { text: "Safety buffer" }), bufferOut), el("small", { text: "Prefer workshops that finish this many days before the deadline." }), buffer),
      el("div", { class: "switch-row" }, el("div", { class: "grow" }, el("b", { text: "On-time first" }), el("small", { text: "Never prefer a late workshop over one that meets the date." })), onTime),
      el("div", { class: "switch-row" }, el("div", { class: "grow" }, el("b", { text: "Protect scarce capacity" }), el("small", { text: "Keep workshops that also make accessories free when a tops-only shop meets the date." })), reserve),
      el("div", { class: "objective-note" }, el("b", { text: "Team objective: " }), "minimise lateness first, then defects. Each preset was chosen on development seeds before the course seeds were run; see the objective study."),
      el("div", { class: "actions" }, apply),
    ];
  }

  function memorySheet(data, tab) {
    const current = tab || "rules";
    const tabs = el(
      "div",
      { class: "segmented" },
      [["rules", "Rules"], ["bookings", "Bookings"], ["history", "History"]].map(([id, label]) =>
        el("button", { class: current === id ? "on" : "", type: "button", onclick: () => { state.sheetData = id; renderSheet(); } }, label),
      ),
    );
    let list;
    if (current === "rules") {
      list = data.memory.rules.length
        ? el(
            "ul",
            { class: "rows" },
            data.memory.rules.map((rule) => {
              const toggle = el("button", { class: "switch", type: "button", role: "switch", "aria-checked": rule.active ? "true" : "false", "aria-label": `${rule.active ? "Pause" : "Resume"} rule` });
              toggle.addEventListener("click", () => emitAndWait({ type: "rule_toggle", rule_id: rule.rule_id, active: !rule.active }));
              return el("li", {}, el("div", { class: "grow" }, el("b", { text: rule.summary }), el("small", { text: `${rule.imposed_by}, ${rule.created_on}: "${rule.evidence}"` })), toggle);
            }),
          )
        : el("div", { class: "empty", text: "No standing rules yet. When you confirm a booking that had a constraint, I offer to remember it." });
    } else if (current === "bookings") {
      list = data.memory.bookings.length
        ? el("ul", { class: "rows" }, data.memory.bookings.map((b) => el("li", {}, el("div", { class: "grow" }, el("b", { text: `${b.order_id} \u2192 ${b.workshop}` }), el("small", { text: `${b.pieces} ${b.product} for ${b.customer} \u00b7 arrives ${b.eta_day} \u00b7 ${b.by}` })))))
        : el("div", { class: "empty", text: "Nothing booked in this plan yet." });
    } else {
      list = data.memory.episodes.length
        ? el("ul", { class: "rows" }, data.memory.episodes.map((e) => el("li", {}, el("div", { class: "grow" }, el("b", { text: e.title }), el("small", { text: e.detail })))))
        : el("div", { class: "empty", text: "Conversations you have here are logged for audit." });
    }
    return [
      el("h3", { text: "Memory" }),
      el("p", { class: "lead", text: "What this desk remembers across sessions. Rules are learned only from bookings you confirmed, and keep the original words and who said them." }),
      tabs,
      list,
    ];
  }

  function workshopSheet(data, w) {
    const live = data.workshops.find((x) => x.id === w.id) || w;
    return [
      el("div", { class: "book-hero" }, el("div", { class: "ws-avatar", style: `--face:${hue(live.id)}`, text: live.initials }), el("div", {}, el("div", { class: "pick-name", text: live.name }), el("div", { class: "pick-note", text: live.notes }))),
      el(
        "div",
        { class: "facts" },
        [["Status", live.status_label], ["Makes", live.makes], ["Capacity", live.capacity], ["Queue now", live.queue], ["Transport", live.lead], ["Defect risk", live.defects], ["Cost per piece", "$" + live.cost], ["Batch limit", live.limit], ["Booked in plan", live.booked]].map(([k, v]) => el("div", { class: "fact" }, el("span", { text: k }), el("b", { text: v }))),
      ),
      el("div", { class: "actions" }, el("button", { class: "btn secondary", type: "button", onclick: () => { closeSheet(); sendUtterance(`How busy is ${live.name}?`, "chip"); } }, "Ask about it")),
    ];
  }

  function bookingSheet(data) {
    const b = data.booking;
    if (!b) return null;
    const nameInput = el("input", { class: "text-field", type: "text", placeholder: "Your name", value: data.profile.name || "", "aria-label": "Confirming dispatcher", maxlength: "60" });
    const slide = el("div", { class: "slide", role: "group", "aria-label": "Slide to book" });
    const fill = el("div", { class: "slide-fill" });
    const knob = el("button", { class: "slide-knob", type: "button", "aria-label": "Slide or press Enter to confirm" }, icon("arrow"));
    slide.append(fill, el("div", { class: "slide-label", text: `Slide to book ${b.workshop}` }), knob);
    const confirm = () => {
      const actor = nameInput.value.trim();
      if (!actor) {
        nameInput.focus();
        toast("Enter your name: every booking records who confirmed it.");
        return false;
      }
      slide.classList.add("done");
      knob.style.left = `${slide.clientWidth - 55}px`;
      navigator.vibrate?.(20);
      state.bookingKey = b.key;
      setTimeout(() => {
        state.sheet = null;
        nodes.scrim.hidden = true;
        nodes.sheet.hidden = true;
        emitAndWait({ type: "confirm", actor });
      }, 260);
      return true;
    };
    let startX = null;
    knob.addEventListener("pointerdown", (event) => {
      startX = event.clientX;
      knob.setPointerCapture(event.pointerId);
    });
    knob.addEventListener("pointermove", (event) => {
      if (startX === null) return;
      const max = slide.clientWidth - 60;
      const offset = Math.max(0, Math.min(max, event.clientX - startX));
      knob.style.left = `${5 + offset}px`;
      fill.style.width = `${60 + offset}px`;
    });
    knob.addEventListener("pointerup", (event) => {
      if (startX === null) return;
      const max = slide.clientWidth - 60;
      const offset = event.clientX - startX;
      startX = null;
      if (offset >= max * 0.9 && confirm()) return;
      knob.style.left = "5px";
      fill.style.width = "60px";
    });
    knob.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        confirm();
      }
    });
    return [
      el("h3", { text: "Confirm booking" }),
      el("div", { class: "book-hero" }, el("div", { class: "ws-avatar", style: `--face:${hue(b.workshop_id)}`, text: b.initials }), el("div", {}, el("div", { class: "pick-name", text: b.workshop }), el("div", { class: "pick-note", text: `${b.order_id} \u00b7 ${b.pieces} ${b.product} for ${b.customer}` }))),
      el(
        "div",
        { class: "summary" },
        [["Arrives", `${b.eta_day} (due ${b.due_day})`], ["Spare time", b.slack], ["Cost", "$" + b.cost], ["Defect risk", b.defects]].concat(b.constraints.map((c) => ["Constraint kept", c])).map(([k, v]) => el("div", {}, el("span", { text: k }), el("b", { text: v }))),
      ),
      el("div", { class: "section-title", text: "Confirming dispatcher" }),
      nameInput,
      slide,
      el("p", { class: "fine", text: "Saves the booking to the local plan and reserves capacity. No workshop is contacted." }),
      el("div", { class: "actions" }, el("button", { class: "btn secondary", type: "button", onclick: closeSheet }, "Cancel")),
    ];
  }

  function profileSheet(data) {
    const name = el("input", { class: "text-field", type: "text", value: data.profile.name || "", placeholder: "Your name", maxlength: "60", "aria-label": "Your name" });
    const voice = el("button", { class: "switch", type: "button", role: "switch", "aria-checked": data.profile.speak ? "true" : "false", "aria-label": "Read answers aloud" });
    voice.addEventListener("click", () => voice.setAttribute("aria-checked", voice.getAttribute("aria-checked") === "true" ? "false" : "true"));
    const supported = Boolean(recognitionClass());
    return [
      el("h3", { text: "You" }),
      el("p", { class: "lead", text: "Your name is recorded on every booking you confirm. Settings are remembered on this desk." }),
      name,
      el("div", { class: "switch-row" }, el("div", { class: "grow" }, el("b", { text: "Read answers aloud" }), el("small", { text: "Spoken replies use the same Python-written text as the cards." })), voice),
      el("div", { class: "switch-row" }, el("div", { class: "grow" }, el("b", { text: "Voice input" }), el("small", { text: supported ? "Available in this browser. Hold the microphone to talk, or tap to start and stop." : "Not available in this browser. Use Chrome, Edge or Safari, or type." })), el("span", { class: "badge " + (supported ? "ok" : "late"), text: supported ? "Ready" : "Off" })),
      el("div", { class: "actions" }, el("button", { class: "btn primary", type: "button", onclick: () => { emitAndWait({ type: "profile", name: name.value.trim(), speak: voice.getAttribute("aria-checked") === "true" }); closeSheet(); } }, "Save")),
    ];
  }

  function traceSheet(data, card) {
    return [
      el("h3", { text: "How this answer was made" }),
      el("p", { class: "lead", text: "Each step, in order. Values are copied from the tools, not written by the model." }),
      el("ol", { class: "pipeline" }, card.trace.map((step) => el("li", {}, el("div", { class: "step-dot" }, icon(STAGE_ICONS[step.stage] || "spark")), el("div", {}, el("div", { class: "step-title" }, step.stage, el("span", { class: "step-actor", text: step.actor })), el("div", { class: "step-detail", text: step.detail }))))),
    ];
  }

  // Updates from Python ---------------------------------------------------------------------
  function update(data) {
    const previous = state.data;
    state.data = data;
    if (state.busy && (!previous || data.v > state.waitingFor)) setBusy(false);
    renderHeader(data);
    renderStories(data);
    renderThread(data);
    renderBehind(data);
    if (data.notice && data.notice.id !== state.notice) {
      state.notice = data.notice.id;
      if (state.initialized) toast(data.notice.text);
    }
    if (data.booking && data.booking.key !== state.bookingKey && state.sheet !== "booking") {
      state.bookingKey = data.booking.key;
      openSheet("booking");
    } else if (!data.booking && state.sheet === "booking") {
      state.sheet = null;
      nodes.scrim.hidden = true;
      nodes.sheet.hidden = true;
    } else if (state.sheet && state.sheet !== "booking") {
      renderSheet();
    }
    const last = [...data.thread].reverse().find((m) => m.role === "assistant");
    if (!state.initialized) {
      data.thread.forEach((m) => state.spoken.add(m.id));
      state.initialized = true;
    } else if (last && !state.spoken.has(last.id)) {
      state.spoken.add(last.id);
      speak(last.card && last.card.speak);
    }
  }

  return {
    update,
    alive: () => nodes.thread.isConnected && root.querySelector("#thread") === nodes.thread,
    build: BUILD,
    set trigger(fn) {
      state.trigger = fn;
    },
    destroy() {
      listeners.abort();
      try {
        state.recognition?.abort();
      } catch (error) {
        /* already stopped */
      }
      window.speechSynthesis?.cancel();
      clearTimeout(state.busyTimer);
      clearInterval(state.thinkingTimer);
    },
  };
}

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let app = parentElement.__dispatchAssistant;
  if (app && (!app.alive() || app.build !== BUILD)) {
    app.destroy();
    app = null;
  }
  if (!app) {
    app = createApp(parentElement);
    parentElement.__dispatchAssistant = app;
  }
  app.trigger = setTriggerValue;
  if (data) app.update(data);
  return () => {
    app.destroy();
    delete parentElement.__dispatchAssistant;
  };
}
