const path = require("path");
const PptxGenJS = require("C:/Users/shanu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs/dist/pptxgen.cjs.js");

const root = path.resolve(__dirname);
const assets = path.join(root, "generated_assets");
const thesisRoot = root;

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "DIT University";
pptx.subject = "Miryn AI Extended Slides";
pptx.title = "BTECH-86 Extended Miryn Deck";

const C = {
  ink: "111111",
  blue: "4F81BD",
  red: "C0504D",
  green: "9BBB59",
  gray: "666666",
  line: "D9D9D9",
  white: "FFFFFF",
  paleBlue: "EAF2FB",
  paleRed: "FDEDEC",
  paleGreen: "EAF7EA",
  paleYellow: "FFF4D6",
};

function frame(slide, section, title, source = "") {
  slide.background = { color: C.white };
  slide.addText(section, {
    x: 0.42, y: 0.18, w: 4.6, h: 0.26,
    fontFace: "Calibri", fontSize: 18, bold: true, color: C.ink, margin: 0
  });
  if (source) {
    slide.addText(source, {
      x: 9.0, y: 0.18, w: 3.8, h: 0.2,
      fontFace: "Calibri", fontSize: 9, color: C.gray, align: "right", margin: 0
    });
  }
  slide.addText(title, {
    x: 0.42, y: 0.55, w: 8.7, h: 0.36,
    fontFace: "Calibri", fontSize: 24, bold: true, color: C.ink, margin: 0
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 0.42, y: 0.98, w: 12.1, h: 0, line: { color: C.line, pt: 1.0 }
  });
  slide.addText("Group BTCSE-86", {
    x: 0.42, y: 7.1, w: 1.6, h: 0.16, fontFace: "Calibri", fontSize: 9, color: C.gray, margin: 0
  });
  slide.addText("DIT University", {
    x: 5.62, y: 7.1, w: 1.4, h: 0.16, fontFace: "Calibri", fontSize: 9, color: C.gray, align: "center", margin: 0
  });
  slide.addText("March 2026", {
    x: 11.4, y: 7.1, w: 1.0, h: 0.16, fontFace: "Calibri", fontSize: 9, color: C.gray, align: "right", margin: 0
  });
}

function bullets(slide, arr, x, y, w, h, size = 16) {
  const runs = [];
  arr.forEach((b) => runs.push({ text: b, options: { bullet: { indent: 14 } } }));
  slide.addText(runs, {
    x, y, w, h, fontFace: "Calibri", fontSize: size, color: C.ink,
    breakLine: true, paraSpaceAfterPt: 9, margin: 0.02, fit: "shrink"
  });
}

function band(slide, text, x, y, w, h, fill) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.04,
    fill: { color: fill }, line: { color: fill, pt: 0.7 }
  });
  slide.addText(text, {
    x: x + 0.08, y: y + 0.06, w: w - 0.16, h: h - 0.1,
    fontFace: "Calibri", fontSize: 14, color: C.ink, margin: 0, fit: "shrink"
  });
}

function img(name) {
  return path.join(assets, name);
}

// 1
{
  const s = pptx.addSlide();
  frame(s, "PROJECT DESCRIPTION", "IMPLEMENTED SYSTEM OVERVIEW", "Source: github.com/phnxsahil/Miryn-AI");
  bullets(s, [
    "The original proposal deck described MIRYN AI as a persistent memory and identity framework. The implemented system now includes a working compare workspace, persona drill-down pages, deterministic reporting, and streaming route repair.",
    "The final architecture is centered on four interacting layers: frontend surfaces, FastAPI orchestration, memory + identity services, and background reflection / event delivery.",
    "This extension adds the implementation evidence that was missing from the earlier deck: actual system diagrams, database view, persona comparison, prompt behavior, and final thesis artifacts."
  ], 0.55, 1.35, 6.2, 4.7);
  band(s, "Implemented frontend routes: /chat, /identity, /memory, /compare, /compare/persona/[userId]", 7.0, 1.45, 5.4, 0.68, C.paleBlue);
  band(s, "Implemented backend endpoints: auth, chat, streaming, analytics, compare, report, memory, identity", 7.0, 2.35, 5.4, 0.68, C.paleGreen);
  band(s, "Implemented thesis artifacts: 47-page PDF report, prompt screenshots, code screenshots, ER diagram, and final presentation assets", 7.0, 3.25, 5.4, 0.82, C.paleYellow);
  band(s, "Validation focus: showing that different users cause different internal identity trajectories, not just different wording in chat replies.", 7.0, 4.35, 5.4, 0.92, C.paleRed);
}

// 2
{
  const s = pptx.addSlide();
  frame(s, "PROPOSED METHODOLOGY", "UPDATED SYSTEM ARCHITECTURE", "Source: generated from implemented codebase");
  s.addImage({ path: img("architecture_diagram.png"), x: 0.65, y: 1.2, w: 8.1, h: 4.65 });
  bullets(s, [
    "Next.js frontend hosts the user-facing surfaces for chat, identity, memory, and compare.",
    "FastAPI routes act as the application boundary and pass requests into orchestrator-driven service logic.",
    "Core services manage context retrieval, identity state, prompt construction, and memory persistence.",
    "Redis and workers allow reflection and events to happen after the visible response path."
  ], 8.95, 1.35, 3.45, 4.8, 15);
}

// 3
{
  const s = pptx.addSlide();
  frame(s, "PROPOSED METHODOLOGY", "UPDATED WORKFLOW DIAGRAM", "Source: generated from implemented codebase");
  s.addImage({ path: img("workflow_diagram.png"), x: 0.85, y: 1.18, w: 6.2, h: 5.65 });
  bullets(s, [
    "User message arrives through the chat UI and is validated by the backend.",
    "Orchestrator loads identity and retrieves memory before the LLM call.",
    "Response is streamed first so the chat experience remains responsive.",
    "Only after that does Miryn continue with DS inference, event publication, and reflection updates."
  ], 7.45, 1.45, 4.7, 4.55, 16);
  band(s, "Key optimization in final build: reflection and non-critical analytics were moved off the first-token path.", 7.38, 6.1, 4.85, 0.58, C.paleYellow);
}

// 4
{
  const s = pptx.addSlide();
  frame(s, "PROPOSED METHODOLOGY", "ENTITY RELATIONSHIP DIAGRAM", "Source: backend models + schema alignment");
  s.addImage({ path: img("er_diagram.png"), x: 0.55, y: 1.18, w: 8.7, h: 5.45 });
  bullets(s, [
    "Users own conversations, messages, identity versions, and onboarding data.",
    "Messages store role, content, embeddings, importance score, and idempotency metadata.",
    "Identity versions are append-oriented and linked to evolution logs for state-change inspection."
  ], 9.45, 1.4, 3.0, 4.6, 14);
}

// 5
{
  const s = pptx.addSlide();
  frame(s, "PROJECT DESCRIPTION", "THREE-TIER MEMORY + IDENTITY ENGINE", "Source: memory_layer.py and identity_engine.py");
  s.addImage({ path: img("memory_tiers.png"), x: 0.72, y: 1.26, w: 6.55, h: 3.72 });
  bullets(s, [
    "Transient memory supports immediate continuity inside an active session.",
    "Episodic memory stores semantically retrievable history for recent recall.",
    "Core identity memory stores beliefs, open loops, patterns, emotions, and conflict traces.",
    "Identity snapshots unify these into a stable state used before every future response."
  ], 7.55, 1.42, 4.7, 3.95, 15);
  band(s, "Hybrid retrieval balances semantic similarity, temporal relevance, and importance rather than treating every old message equally.", 0.82, 5.55, 11.4, 0.7, C.paleBlue);
}

// 6
{
  const s = pptx.addSlide();
  frame(s, "PROJECT DESCRIPTION", "COMPARE WORKSPACE AND PERSONA DRILL-DOWN", "Source: implemented compare pages");
  s.addImage({ path: path.join(thesisRoot, "chat_interface.png"), x: 0.62, y: 1.23, w: 5.7, h: 2.6 });
  s.addImage({ path: path.join(thesisRoot, "identity_dashboard.png"), x: 6.62, y: 1.23, w: 5.7, h: 2.6 });
  bullets(s, [
    "The compare workspace acts as the thesis evaluation surface rather than forcing screenshots out of raw developer views.",
    "Each persona can be opened separately in identity, memory, or past-conversation mode for evidence capture.",
    "This makes the architecture inspectable and presentable to a supervisor or viva panel."
  ], 0.72, 4.25, 11.4, 2.0, 15);
}

// 7
{
  const s = pptx.addSlide();
  frame(s, "CASE STUDY", "SAD USER VS CONFIDENT WORKING USER", "Source: seeded demo personas");
  band(s, "Persona A - Vulnerable Soul", 0.7, 1.35, 5.6, 0.42, C.paleRed);
  bullets(s, [
    "Emotionally burdened, grief-heavy, lower confidence.",
    "Speaks through loneliness, atmosphere, sleep disruption, and personal meaning.",
    "Miryn should answer with slower pacing, gentler reflection, and memory of emotionally important prior context."
  ], 0.75, 1.9, 5.5, 2.75, 15);
  band(s, "Persona B - High Performer", 6.95, 1.35, 5.35, 0.42, C.paleBlue);
  bullets(s, [
    "Confident, project-focused, and execution-oriented.",
    "Speaks through launch planning, hiring, deployment, latency, and measurable progress.",
    "Miryn should answer with concise strategic continuity and stronger action orientation."
  ], 7.0, 1.9, 5.2, 2.75, 15);
  band(s, "Research value of this comparison: the same system must produce different evolving internal models, not only different surface tones.", 0.78, 5.2, 11.4, 0.8, C.paleYellow);
}

// 8
{
  const s = pptx.addSlide();
  frame(s, "CASE STUDY", "PERSONA COMPARISON METRICS", "Source: compare analytics output");
  s.addImage({ path: img("persona_metrics.png"), x: 0.62, y: 1.25, w: 7.1, h: 4.3 });
  s.addTable([
    [{ text: "Metric" }, { text: "Vulnerable" }, { text: "High Performer" }],
    [{ text: "Sadness" }, { text: "0.88" }, { text: "0.14" }],
    [{ text: "Confidence" }, { text: "0.22" }, { text: "0.91" }],
    [{ text: "Semantic Drift" }, { text: "0.71" }, { text: "0.34" }],
    [{ text: "Identity Stability" }, { text: "0.31" }, { text: "0.79" }],
    [{ text: "Goal Focus" }, { text: "0.28" }, { text: "0.93" }],
  ], {
    x: 8.25, y: 1.45, w: 3.9, h: 2.8,
    fontFace: "Calibri", fontSize: 11, color: C.ink, border: { type: "solid", color: "A6A6A6", pt: 1 },
    fill: "FFFFFF", rowH: 0.44, colW: [1.6, 0.95, 1.25], margin: 0.04, autoFit: false
  });
  bullets(s, [
    "Higher emotional salience and drift in Persona A indicate a broader and more emotionally reinterpreted identity trajectory.",
    "Higher confidence and goal focus in Persona B indicate a more convergent operational identity path."
  ], 8.2, 4.75, 4.05, 1.45, 14);
}

// 9
{
  const s = pptx.addSlide();
  frame(s, "CASE STUDY", "IDENTITY EVOLUTION AND PROMPT ADAPTATION", "Source: generated compare report artifacts");
  s.addImage({ path: img("drift_timeline.png"), x: 0.58, y: 1.18, w: 5.9, h: 3.45 });
  s.addImage({ path: img("sad_prompt.png"), x: 6.72, y: 1.2, w: 5.45, h: 2.15 });
  s.addImage({ path: img("confident_prompt.png"), x: 6.72, y: 3.55, w: 5.45, h: 2.15 });
  band(s, "Miryn changes not only its wording but also its memory priorities, pacing, and conversational objective for the two personas.", 0.72, 5.95, 11.45, 0.62, C.paleGreen);
}

// 10
{
  const s = pptx.addSlide();
  frame(s, "FINAL STATUS", "IMPLEMENTATION EVIDENCE, LIMITATIONS, AND CONCLUSION", "Source: local validated thesis build");
  s.addImage({ path: path.join(root, "images", "code_sse.png"), x: 0.62, y: 1.22, w: 3.75, h: 2.0 });
  s.addImage({ path: path.join(root, "images", "code_sql.png"), x: 4.78, y: 1.22, w: 3.75, h: 2.0 });
  s.addImage({ path: path.join(root, "images", "code_react.png"), x: 8.95, y: 1.22, w: 3.0, h: 2.0 });
  bullets(s, [
    "Miryn is now best described as a strong local thesis-demo build with real identity, memory, comparison, and report surfaces implemented end to end.",
    "The key limitation is deployment maturity: local validation is strong, but public environment wiring still remains a next step.",
    "Final conclusion: Miryn demonstrates that an identity-first conversational architecture can move beyond stateless chat and show different user trajectories in a structured, inspectable form."
  ], 0.7, 3.65, 11.4, 2.2, 15);
}

const out = path.join(root, "BTECH-86_24th_extended_newslides.pptx");
pptx.writeFile({ fileName: out }).then(() => console.log(out)).catch((err) => {
  console.error(err);
  process.exit(1);
});
