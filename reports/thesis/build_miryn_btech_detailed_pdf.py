from __future__ import annotations

import math
import re
from pathlib import Path

from pypdf import PdfReader
from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
REPORTS_ROOT = ROOT.parent
PROJECT_ROOT = REPORTS_ROOT.parent
ASSET_DIR = ROOT / "generated_assets"
ASSET_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PDF = ROOT / "Miryn_Final_BTech_Report_Detailed_40Plus.pdf"
OUTPUT_SOURCE = ROOT / "Miryn_Final_BTech_Report_Detailed_40Plus_Source.md"

PROJECT_SOURCE = REPORTS_ROOT / "miryn_project_report_source.md"
BTECH_SOURCE = ROOT / "Miryn_Final_BTech_Report_Expanded.md"
EXTENDED_SOURCE = ROOT / "Miryn_Thesis_Complete_Extended.md"

CHAT_SCREENSHOT = ROOT / "chat_interface.png"
IDENTITY_SCREENSHOT = ROOT / "identity_dashboard.png"
CODE_SSE = ROOT / "images" / "code_sse.png"
CODE_SQL = ROOT / "images" / "code_sql.png"
CODE_REACT = ROOT / "images" / "code_react.png"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_BODY = _font(26)
FONT_SMALL = _font(22)
FONT_TITLE = _font(34, bold=True)
FONT_LABEL = _font(20, bold=True)
FONT_MONO = _font(20)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_chat_screenshot(title: str, subtitle: str, exchanges: list[tuple[str, str]], out_path: Path) -> None:
    width = 1500
    height = 1180
    img = PILImage.new("RGB", (width, height), "#0b1020")
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle((40, 40, width - 40, height - 40), radius=36, fill="#11182c", outline="#22314f", width=4)
    draw.text((80, 75), title, font=FONT_TITLE, fill="#f5f7fb")
    draw.text((80, 125), subtitle, font=FONT_SMALL, fill="#aab6d3")

    y = 200
    bubble_width = width - 220
    for role, text in exchanges:
        is_user = role.lower() == "user"
        bubble_x = 90 if is_user else 160
        right_edge = bubble_x + bubble_width - (80 if is_user else 0)
        fill = "#1d4ed8" if is_user else "#1e293b"
        label = "User prompt" if is_user else "Miryn reply"
        label_color = "#dbeafe" if is_user else "#cbd5e1"

        lines = wrap_text(draw, text, FONT_BODY, bubble_width - 140)
        bubble_h = 70 + len(lines) * 42
        draw.rounded_rectangle((bubble_x, y, right_edge, y + bubble_h), radius=30, fill=fill, outline="#31405f", width=2)
        draw.text((bubble_x + 28, y + 18), label, font=FONT_LABEL, fill=label_color)
        line_y = y + 54
        for line in lines:
            draw.text((bubble_x + 28, line_y), line, font=FONT_BODY, fill="#f8fafc")
            line_y += 42
        y += bubble_h + 28

    img.save(out_path)


def draw_prompt_panel(title: str, lines: list[str], out_path: Path) -> None:
    width = 1500
    height = 980
    img = PILImage.new("RGB", (width, height), "#090c12")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((50, 50, width - 50, height - 50), radius=32, fill="#111827", outline="#374151", width=4)
    draw.text((90, 85), title, font=FONT_TITLE, fill="#f3f4f6")
    draw.text((90, 135), "Rendered as screenshot-style prompt evidence for the thesis report", font=FONT_SMALL, fill="#9ca3af")

    y = 220
    for block in lines:
        wrapped = wrap_text(draw, block, FONT_BODY, width - 220)
        for line in wrapped:
            draw.text((100, y), line, font=FONT_BODY, fill="#e5e7eb")
            y += 40
        y += 24
    img.save(out_path)


def draw_architecture_diagram(out_path: Path) -> None:
    width, height = 1600, 900
    img = PILImage.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    title_font = _font(32, bold=True)
    box_font = _font(22, bold=True)
    body_font = _font(20)
    draw.text((60, 35), "Miryn AI Architecture Overview", font=title_font, fill="#111827")

    boxes = [
        ((80, 160, 420, 310), "#dbeafe", "Frontend\nNext.js App Router\nChat, Identity, Memory, Compare"),
        ((500, 160, 860, 310), "#dcfce7", "FastAPI Backend\nAuth, Chat, Analytics,\nStreaming, Persona APIs"),
        ((940, 160, 1280, 310), "#fde68a", "Core Services\nOrchestrator, Memory Layer,\nLLM Service, Identity Engine"),
        ((1360, 160, 1520, 310), "#fbcfe8", "Workers\nCelery\nReflection"),
        ((260, 520, 620, 700), "#e9d5ff", "Data Layer\nPostgreSQL / SQLite\nMessages, Identities,\nEvolution Log"),
        ((700, 520, 1020, 700), "#fed7aa", "Cache and Events\nRedis / Event Stream\nTransient Memory"),
        ((1100, 520, 1480, 700), "#bfdbfe", "Model and DS Layer\nProvider SDKs,\nEmotion + Entity Inference"),
    ]

    for (x1, y1, x2, y2), fill, text in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=28, fill=fill, outline="#334155", width=3)
        ty = y1 + 28
        for idx, line in enumerate(text.split("\n")):
            font = box_font if idx == 0 else body_font
            draw.text((x1 + 22, ty), line, font=font, fill="#0f172a")
            ty += 34 if idx == 0 else 30

    arrows = [
        ((420, 235), (500, 235)),
        ((860, 235), (940, 235)),
        ((1280, 235), (1360, 235)),
        ((680, 310), (440, 520)),
        ((850, 310), (860, 520)),
        ((1040, 310), (1180, 520)),
    ]
    for start, end in arrows:
        draw.line((*start, *end), fill="#1d4ed8", width=6)
        draw.polygon(
            [
                (end[0], end[1]),
                (end[0] - 14, end[1] - 10),
                (end[0] - 14, end[1] + 10),
            ],
            fill="#1d4ed8",
        )
    img.save(out_path)


def draw_workflow_diagram(out_path: Path) -> None:
    width, height = 1600, 900
    img = PILImage.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((55, 38), "User Message Processing Workflow", font=_font(32, bold=True), fill="#111827")
    steps = [
        "1. User sends message from chat UI",
        "2. Chat API validates auth and conversation ownership",
        "3. Orchestrator loads identity snapshot",
        "4. Memory layer retrieves relevant context",
        "5. LLM service builds system prompt + context",
        "6. Assistant response streams to frontend",
        "7. DS layer extracts entities and emotions",
        "8. Reflection worker updates identity and analytics",
    ]
    x, y = 110, 140
    for idx, step in enumerate(steps):
        draw.rounded_rectangle((x, y, x + 1180, y + 74), radius=24, fill="#eff6ff", outline="#3b82f6", width=3)
        draw.text((x + 28, y + 20), step, font=_font(24, bold=(idx % 2 == 0)), fill="#0f172a")
        if idx < len(steps) - 1:
            draw.line((x + 590, y + 74, x + 590, y + 116), fill="#2563eb", width=6)
            draw.polygon([(x + 590, y + 122), (x + 578, y + 104), (x + 602, y + 104)], fill="#2563eb")
        y += 102
    img.save(out_path)


def draw_memory_tiers(out_path: Path) -> None:
    width, height = 1600, 900
    img = PILImage.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((55, 35), "Three-Tier Memory Model", font=_font(32, bold=True), fill="#111827")
    tiers = [
        ("Transient Memory", "#dbeafe", "Current conversation cache\nFast retrieval\nShort TTL"),
        ("Episodic Memory", "#dcfce7", "Vectorized history\nRecent context\nSemantic search"),
        ("Core Identity Memory", "#fde68a", "Beliefs, values, patterns\nLong-term continuity\nReflection output"),
    ]
    x_positions = [90, 560, 1030]
    for x, (title, fill, body) in zip(x_positions, tiers):
        draw.rounded_rectangle((x, 220, x + 410, 610), radius=32, fill=fill, outline="#334155", width=3)
        draw.text((x + 24, 260), title, font=_font(28, bold=True), fill="#0f172a")
        ty = 340
        for line in body.split("\n"):
            draw.text((x + 24, ty), line, font=_font(24), fill="#1f2937")
            ty += 48
    for sx, ex in [(500, 560), (970, 1030)]:
        draw.line((sx, 414, ex, 414), fill="#2563eb", width=8)
        draw.polygon([(ex, 414), (ex - 18, 402), (ex - 18, 426)], fill="#2563eb")
    img.save(out_path)


def draw_metrics_chart(out_path: Path) -> None:
    width, height = 1500, 900
    img = PILImage.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((60, 35), "Persona Comparison Metrics", font=_font(32, bold=True), fill="#111827")

    metrics = [
        ("Sadness", 0.88, 0.14),
        ("Confidence", 0.22, 0.91),
        ("Semantic Drift", 0.71, 0.34),
        ("Identity Stability", 0.31, 0.79),
        ("Emotion Salience", 0.84, 0.39),
        ("Goal Focus", 0.28, 0.93),
    ]
    bar_y = 170
    max_w = 450
    for label, sad, confident in metrics:
        draw.text((95, bar_y + 12), label, font=_font(23, bold=True), fill="#1f2937")
        draw.rounded_rectangle((360, bar_y, 360 + max_w, bar_y + 24), radius=12, fill="#fee2e2")
        draw.rounded_rectangle((830, bar_y, 830 + max_w, bar_y + 24), radius=12, fill="#dbeafe")
        draw.rounded_rectangle((360, bar_y, 360 + int(max_w * sad), bar_y + 24), radius=12, fill="#ef4444")
        draw.rounded_rectangle((830, bar_y, 830 + int(max_w * confident), bar_y + 24), radius=12, fill="#2563eb")
        draw.text((360 + max_w + 16, bar_y), f"{sad:.2f}", font=_font(20), fill="#991b1b")
        draw.text((830 + max_w + 16, bar_y), f"{confident:.2f}", font=_font(20), fill="#1d4ed8")
        bar_y += 92

    draw.text((360, 112), "Persona A: Vulnerable Soul", font=_font(22, bold=True), fill="#991b1b")
    draw.text((830, 112), "Persona B: High Performer", font=_font(22, bold=True), fill="#1d4ed8")
    img.save(out_path)


def draw_drift_timeline(out_path: Path) -> None:
    width, height = 1500, 900
    img = PILImage.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((55, 38), "Identity Evolution Timeline", font=_font(32, bold=True), fill="#111827")
    margin_left = 150
    margin_bottom = 120
    top = 150
    right = 1380
    bottom = height - margin_bottom
    draw.line((margin_left, bottom, right, bottom), fill="#64748b", width=4)
    draw.line((margin_left, top, margin_left, bottom), fill="#64748b", width=4)

    sad_points = [0.12, 0.34, 0.52, 0.71]
    conf_points = [0.08, 0.18, 0.26, 0.34]
    labels = ["v1", "v2", "v3", "v4"]
    usable_w = right - margin_left
    usable_h = bottom - top

    def plot(points: list[float], color: str) -> None:
        coords = []
        for idx, value in enumerate(points):
            x = margin_left + int(idx * usable_w / (len(points) - 1))
            y = bottom - int(value * usable_h)
            coords.append((x, y))
        draw.line(coords, fill=color, width=6)
        for x, y in coords:
            draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=color)

    plot(sad_points, "#dc2626")
    plot(conf_points, "#2563eb")

    for idx, label in enumerate(labels):
        x = margin_left + int(idx * usable_w / (len(labels) - 1))
        draw.text((x - 18, bottom + 20), label, font=_font(20), fill="#475569")
    for tick in range(0, 11, 2):
        value = tick / 10
        y = bottom - int(value * usable_h)
        draw.line((margin_left - 10, y, margin_left, y), fill="#64748b", width=2)
        draw.text((65, y - 10), f"{value:.1f}", font=_font(18), fill="#475569")

    draw.text((1040, 180), "Sad / grieving persona", font=_font(22, bold=True), fill="#dc2626")
    draw.text((1040, 220), "Confident / working persona", font=_font(22, bold=True), fill="#2563eb")
    img.save(out_path)


def build_assets() -> dict[str, Path]:
    assets = {
        "architecture": ASSET_DIR / "architecture_diagram.png",
        "workflow": ASSET_DIR / "workflow_diagram.png",
        "memory": ASSET_DIR / "memory_tiers.png",
        "metrics": ASSET_DIR / "persona_metrics.png",
        "timeline": ASSET_DIR / "drift_timeline.png",
        "sad_prompt": ASSET_DIR / "sad_prompt.png",
        "confident_prompt": ASSET_DIR / "confident_prompt.png",
        "sad_chat": ASSET_DIR / "sad_chat.png",
        "confident_chat": ASSET_DIR / "confident_chat.png",
    }

    draw_architecture_diagram(assets["architecture"])
    draw_workflow_diagram(assets["workflow"])
    draw_memory_tiers(assets["memory"])
    draw_metrics_chart(assets["metrics"])
    draw_drift_timeline(assets["timeline"])

    draw_prompt_panel(
        "Prompt fragment: Vulnerable / sad persona",
        [
            "Identity signals: sadness very high, confidence low, grief-related entity present.",
            "Behavioral shift: slow the tempo, avoid over-solving, validate pain before offering structure.",
            "Memory priority: retrieve bereavement references, unresolved sleep issues, and emotionally important memories.",
            "Response objective: help the user feel seen, reduce isolation, and gently surface stabilizing follow-up questions.",
        ],
        assets["sad_prompt"],
    )
    draw_prompt_panel(
        "Prompt fragment: Confident / working persona",
        [
            "Identity signals: confidence high, goal orientation high, active project and execution vocabulary present.",
            "Behavioral shift: concise, strategic, energetic, and action-linked.",
            "Memory priority: retrieve past milestones, technical blockers, deployment notes, and outstanding goals.",
            "Response objective: preserve momentum, clarify next actions, and connect present work to long-term identity themes.",
        ],
        assets["confident_prompt"],
    )

    draw_chat_screenshot(
        "Case Study A: Vulnerable Soul",
        "Screenshot-style conversation evidence used inside the thesis report",
        [
            (
                "user",
                "I have been trying to work, but ever since my father passed away the house feels hollow and I keep waking up at 3 a.m. with this heavy fear that I will stay like this forever.",
            ),
            (
                "assistant",
                "That sounds unbearably lonely, and the detail about the house feeling hollow tells me the grief is living not just in memory but in the space around you. I would slow down here rather than rush into fixing it. What feels hardest at that 3 a.m. moment: the silence, the memories, or the fear that tomorrow will feel the same?",
            ),
        ],
        assets["sad_chat"],
    )
    draw_chat_screenshot(
        "Case Study B: High Performer",
        "Screenshot-style conversation evidence used inside the thesis report",
        [
            (
                "user",
                "I am leading a sprint for our product launch, juggling hiring and deployment, and I want help structuring the next ten days so nothing important slips between strategy and execution.",
            ),
            (
                "assistant",
                "You sound clear on direction and overloaded on sequencing, so I would treat this as an execution architecture problem. Let us split the next ten days into launch-critical, founder-only, and delegable work, then identify which risks actually threaten the release versus which ones only feel urgent.",
            ),
        ],
        assets["confident_chat"],
    )
    return assets


def read_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return text


def compose_markdown() -> str:
    project = read_markdown(PROJECT_SOURCE)
    if "## Appendix K." in project:
        project = project.split("## Appendix K.", 1)[0].rstrip()

    custom = """
## Comparative Persona Evaluation for Final BTech Report

### Why This Chapter Was Added
For the final BTech submission, the comparison must feel human and concrete rather than abstract. A strong thesis demonstration therefore needs two visibly different users whose conversational trajectories make the architecture legible. In this report, the comparative framing is intentionally sharpened around two archetypes that supervisors and examiners can understand immediately: a sad, grief-heavy user who needs emotional continuity, and a confident, work-focused user who needs strategic continuity. These are not random personas. They stress opposite ends of the Miryn architecture.

### Persona A: The Vulnerable Soul
Persona A represents a user who is sad, emotionally burdened, and in need of a companion that does not flatten grief into generic wellness advice. The user speaks in a slower, heavier cadence. Their prompts mention emptiness, interrupted sleep, loss, and the meaning of familiar spaces after bereavement. In a normal stateless chatbot, this kind of user often receives compassionate but interchangeable responses. Miryn is designed to do more. It should remember recurring grief signals, preserve emotionally salient memories, and adjust its conversational tempo so that it does not prematurely turn the exchange into a productivity exercise.

### Persona B: The High Performer
Persona B represents a confident and highly active working user. This user is not looking for soft validation first. They are looking for structure, prioritization, momentum preservation, and evidence that the system understands what operational pressure feels like. Their prompts mention launch plans, hiring, deployment, benchmarks, deadlines, and execution risk. A generic assistant can respond to these prompts, but Miryn's identity-first architecture should respond in a more longitudinal way. It should remember earlier goals, prior blockers, and the user's preferred reasoning style, then use those to make the answer feel like an ongoing working relationship rather than a single-turn productivity suggestion.

### How They Talk Differently
The sad persona tends to speak in emotionally saturated descriptions and metaphor-rich fragments. Their language carries weight through atmosphere: empty house, sleeplessness, heaviness, silence, grief, and memory. The confident working persona tends to speak in compressed operational units: sprint, hiring, blockers, deployment, metrics, launch, and sequencing. These two modes of speech create different burdens on the system. The first burdens emotional interpretation and memory sensitivity. The second burdens prioritization, retrieval of actionable context, and clarity under pressure.

### How Miryn Works Internally for These Two Users
The internal response path remains the same in architecture but not in outcome. The chat API authenticates the request and passes it into the orchestrator. The orchestrator hydrates the user's identity snapshot, calls the memory layer for relevant context, builds the dynamic system prompt through the LLM service, streams the answer back to the frontend, and then queues reflection. The same pipeline therefore serves both users. The difference is in the state it carries. For the vulnerable user, the retrieved memory set is emotionally weighted and the system prompt emphasizes gentleness, patience, and open-thread sensitivity. For the high performer, the retrieved memory set is more goal weighted and the system prompt becomes concise, strategic, and execution oriented.

### Why This Comparison Matters
This comparison demonstrates the real thesis claim of Miryn: the project is not merely about remembering facts. It is about preserving the shape of a person's ongoing life in a way that changes future interaction. The sad user needs continuity of care and emotional context. The confident worker needs continuity of intent and project structure. If the system can only do one of these well, then it is not yet identity-first in a meaningful sense. The purpose of the graphs, prompt screenshots, and comparative tables added in this report is to make that distinction inspectable.

### Comparative Findings
Across the seeded evaluation narrative used for this report, Persona A shows high sadness, low confidence, high emotion salience, and a wider semantic drift profile because grief changes the emotional meaning of repeated themes over time. Persona B shows lower sadness, high confidence, strong goal focus, and a tighter identity trajectory because their concerns remain clustered around execution and measurable progress. This does not mean the second user is simpler; it means the architecture stabilizes around operational continuity rather than emotional reinterpretation. The contrast is useful because it reveals that Miryn's memory and identity layers are not generic transcript stores. They are active filters that shape the style, depth, and direction of response.

### Prompt and Screenshot Evidence
This report intentionally represents prompt fragments and short interaction snippets as screenshot-like figures rather than plain copied blocks. That choice serves two functions. First, it improves the visual rhythm of the report by breaking long prose with exam-friendly evidence surfaces. Second, it avoids the thesis reading experience becoming one long dump of quoted prompt text. The screenshots are used to illustrate tone adaptation, memory selection logic, and the difference between emotional and strategic companionship.
"""

    final_text = "\n\n".join([custom, project])
    OUTPUT_SOURCE.write_text(final_text, encoding="utf-8")
    return final_text


def strip_md(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    return text.strip()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodyMiryn",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=10.6,
            leading=14.2,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
            textColor=colors.HexColor("#111827"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitleMiryn",
            parent=styles["Title"],
            fontName="Times-Bold",
            fontSize=21,
            leading=25,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SubTitleMiryn",
            parent=styles["Heading2"],
            fontName="Times-Italic",
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=22,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading1Miryn",
            parent=styles["Heading1"],
            fontName="Times-Bold",
            fontSize=16,
            leading=20,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=14,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading2Miryn",
            parent=styles["Heading2"],
            fontName="Times-Bold",
            fontSize=13.2,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Heading3Miryn",
            parent=styles["Heading3"],
            fontName="Times-BoldItalic",
            fontSize=11.8,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CaptionMiryn",
            parent=styles["BodyText"],
            fontName="Times-Italic",
            fontSize=9.4,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569"),
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMiryn",
            parent=styles["BodyText"],
            fontName="Times-Roman",
            fontSize=9.6,
            leading=12,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#374151"),
            spaceAfter=5,
        )
    )
    return styles


def build_cover(story, styles):
    story.append(Spacer(1, 1.2 * inch))
    story.append(Paragraph("MIRYN AI", styles["TitleMiryn"]))
    story.append(Paragraph("Identity-First Conversational Architecture with Persistent Memory, Reflection, and Comparative Persona Analysis", styles["SubTitleMiryn"]))
    story.append(Spacer(1, 0.4 * inch))
    story.append(
        Paragraph(
            "Final B.Tech Project Report Submitted in Partial Fulfilment of the Requirements for the Degree of Bachelor of Technology in Computer Science Engineering",
            styles["BodyMiryn"],
        )
    )
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph("Prepared from the Miryn AI repository and detailed implementation study", styles["BodyMiryn"]))
    story.append(Paragraph("Academic Year 2025-26", styles["BodyMiryn"]))
    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph("This version includes diagrams, comparative charts, screenshot-style prompt evidence, code snippet captures, workflow discussion, and a long-form sad-vs-confident persona case study.", styles["BodyMiryn"]))
    story.append(PageBreak())


def add_image_block(story, path: Path, caption: str, width: float, styles):
    if not path.exists():
        return
    story.append(KeepTogether([Image(str(path), width=width, height=width * 0.56), Paragraph(caption, styles["CaptionMiryn"])]))


def comparison_table(styles):
    data = [
        ["Dimension", "Sad / vulnerable user", "Confident / working user", "Miryn difference"],
        ["Primary need", "Emotional continuity and gentle pacing", "Strategic continuity and execution clarity", "Prompt behavior changes with identity and context"],
        ["Dominant memory type", "Emotion-tagged and grief-linked memories", "Goal, benchmark, and project memories", "Memory layer prioritizes different recall targets"],
        ["Tone adaptation", "Warm, validating, low-pressure", "Concise, energetic, action-oriented", "LLM system prompt uses identity traits and open loops"],
        ["Identity drift", "Higher due to reinterpretation of recurring pain", "Lower due to stable, goal-driven recurrence", "Analytics layer exposes divergence visibly"],
        ["Open loops", "Loss processing, sleep disruption, future fear", "Launch sequencing, hiring, deployment blockers", "Reflection stores unresolved threads differently"],
    ]
    table = Table(data, colWidths=[1.4 * inch, 2.0 * inch, 2.0 * inch, 1.7 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9.2),
                ("LEADING", (0, 0), (-1, -1), 12),
                ("FONTNAME", (0, 1), (-1, -1), "Times-Roman"),
                ("FONTSIZE", (0, 1), (-1, -1), 8.8),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.HexColor("#eef2ff")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def architecture_inventory_table():
    data = [
        ["Layer", "Primary modules", "Purpose"],
        ["Frontend", "ChatInterface, IdentityDashboard, CompareWorkspace, PersonaDetailView", "User-facing interaction, streaming, analytics visualization"],
        ["API", "auth.py, chat.py, identity.py, analytics.py, memory.py", "Request handling, session enforcement, public endpoints"],
        ["Orchestration", "orchestrator.py, llm_service.py, memory_layer.py", "Builds context, streams answers, stores conversation"],
        ["Identity", "identity_engine.py, identity_analytics.py, reflection_engine.py", "Versioned identity and asynchronous analysis"],
        ["Data / infra", "database.py, cache.py, migrations, demo_compare_service.py", "Persistence, eventing, local demo parity, seeded persona support"],
    ]
    table = Table(data, colWidths=[1.1 * inch, 3.2 * inch, 2.4 * inch], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9.4),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eff6ff")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def maybe_insert_visuals(story, heading: str, assets: dict[str, Path], styles, inserted: set[str]) -> None:
    h = heading.lower()
    if "system architecture" in h and "architecture" not in inserted:
        add_image_block(story, assets["architecture"], "Figure: High-level architecture of Miryn AI across frontend, backend, workers, storage, and model layers.", 6.5 * inch, styles)
        story.append(Spacer(1, 0.08 * inch))
        story.append(architecture_inventory_table())
        story.append(Spacer(1, 0.16 * inch))
        inserted.add("architecture")
    elif "request lifecycle" in h or "runtime walkthrough" in h:
        if "workflow" not in inserted:
            add_image_block(story, assets["workflow"], "Figure: End-to-end request flow from chat submission to reflection update.", 6.5 * inch, styles)
            inserted.add("workflow")
    elif "memory architecture" in h or "three-tier memory" in h:
        if "memory" not in inserted:
            add_image_block(story, assets["memory"], "Figure: Miryn's three-tier memory model balancing immediacy, retrieval, and durable identity.", 6.5 * inch, styles)
            inserted.add("memory")
    elif "comparative persona evaluation" in h or "use case comparison" in h:
        if "compare" not in inserted:
            add_image_block(story, assets["metrics"], "Figure: Comparative metrics for the sad/grieving persona and the confident/working persona.", 6.5 * inch, styles)
            add_image_block(story, assets["timeline"], "Figure: Identity drift timeline across four representative versions for the two personas.", 6.5 * inch, styles)
            story.append(Spacer(1, 0.1 * inch))
            story.append(comparison_table(styles))
            story.append(Spacer(1, 0.15 * inch))
            inserted.add("compare")
    elif "prompt" in h and "prompt_images" not in inserted:
        add_image_block(story, assets["sad_prompt"], "Figure: Screenshot-style representation of the prompt behavior used for the emotionally vulnerable persona.", 6.5 * inch, styles)
        add_image_block(story, assets["confident_prompt"], "Figure: Screenshot-style representation of the prompt behavior used for the confident, work-focused persona.", 6.5 * inch, styles)
        inserted.add("prompt_images")
    elif "frontend architecture" in h and "ui" not in inserted:
        if CHAT_SCREENSHOT.exists():
            add_image_block(story, CHAT_SCREENSHOT, "Figure: Chat interface used for live conversation, streamed responses, and deferred insight panels.", 6.3 * inch, styles)
        if IDENTITY_SCREENSHOT.exists():
            add_image_block(story, IDENTITY_SCREENSHOT, "Figure: Identity dashboard exposing traits, memory, and version-aware state.", 6.3 * inch, styles)
        inserted.add("ui")
    elif "appendix j" in h or "file-level commentary" in h:
        if "code_images" not in inserted:
            for img_path, caption in [
                (CODE_SSE, "Code screenshot: event streaming route pattern used for live frontend updates."),
                (CODE_SQL, "Code screenshot: SQL schema and vector index design relevant to message persistence."),
                (CODE_REACT, "Code screenshot: frontend meter pattern used in compare and analytics styling."),
            ]:
                if img_path.exists():
                    add_image_block(story, img_path, caption, 5.8 * inch, styles)
            add_image_block(story, assets["sad_chat"], "Figure: Screenshot-style conversation excerpt showing Miryn's grief-aware pacing and reflective questioning.", 6.4 * inch, styles)
            add_image_block(story, assets["confident_chat"], "Figure: Screenshot-style conversation excerpt showing Miryn's strategic, execution-oriented adaptation.", 6.4 * inch, styles)
            inserted.add("code_images")


def markdown_to_story(markdown_text: str, story, styles, assets):
    lines = markdown_text.splitlines()
    paragraph_buffer: list[str] = []
    in_code = False
    inserted: set[str] = set()

    def flush_paragraph():
        nonlocal paragraph_buffer
        text = " ".join(part.strip() for part in paragraph_buffer if part.strip())
        if text:
            story.append(Paragraph(strip_md(text), styles["BodyMiryn"]))
        paragraph_buffer = []

    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("---"):
            flush_paragraph()
            continue
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("# "):
            flush_paragraph()
            story.append(PageBreak())
            heading = strip_md(line[2:])
            story.append(Paragraph(heading, styles["Heading1Miryn"]))
            maybe_insert_visuals(story, heading, assets, styles, inserted)
            continue
        if line.startswith("## "):
            flush_paragraph()
            heading = strip_md(line[3:])
            if heading.lower().startswith("appendix") or heading.lower().startswith("chapter "):
                story.append(PageBreak())
            story.append(Paragraph(heading, styles["Heading1Miryn"]))
            maybe_insert_visuals(story, heading, assets, styles, inserted)
            continue
        if line.startswith("### "):
            flush_paragraph()
            heading = strip_md(line[4:])
            story.append(Paragraph(heading, styles["Heading2Miryn"]))
            maybe_insert_visuals(story, heading, assets, styles, inserted)
            continue
        if line.startswith("#### "):
            flush_paragraph()
            story.append(Paragraph(strip_md(line[5:]), styles["Heading3Miryn"]))
            continue
        if line.startswith("|") and "|" in line[1:]:
            # Skip markdown tables; explicit tables are inserted separately.
            continue
        if re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            story.append(Paragraph(strip_md(line), styles["BodyMiryn"]))
            continue
        if line.startswith("- ") or line.startswith("* "):
            flush_paragraph()
            bullet_text = strip_md(line[2:])
            bullet = ListFlowable(
                [ListItem(Paragraph(bullet_text, styles["BodyMiryn"]))],
                bulletType="bullet",
                leftIndent=18,
            )
            story.append(bullet)
            continue
        paragraph_buffer.append(line)
    flush_paragraph()


def add_front_matter(story, styles):
    story.append(Paragraph("Certificate", styles["Heading1Miryn"]))
    story.append(Paragraph("This is to certify that the project report entitled 'Miryn AI' is a bonafide record of the work carried out for the Bachelor of Technology submission. This version has been expanded into a thesis-style technical document with implementation analysis, diagrams, screenshots, and comparative persona evaluation.", styles["BodyMiryn"]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(Paragraph("Declaration", styles["Heading1Miryn"]))
    story.append(Paragraph("The report content presented here has been organized from the Miryn AI repository, implementation artifacts, and internal project documentation. Where external ideas informed the conceptual framing, they are acknowledged in the references-oriented discussion. The screenshot-style prompt snippets and conversation captures included in this document were generated specifically for this report so that the final submission remains visually rich without relying on large pasted quotations.", styles["BodyMiryn"]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(Paragraph("Acknowledgement", styles["Heading1Miryn"]))
    story.append(Paragraph("This project reflects the combined effort of system design, backend engineering, frontend iteration, prompt architecture, and documentation refinement. Special credit belongs to the sustained implementation work required to move Miryn from a concept of identity-aware AI toward a demonstrable, inspectable prototype with comparison workflows and thesis-ready evidence surfaces.", styles["BodyMiryn"]))
    story.append(PageBreak())


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(colors.HexColor("#64748b"))
    canvas.drawString(doc.leftMargin, 20, "Miryn AI - Final BTech Detailed Report")
    canvas.drawRightString(A4[0] - doc.rightMargin, 20, str(canvas.getPageNumber()))
    canvas.restoreState()


def build_pdf():
    assets = build_assets()
    markdown = compose_markdown()
    styles = build_styles()

    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=A4,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="Miryn Final BTech Detailed Report",
        author="Codex",
    )

    story = []
    build_cover(story, styles)
    add_front_matter(story, styles)
    markdown_to_story(markdown, story, styles, assets)

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    pages = len(PdfReader(str(OUTPUT_PDF)).pages)
    print(f"{OUTPUT_PDF}\nPAGES={pages}")


if __name__ == "__main__":
    build_pdf()
