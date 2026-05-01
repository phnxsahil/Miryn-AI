const path = require("path");
const PptxGenJS = require("C:/Users/shanu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs/dist/pptxgen.cjs.js");

const root = path.resolve(__dirname);
const assets = path.join(root, "generated_assets");
const images = path.join(root, "images");

const pptx = new PptxGenJS();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "OpenAI Codex";
pptx.company = "Miryn AI";
pptx.subject = "Final BTech Presentation";
pptx.title = "Miryn AI Final BTech Presentation";
pptx.lang = "en-US";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "en-US",
};

const C = {
  bg: "F7F8FC",
  ink: "0F172A",
  muted: "475569",
  blue: "2563EB",
  blueSoft: "DBEAFE",
  amber: "F59E0B",
  amberSoft: "FEF3C7",
  red: "DC2626",
  redSoft: "FEE2E2",
  greenSoft: "DCFCE7",
  violetSoft: "E9D5FF",
  line: "CBD5E1",
  white: "FFFFFF",
  dark: "0B1220",
};

function addSlideBase(slide, title, kicker) {
  slide.background = { color: C.bg };
  if (kicker) {
    slide.addText(kicker, {
      x: 0.55, y: 0.28, w: 4.2, h: 0.22,
      fontFace: "Aptos", fontSize: 10, color: C.blue, bold: true,
      charSpace: 1.2,
    });
  }
  slide.addText(title, {
    x: 0.55, y: 0.5, w: 8.6, h: 0.5,
    fontFace: "Aptos Display", fontSize: 24, bold: true, color: C.ink,
    margin: 0,
  });
  slide.addShape(pptx.ShapeType.line, {
    x: 0.55, y: 1.07, w: 12.15, h: 0,
    line: { color: C.line, pt: 1.2 }
  });
}

function addBullets(slide, bullets, x, y, w, h, opts = {}) {
  const runs = [];
  bullets.forEach((b) => {
    runs.push({
      text: b,
      options: { bullet: { indent: 14 }, hanging: 3 }
    });
  });
  slide.addText(runs, {
    x, y, w, h,
    fontFace: "Aptos",
    fontSize: opts.fontSize || 17,
    color: C.ink,
    breakLine: true,
    paraSpaceAfterPt: opts.spaceAfter || 10,
    valign: "top",
    margin: 0.02,
    fit: "shrink",
  });
}

function addInfoBand(slide, text, x, y, w, h, fill, color = C.ink) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.08,
    fill: { color: fill },
    line: { color: fill, pt: 0.5 }
  });
  slide.addText(text, {
    x: x + 0.12, y: y + 0.08, w: w - 0.24, h: h - 0.12,
    fontFace: "Aptos", fontSize: 15, color, margin: 0, fit: "shrink"
  });
}

function addLabel(slide, text, x, y, w, color = C.muted) {
  slide.addText(text, {
    x, y, w, h: 0.2,
    fontFace: "Aptos", fontSize: 10, bold: true, color,
    charSpace: 1.1, margin: 0,
  });
}

function img(name) {
  return path.join(assets, name);
}

function thesisImg(name) {
  return path.join(root, name);
}

// Slide 1: Cover
{
  const slide = pptx.addSlide();
  slide.background = { color: C.dark };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.dark }, line: { color: C.dark, pt: 0 } });
  slide.addText("MIRYN AI", {
    x: 0.7, y: 0.8, w: 4.8, h: 0.6,
    fontFace: "Aptos Display", fontSize: 28, bold: true, color: C.white, margin: 0
  });
  slide.addText("Identity-First Conversational Architecture with Persistent Memory, Reflection, and Persona Comparison", {
    x: 0.7, y: 1.45, w: 5.8, h: 1.1,
    fontFace: "Aptos", fontSize: 18, color: "D6E2FF", margin: 0, fit: "shrink"
  });
  slide.addText("Final B.Tech Presentation", {
    x: 0.7, y: 2.9, w: 3.2, h: 0.26,
    fontFace: "Aptos", fontSize: 12, bold: true, color: "93C5FD", margin: 0
  });
  slide.addText("Architecture, ER design, workflow, implementation, and sad-vs-confident user evaluation", {
    x: 0.7, y: 3.2, w: 4.7, h: 0.46,
    fontFace: "Aptos", fontSize: 14, color: "CBD5E1", margin: 0
  });
  slide.addImage({ path: img("architecture_diagram.png"), x: 6.35, y: 0.55, w: 6.2, h: 3.55 });
  addInfoBand(slide, "Core idea: Miryn should not behave like a stateless chatbot. It should remember, reflect, adapt, and expose identity evolution over time.", 0.72, 4.5, 11.95, 0.95, "13203A", "E2E8F0");
  addInfoBand(slide, "This presentation summarizes the final implemented system, including compare workspace, persona drill-down views, report generation, and performance cleanup.", 0.72, 5.62, 11.95, 0.8, "111827", "CBD5E1");
}

// Slide 2: Problem and motivation
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Problem Statement and Motivation", "WHY MIRYN");
  addBullets(slide, [
    "Most conversational AI systems are fluent but stateless. They answer the current turn well but do not preserve a meaningful model of the user's longer trajectory.",
    "This causes contextual amnesia: users must restate history, emotional patterns are forgotten, and recurring concerns are treated as isolated fresh events.",
    "For companion-style AI, this is not a small UX flaw. It breaks trust, continuity, and the sense of being known over time.",
    "Miryn was built to make identity, memory, and reflection first-class runtime components rather than side notes around a chat box."
  ], 0.75, 1.35, 6.2, 4.9);
  addInfoBand(slide, "Target outcome: an AI system that can remember what matters, update who the user seems to be, and visibly show that evolution through dashboards and comparison views.", 7.1, 1.45, 5.5, 0.95, C.blueSoft);
  addInfoBand(slide, "Research framing: Miryn is not just retrieval-augmented generation. It is an identity-first architecture with persistent state, reflective analytics, and longitudinal differentiation.", 7.1, 2.62, 5.5, 1.15, C.violetSoft);
  addInfoBand(slide, "Final thesis demonstration: compare a sad / vulnerable user and a confident / working user to show that the same system builds different identity trajectories.", 7.1, 4.02, 5.5, 1.1, C.amberSoft);
}

// Slide 3: Objectives
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Project Objectives and Key Contributions", "WHAT WAS BUILT");
  addBullets(slide, [
    "Persistent memory storage across sessions using transient, episodic, and core identity-aware layers.",
    "Versioned identity engine capturing traits, values, beliefs, open loops, emotional traces, and conflicts.",
    "FastAPI backend with dedicated chat, analytics, identity, memory, and compare/report endpoints.",
    "Frontend surfaces for chat, identity, memory, and a thesis-oriented compare workspace.",
    "Deterministic comparative report generation for seeded personas to support evaluation and screenshots.",
    "Performance cleanup so reflection and non-critical analytics do not block first-response chat latency."
  ], 0.75, 1.35, 6.3, 5.2);
  slide.addTable([
    [{ text: "Contribution" }, { text: "Implemented outcome" }],
    [{ text: "Comparison workspace" }, { text: "Side-by-side persona overview, charts, narrative report, and drill-down links" }],
    [{ text: "Persona drill-down" }, { text: "Read-only identity, memory, and past-conversation pages for each demo account" }],
    [{ text: "Streaming repair" }, { text: "Chat stream and event stream routes restored to match frontend expectations" }],
    [{ text: "Thesis artifact layer" }, { text: "Long PDF report, prompt screenshots, code screenshots, and presentation assets" }],
  ], {
    x: 7.05, y: 1.45, w: 5.65, h: 4.95,
    border: { type: "solid", color: C.line, pt: 1 },
    fill: C.white,
    color: C.ink,
    fontFace: "Aptos",
    fontSize: 11,
    rowH: 0.68,
    colW: [1.8, 3.7],
    margin: 0.06,
    bold: false,
    autoFit: false
  });
}

// Slide 4: Architecture
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "High-Level System Architecture", "END-TO-END STACK");
  slide.addImage({ path: img("architecture_diagram.png"), x: 0.7, y: 1.35, w: 7.0, h: 4.05 });
  addBullets(slide, [
    "Frontend: Next.js App Router with chat, identity, memory, compare, and persona detail surfaces.",
    "Backend: FastAPI orchestrates authentication, context retrieval, LLM calls, and persistence.",
    "Core services: orchestrator, memory layer, identity engine, reflection engine, and LLM service.",
    "Data layer: PostgreSQL or local SQLite compatibility with identity evolution logging.",
    "Workers and eventing: Redis-backed queues and event streams for deferred reflection and updates."
  ], 7.95, 1.45, 4.7, 4.2);
  addInfoBand(slide, "Architectural thesis: the same user message path can stay fast while deeper reflective work happens in the background.", 0.72, 5.75, 11.9, 0.7, C.greenSoft);
}

// Slide 5: Workflow
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "User Message Processing Workflow", "RUNTIME PATH");
  slide.addImage({ path: img("workflow_diagram.png"), x: 0.78, y: 1.35, w: 6.0, h: 5.55 });
  addBullets(slide, [
    "1. User submits a message through chat UI.",
    "2. Chat API validates session and conversation ownership.",
    "3. Orchestrator loads identity and fetches relevant memory context.",
    "4. LLM service builds a dynamic prompt using identity state plus context.",
    "5. Assistant response is streamed to the frontend.",
    "6. DS inference and reflection continue after the visible reply path."
  ], 7.15, 1.5, 5.0, 4.85);
  addInfoBand(slide, "Performance decision: reflection, conflict detection, and secondary panels were moved off the critical path so the first useful token arrives earlier.", 7.1, 6.0, 5.1, 0.8, C.redSoft);
}

// Slide 6: ER
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Entity Relationship Diagram", "DATABASE DESIGN");
  slide.addImage({ path: img("er_diagram.png"), x: 0.62, y: 1.25, w: 8.3, h: 5.15 });
  addBullets(slide, [
    "A single user owns conversations, messages, identity versions, and onboarding responses.",
    "Messages are tied both to conversation history and user-level retrieval through embeddings and importance scores.",
    "Identity versions are append-oriented rather than destructive updates, which allows temporal analysis.",
    "Identity evolution is stored as a log so field-level change can be inspected later."
  ], 9.1, 1.55, 3.75, 4.6);
}

// Slide 7: Memory and identity
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Three-Tier Memory and Identity Engine", "STATE MODEL");
  slide.addImage({ path: img("memory_tiers.png"), x: 0.78, y: 1.35, w: 6.0, h: 3.4 });
  addBullets(slide, [
    "Transient memory keeps immediate conversation accessible with very low friction.",
    "Episodic memory stores semantically retrievable message history for short- to medium-term recall.",
    "Core memory stores the user's more stable semantic anchors: beliefs, open loops, patterns, and emotionally important themes.",
    "Identity snapshots unify these into a versioned user model that can be reused before every future response."
  ], 7.05, 1.5, 5.25, 4.35);
  addInfoBand(slide, "Hybrid retrieval = semantic similarity + temporal relevance + importance weighting. The goal is not to recall everything, but to recall what matters now.", 0.78, 5.25, 11.5, 0.8, C.blueSoft);
}

// Slide 8: Core modules
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Core Implementation Modules", "BACKEND + FRONTEND");
  slide.addTable([
    [{ text: "Module" }, { text: "Location" }, { text: "Role in the system" }],
    [{ text: "Conversation Orchestrator" }, { text: "services/orchestrator.py" }, { text: "Coordinates identity load, memory retrieval, LLM response, storage, and reflection queueing." }],
    [{ text: "LLM Service" }, { text: "services/llm_service.py" }, { text: "Builds system prompts from identity and context, supports chat and streaming." }],
    [{ text: "Memory Layer" }, { text: "services/memory_layer.py" }, { text: "Stores and retrieves transient, semantic, and important memories." }],
    [{ text: "Identity Engine" }, { text: "services/identity_engine.py" }, { text: "Maintains versioned identity snapshots and related substructures." }],
    [{ text: "Compare Workspace" }, { text: "components/Compare/*" }, { text: "Shows charts, differences, report narrative, and links into persona-specific views." }],
  ], {
    x: 0.62, y: 1.45, w: 12.05, h: 3.55,
    border: { type: "solid", color: C.line, pt: 1 },
    fill: C.white,
    color: C.ink,
    fontFace: "Aptos",
    fontSize: 11,
    rowH: 0.62,
    colW: [2.0, 2.8, 7.0],
    margin: 0.05,
    autoFit: false
  });
  addLabel(slide, "Key observation", 0.67, 5.35, 1.4, C.blue);
  slide.addText("The compare/demo implementation is not a detached side project. It is built directly on the same identity, memory, chat, and analytics foundations as the main application.", {
    x: 0.67, y: 5.62, w: 8.8, h: 0.55, fontFace: "Aptos", fontSize: 16, color: C.ink, margin: 0
  });
  addInfoBand(slide, "This is important for the viva: the thesis evidence surface is part of the real product stack, not an isolated mockup.", 9.65, 5.35, 2.95, 0.9, C.amberSoft);
}

// Slide 9: Frontend
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Frontend Surfaces and Compare Workspace", "USER EXPERIENCE");
  slide.addImage({ path: thesisImg("chat_interface.png"), x: 0.7, y: 1.35, w: 5.85, h: 2.75 });
  slide.addImage({ path: thesisImg("identity_dashboard.png"), x: 6.8, y: 1.35, w: 5.85, h: 2.75 });
  addBullets(slide, [
    "Chat view: main interaction surface with streaming responses and deferred insights.",
    "Identity view: inspectable state including traits, values, beliefs, loops, and emotional patterns.",
    "Memory view: stored message clusters across different retrieval categories.",
    "Compare workspace: thesis-facing route for side-by-side persona evaluation and screenshot capture.",
    "Persona detail pages: read-only identity, memory, and history views for each seeded user."
  ], 0.82, 4.45, 11.7, 2.2);
}

// Slide 10: Persona design
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Evaluation Personas: Sad User vs Confident Working User", "CASE STUDY DESIGN");
  addInfoBand(slide, "Persona A - Vulnerable Soul", 0.75, 1.45, 5.85, 0.45, C.redSoft, C.red);
  addBullets(slide, [
    "Emotionally burdened, grief-heavy, lower confidence.",
    "Talks through atmosphere, loneliness, sleep disruption, and meaning.",
    "Needs validation, gentler pacing, and memory of emotionally important prior disclosures.",
    "Tests whether Miryn can preserve continuity of care rather than generic empathy."
  ], 0.78, 2.0, 5.7, 3.25);
  addInfoBand(slide, "Persona B - High Performer", 6.78, 1.45, 5.8, 0.45, C.blueSoft, C.blue);
  addBullets(slide, [
    "Confident, action-oriented, and project-focused.",
    "Talks through sprints, launch pressure, hiring, deployment, and execution risk.",
    "Needs strategic continuity, prioritization support, and retrieval of project-relevant history.",
    "Tests whether Miryn can preserve momentum and operational context rather than only emotional tone."
  ], 6.8, 2.0, 5.65, 3.25);
  addInfoBand(slide, "Why this pair matters: the same architecture should produce different identity evolution for different user styles. Otherwise the system is only storing transcripts, not modeling users.", 0.78, 5.65, 11.75, 0.85, C.greenSoft);
}

// Slide 11: Metrics
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Persona Comparison Metrics", "ANALYTICS OUTPUT");
  slide.addImage({ path: img("persona_metrics.png"), x: 0.75, y: 1.35, w: 7.15, h: 4.45 });
  slide.addTable([
    [{ text: "Metric" }, { text: "Sad persona" }, { text: "Confident persona" }],
    [{ text: "Sadness" }, { text: "0.88" }, { text: "0.14" }],
    [{ text: "Confidence" }, { text: "0.22" }, { text: "0.91" }],
    [{ text: "Semantic drift" }, { text: "0.71" }, { text: "0.34" }],
    [{ text: "Identity stability" }, { text: "0.31" }, { text: "0.79" }],
    [{ text: "Goal focus" }, { text: "0.28" }, { text: "0.93" }],
  ], {
    x: 8.25, y: 1.6, w: 4.15, h: 2.85,
    border: { type: "solid", color: C.line, pt: 1 },
    fill: C.white,
    color: C.ink,
    fontFace: "Aptos", fontSize: 11,
    rowH: 0.45,
    colW: [1.9, 1.0, 1.25],
    margin: 0.04,
    autoFit: false
  });
  addBullets(slide, [
    "Higher sadness and broader drift in Persona A indicate a more emotionally expansive evolving model.",
    "Higher confidence and stronger goal focus in Persona B indicate a narrower but more execution-stable model.",
    "This is the key proof that Miryn's internal state diverges in meaningful ways across users."
  ], 8.2, 4.75, 4.2, 1.7, { fontSize: 15 });
}

// Slide 12: Drift timeline and compare table
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Identity Evolution Over Time", "DRIFT + INTERPRETATION");
  slide.addImage({ path: img("drift_timeline.png"), x: 0.72, y: 1.35, w: 7.0, h: 4.15 });
  slide.addTable([
    [{ text: "Dimension" }, { text: "Persona A" }, { text: "Persona B" }],
    [{ text: "Dominant memory" }, { text: "Emotion-rich and grief-linked" }, { text: "Goal-linked and technical" }],
    [{ text: "Pattern style" }, { text: "Meaning seeking and metaphor heavy" }, { text: "Problem decomposition and observability" }],
    [{ text: "Open loops" }, { text: "Loneliness, sleep, personal meaning" }, { text: "Launch, latency, deployment, benchmarks" }],
    [{ text: "Miryn tone shift" }, { text: "Validating, slower, reflective" }, { text: "Strategic, concise, energetic" }],
  ], {
    x: 8.05, y: 1.55, w: 4.45, h: 3.25,
    border: { type: "solid", color: C.line, pt: 1 },
    fill: C.white, color: C.ink, fontFace: "Aptos", fontSize: 10.5,
    rowH: 0.52, colW: [1.55, 1.4, 1.5], margin: 0.04, autoFit: false
  });
  addInfoBand(slide, "Interpretation: Persona A forces Miryn to widen its model through recurring emotional reinterpretation, while Persona B converges around strategic continuity and measurable execution.", 8.0, 5.15, 4.5, 1.0, C.violetSoft);
}

// Slide 13: Prompt behavior and conversation evidence
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Prompt Adaptation and Conversation Evidence", "HOW MIRYN CHANGES ITS VOICE");
  slide.addImage({ path: img("sad_prompt.png"), x: 0.68, y: 1.3, w: 6.0, h: 2.35 });
  slide.addImage({ path: img("confident_prompt.png"), x: 6.9, y: 1.3, w: 5.75, h: 2.35 });
  slide.addImage({ path: img("sad_chat.png"), x: 0.68, y: 3.95, w: 6.0, h: 2.6 });
  slide.addImage({ path: img("confident_chat.png"), x: 6.9, y: 3.95, w: 5.75, h: 2.6 });
}

// Slide 14: Code evidence
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Implementation Evidence: Code Snippets", "WHAT EXISTS IN THE REPO");
  slide.addImage({ path: path.join(images, "code_sse.png"), x: 0.7, y: 1.35, w: 4.05, h: 2.15 });
  slide.addImage({ path: path.join(images, "code_sql.png"), x: 4.88, y: 1.35, w: 4.05, h: 2.15 });
  slide.addImage({ path: path.join(images, "code_react.png"), x: 9.05, y: 1.35, w: 3.55, h: 2.15 });
  addBullets(slide, [
    "Streaming route evidence: shows the live event delivery path expected by the frontend.",
    "Schema / vector evidence: shows message storage, embeddings, and retrieval-oriented database design.",
    "Frontend evidence: shows the compare/report UI styling logic used for visual analytics components.",
    "Together these snippets demonstrate that architecture, storage, and UI were all implemented rather than only described."
  ], 0.82, 3.95, 11.7, 2.05);
}

// Slide 15: Results and status
{
  const slide = pptx.addSlide();
  addSlideBase(slide, "Implemented Results, Limitations, and Future Scope", "FINAL STATUS");
  slide.addTable([
    [{ text: "Area" }, { text: "Current status" }, { text: "Next step" }],
    [{ text: "Compare demo" }, { text: "Implemented with seeded personas, charts, and report generation" }, { text: "Deploy publicly for external review" }],
    [{ text: "Persona drill-down" }, { text: "Implemented for identity, memory, and conversation history" }, { text: "Add richer filters and export options" }],
    [{ text: "Chat performance" }, { text: "Critical path trimmed and streaming repaired" }, { text: "Further production latency testing" }],
    [{ text: "Deployment" }, { text: "Local thesis/demo build validated" }, { text: "Railway + frontend hosting handoff" }],
    [{ text: "Research depth" }, { text: "Strong prototype and thesis evidence surfaces" }, { text: "Real user study and correction loops" }],
  ], {
    x: 0.68, y: 1.45, w: 12.0, h: 3.45,
    border: { type: "solid", color: C.line, pt: 1 },
    fill: C.white, color: C.ink, fontFace: "Aptos", fontSize: 10.5,
    rowH: 0.55, colW: [1.4, 5.0, 4.8], margin: 0.04, autoFit: false
  });
  addBullets(slide, [
    "The system is strongest as an identity-aware research prototype with unusually inspectable internal state.",
    "Its clearest proof point is that two different personas produce two different trajectories, not merely different word choices.",
    "The next major milestone is deployment and evaluation with real longitudinal users."
  ], 0.82, 5.2, 11.5, 1.25, { fontSize: 15 });
}

// Slide 16: Closing
{
  const slide = pptx.addSlide();
  slide.background = { color: C.dark };
  slide.addText("Thank You", {
    x: 0.75, y: 1.1, w: 3.4, h: 0.6,
    fontFace: "Aptos Display", fontSize: 28, bold: true, color: C.white, margin: 0
  });
  slide.addText("Miryn AI demonstrates how memory, identity, and reflection can be integrated into a companion-style conversational system in a way that is inspectable, comparable, and technically grounded.", {
    x: 0.75, y: 1.95, w: 6.0, h: 1.05,
    fontFace: "Aptos", fontSize: 18, color: "D7E4FF", margin: 0, fit: "shrink"
  });
  slide.addImage({ path: img("persona_metrics.png"), x: 7.15, y: 1.0, w: 5.55, h: 3.35 });
  addInfoBand(slide, "Suggested viva line: Miryn is not just a chatbot with memory. It is an identity-first system that changes its future behavior by storing and interpreting what the user becomes over time.", 0.75, 4.65, 11.95, 0.95, "111827", "E5E7EB");
  addInfoBand(slide, "Presentation prepared from the implemented project, final report artifacts, and generated thesis visuals.", 0.75, 5.85, 11.95, 0.62, "13203A", "AFC5E8");
}

const out = path.join(root, "Miryn_Final_BTech_Presentation.pptx");
pptx.writeFile({ fileName: out }).then(() => {
  console.log(out);
}).catch((err) => {
  console.error(err);
  process.exit(1);
});
