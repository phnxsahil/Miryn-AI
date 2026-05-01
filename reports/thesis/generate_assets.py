import os
from pygments import highlight
from pygments.lexers import PythonLexer, SqlLexer, TypeScriptLexer
from pygments.formatters import ImageFormatter

output_dir = "d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images"
os.makedirs(output_dir, exist_ok=True)

# Code Snippet: Python SSE
code_python = """@router.get("/events/stream")
async def stream_events(request: Request, authorization: str | None = Header(default=None)):
    token = request.query_params.get("token")
    user_id = get_user_id_from_token(token)

    async def event_stream():
        while True:
            if await request.is_disconnected():
                break
            events = await asyncio.to_thread(drain_events, user_id, 50)
            for event in events:
                payload = json.dumps(event)
                yield f"data: {payload}\\n\\n"
            await asyncio.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")"""

with open(f"{output_dir}/code_sse.png", "wb") as f:
    f.write(highlight(code_python, PythonLexer(), ImageFormatter(style="monokai", font_size=16, line_numbers=True)))

# Code Snippet: SQL
code_sql = """CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    content_encrypted TEXT,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS messages_embedding_idx ON messages USING hnsw (embedding vector_cosine_ops);"""

with open(f"{output_dir}/code_sql.png", "wb") as f:
    f.write(highlight(code_sql, SqlLexer(), ImageFormatter(style="monokai", font_size=16, line_numbers=True)))

# Code Snippet: React
code_react = """function Meter({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="h-2 w-full rounded-full bg-white/10">
      <div
        className="h-2 rounded-full bg-gradient-to-r from-amber-400/80 via-amber-300/70 to-white/60"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}"""

with open(f"{output_dir}/code_react.png", "wb") as f:
    f.write(highlight(code_react, TypeScriptLexer(), ImageFormatter(style="monokai", font_size=16, line_numbers=True)))

print("All PNG code screenshots generated successfully.")
