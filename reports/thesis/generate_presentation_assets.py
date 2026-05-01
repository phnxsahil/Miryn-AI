from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "generated_assets"
ASSETS.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


TITLE = font(30, True)
HEAD = font(22, True)
BODY = font(18, False)


def draw_box(draw: ImageDraw.ImageDraw, box, fill: str, title: str, rows: list[str]) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=24, fill=fill, outline="#334155", width=3)
    draw.rectangle((x1, y1, x2, y1 + 42), fill="#0f172a")
    draw.text((x1 + 16, y1 + 9), title, font=HEAD, fill="white")
    y = y1 + 58
    for row in rows:
        draw.text((x1 + 18, y), row, font=BODY, fill="#111827")
        y += 28


def draw_er_diagram(out_path: Path) -> None:
    width, height = 1600, 980
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    draw.text((55, 35), "Miryn AI ER Diagram", font=TITLE, fill="#111827")

    users = (90, 140, 410, 310)
    conversations = (530, 120, 920, 270)
    messages = (1010, 90, 1500, 360)
    identities = (520, 420, 930, 650)
    evolution = (1030, 470, 1500, 740)
    onboarding = (100, 470, 420, 680)

    draw_box(draw, users, "#dbeafe", "users", [
        "PK id",
        "email",
        "password_hash",
        "is_verified",
        "last_seen_at",
    ])
    draw_box(draw, conversations, "#dcfce7", "conversations", [
        "PK id",
        "FK user_id -> users.id",
        "title",
        "created_at / updated_at",
    ])
    draw_box(draw, messages, "#fde68a", "messages", [
        "PK id",
        "FK conversation_id -> conversations.id",
        "FK user_id -> users.id",
        "role",
        "content",
        "embedding vector(384)",
        "importance_score",
        "idempotency_key",
    ])
    draw_box(draw, identities, "#e9d5ff", "identities", [
        "PK id",
        "FK user_id -> users.id",
        "version",
        "state",
        "traits / values",
        "beliefs / open_loops",
        "memory_weights / drift_score",
    ])
    draw_box(draw, evolution, "#fbcfe8", "identity_evolution_log", [
        "PK id",
        "FK user_id -> users.id",
        "FK identity_id -> identities.id",
        "field_changed",
        "old_value / new_value",
        "trigger_type",
    ])
    draw_box(draw, onboarding, "#bfdbfe", "onboarding_responses", [
        "PK id",
        "FK user_id -> users.id",
        "question",
        "answer",
        "created_at",
    ])

    relations = [
        ((410, 220), (530, 195), "1:N"),
        ((920, 195), (1010, 195), "1:N"),
        ((340, 310), (620, 420), "1:N"),
        ((260, 310), (260, 470), "1:N"),
        ((930, 535), (1030, 575), "1:N"),
        ((380, 230), (1010, 240), "1:N"),
    ]

    for (x1, y1), (x2, y2), label in relations:
        draw.line((x1, y1, x2, y2), fill="#2563eb", width=5)
        draw.text(((x1 + x2) / 2 - 18, (y1 + y2) / 2 - 20), label, font=BODY, fill="#1d4ed8")
        draw.polygon([(x2, y2), (x2 - 16, y2 - 10), (x2 - 16, y2 + 10)], fill="#2563eb")

    draw.text((55, 900), "Core relational story: one user owns conversations, messages, identity versions, and onboarding data. Identity evolution is stored as an append-only log.", font=BODY, fill="#475569")
    img.save(out_path)


if __name__ == "__main__":
    draw_er_diagram(ASSETS / "er_diagram.png")
    print(str(ASSETS / "er_diagram.png"))
