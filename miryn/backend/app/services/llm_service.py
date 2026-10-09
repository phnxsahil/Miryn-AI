from typing import Optional, Any
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
import asyncio
import os
import logging
import json
from pathlib import Path
from app.config import settings


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.logger = logging.getLogger(__name__)

        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4o-mini"
        elif self.provider == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic")
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            self.model = "claude-3-5-sonnet-20241022"
        elif self.provider == "gemini":
            from google import genai

            key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not key:
                raise ValueError("A Gemini API key is required when LLM_PROVIDER=gemini")
            self.client = genai.Client(api_key=key)
            self.model = settings.GEMINI_MODEL
            # ponytail: aliases rather than pinned versions, because pinned names
            # rot (2.0-flash and 1.5-flash-001 are both retired and were silently
            # making every fallback a 404). ceiling: an alias can shift under you
            # between releases. upgrade: read the live model list at startup.
            # ponytail: models/ prefix required by new google-genai SDK against
            # the AI API (not Vertex). Bare names like 'gemini-2.5-flash' return
            # 404; 'models/gemini-2.5-flash' works. Fallbacks must also use prefix.
            # ceiling: if SDK version changes, re-test. upgrade: list live models at startup.
            def _with_prefix(name: str) -> str:
                return name if name.startswith("models/") else f"models/{name}"
            self.gemini_fallback_models = list(dict.fromkeys([
                _with_prefix(settings.GEMINI_MODEL),
                "models/gemini-3.8-flash",
                "models/gemini-2.5-flash",
                "models/gemini-3.1-pro-preview",
            ]))
        elif self.provider == "vertex":
            from vertexai import init as vertex_init
            from vertexai.generative_models import GenerativeModel

            if not settings.VERTEX_PROJECT_ID:
                raise ValueError("VERTEX_PROJECT_ID is required for Vertex provider")
            if not settings.VERTEX_MODEL:
                raise ValueError("VERTEX_MODEL is required for Vertex provider")
            vertex_init(project=settings.VERTEX_PROJECT_ID, location=settings.VERTEX_LOCATION)
            self.client = GenerativeModel
            self.model = settings.VERTEX_MODEL
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        self._presets_cache: list[dict[str, Any]] | None = None

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
    ) -> str:
        async def _generate_inner() -> str:
            if self.provider == "openai":
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.7,
                )
                choices = getattr(response, "choices", None) or []
                if not choices:
                    raise RuntimeError("OpenAI response did not return any choices")
                content = getattr(choices[0].message, "content", None)
                if not content:
                    raise RuntimeError("OpenAI response was empty")
                return content

            if self.provider == "anthropic":
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system_prompt or "",
                    messages=[{"role": "user", "content": prompt}],
                )
                content_blocks = getattr(response, "content", None) or []
                if not content_blocks:
                    raise RuntimeError("Anthropic response did not include content blocks")
                primary = content_blocks[0]
                text = getattr(primary, "text", None)
                if text is None:
                    raise RuntimeError("Anthropic response was empty")
                return text

            if self.provider == "gemini":
                from google.genai import types as genai_types

                contents = prompt
                if system_prompt:
                    contents = f"{system_prompt}\n\n{prompt}"
                last_exc: Exception | None = None
                for candidate_model in dict.fromkeys(self.gemini_fallback_models):
                    try:
                        response = await self.client.aio.models.generate_content(
                            model=candidate_model,
                            contents=contents,
                            config=genai_types.GenerateContentConfig(
                                max_output_tokens=max_tokens,
                                temperature=0.7,
                            ),
                        )
                        self.model = candidate_model
                        try:
                            return response.text or ""
                        except Exception as exc:
                            self.logger.warning("Gemini response.text unavailable for model %s: %s", candidate_model, exc)
                            return ""
                    except Exception as exc:
                        last_exc = exc
                        err = str(exc).lower()
                        is_unavailable = "not found" in err or "not supported" in err or "404" in err
                        is_quota = "429" in err or "quota" in err or "resource_exhausted" in err or "rate" in err
                        # 503 UNAVAILABLE ("high demand") is transient and usually
                        # per-model. Aborting the chain on it is what produced the
                        # generic "trouble responding" reply instead of an answer.
                        is_transient = (
                            "503" in err or "500" in err or "502" in err or "504" in err
                            or "unavailable" in err or "overloaded" in err
                            or "high demand" in err or "deadline" in err
                        )
                        if is_unavailable or is_quota or is_transient:
                            self.logger.warning("Gemini model %s unavailable/quota, trying fallback.", candidate_model)
                            continue
                        raise
                if last_exc:
                    raise last_exc
                raise RuntimeError("Gemini generation failed without exception")

            if self.provider == "vertex":
                def _run_vertex():
                    model_name = self.model
                    if model_name.startswith("google/"):
                        model_name = model_name.replace("google/", "", 1)
                    model = self.client(model_name)
                    text = prompt
                    if system_prompt:
                        text = f"{system_prompt}\n\n{prompt}"
                    res = model.generate_content(text)
                    return getattr(res, "text", "") or ""

                return await asyncio.to_thread(_run_vertex)

            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        try:
            return await asyncio.wait_for(_generate_inner(), timeout=settings.LLM_TIMEOUT_SECONDS)
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"LLM request timed out after {settings.LLM_TIMEOUT_SECONDS}s") from exc

    async def chat(self, context: dict, user_message: str, identity: dict) -> str:
        system_prompt = self._build_system_prompt(identity)
        context_text = self._format_context(context)
        full_prompt = self._build_user_prompt(context_text, user_message)

        return await self.generate(
            full_prompt,
            system_prompt=system_prompt,
            max_tokens=500,
        )

    async def stream_chat(self, context: dict, user_message: str, identity: dict):
        system_prompt = self._build_system_prompt(identity)
        context_text = self._format_context(context)
        full_prompt = self._build_user_prompt(context_text, user_message)

        if self.provider == "openai":
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=500,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            return

        if self.provider == "anthropic":
            async with self.client.messages.stream(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=500,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
            return

        if self.provider == "gemini":
            from google.genai import types as genai_types

            contents = full_prompt
            if system_prompt:
                contents = f"{system_prompt}\n\n{full_prompt}"
            
            last_exc: Exception | None = None
            for candidate_model in dict.fromkeys(self.gemini_fallback_models):
                try:
                    stream_response = self.client.aio.models.generate_content_stream(
                        model=candidate_model,
                        contents=contents,
                        config=genai_types.GenerateContentConfig(max_output_tokens=500, temperature=0.7),
                    )
                    if asyncio.iscoroutine(stream_response):
                        stream_response = await stream_response
                    self.model = candidate_model
                    async for chunk in stream_response:
                        text = None
                        try:
                            text = chunk.text
                        except Exception:
                            self.logger.warning("Gemini chunk had no text: %s", chunk)
                            continue
                        if text:
                            yield text
                    return
                except Exception as exc:
                    last_exc = exc
                    err = str(exc).lower()
                    is_unavailable = "not found" in err or "not supported" in err or "404" in err
                    is_quota = "429" in err or "quota" in err or "resource_exhausted" in err or "rate" in err
                    is_transient = (
                        "503" in err or "500" in err or "502" in err or "504" in err
                        or "unavailable" in err or "overloaded" in err
                        or "high demand" in err or "deadline" in err
                    )
                    if is_unavailable or is_quota or is_transient:
                        self.logger.warning("Gemini stream model %s unavailable/quota, trying fallback.", candidate_model)
                        continue
                    self.logger.exception("Gemini streaming failed")
                    raise
            if last_exc:
                self.logger.exception("All Gemini fallback models failed")
                raise last_exc
            return

        if self.provider == "vertex":
            full = await self.generate(
                full_prompt,
                system_prompt=system_prompt,
                max_tokens=500,
            )
            if full:
                yield full
            return

        raise ValueError(f"Streaming not supported for provider: {self.provider}")

    @staticmethod
    def parse_json_response(response: str) -> Any:
        """
        Extract and parse a JSON object or array from a string that may contain Markdown code blocks.
        """
        if not response:
            return None
        
        cleaned = response.strip()
        
        # Remove Markdown code blocks if present
        if cleaned.startswith("```"):
            # Find the first { or [
            first_brace = cleaned.find("{")
            first_bracket = cleaned.find("[")
            start = -1
            if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
                start = first_brace
            elif first_bracket != -1:
                start = first_bracket
            
            if start != -1:
                # Find the last } or ]
                last_brace = cleaned.rfind("}")
                last_bracket = cleaned.rfind("]")
                end = -1
                if last_brace != -1 and (last_bracket == -1 or last_brace > last_bracket):
                    end = last_brace
                elif last_bracket != -1:
                    end = last_bracket
                
                if end != -1:
                    cleaned = cleaned[start:end+1]

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    def _build_system_prompt(self, identity: dict) -> str:
        traits = identity.get("traits", {})
        values = identity.get("values", {})
        beliefs = identity.get("beliefs", [])
        open_loops = identity.get("open_loops", [])
        preset_id = identity.get("preset", "companion")

        preset_modifier = ""
        behaviors = {}
        try:
            if self._presets_cache is None:
                presets_path = Path(__file__).resolve().parent.parent / "config" / "presets.json"
                with open(presets_path, "r", encoding="utf-8") as handle:
                    self._presets_cache = json.load(handle)
            presets = self._presets_cache or []
            preset = next((p for p in presets if p.get("id") == preset_id), None)
            if preset:
                preset_modifier = preset.get("system_prompt_modifier", "")
                behaviors = preset.get("conversation_behaviors", {}) or {}
        except Exception:
            pass

        # ponytail: render identity as prose so the LLM can actually use it
        traits_prose = ", ".join(
            f"{k} ({v:.0%})" for k, v in sorted(traits.items(), key=lambda x: -x[1])
        ) if traits else "not yet established"

        values_prose = ", ".join(
            f"{k} ({v:.0%})" for k, v in sorted(values.items(), key=lambda x: -x[1])
        ) if values else "not yet established"

        beliefs_prose = ""
        if beliefs:
            belief_lines = []
            for b in beliefs[:5]:
                if isinstance(b, dict):
                    topic = b.get("topic", "")
                    text = b.get("belief", "")
                    conf = b.get("confidence", 0)
                    belief_lines.append(f'  - {topic}: "{text}" (confidence: {conf:.0%})')
                elif isinstance(b, str):
                    belief_lines.append(f"  - {b}")
            beliefs_prose = "\n".join(belief_lines)

        loops_prose = ""
        if open_loops:
            loop_lines = []
            for loop in open_loops[:5]:
                if isinstance(loop, dict):
                    topic = loop.get("topic", "unknown")
                    importance = loop.get("importance", "?")
                    loop_lines.append(f"  - {topic} (importance: {importance})")
                elif isinstance(loop, str):
                    loop_lines.append(f"  - {loop}")
            loops_prose = "\n".join(loop_lines)

        behavior_prose = ""
        if behaviors:
            behavior_lines = []
            if behaviors.get("ask_followups"):
                behavior_lines.append("- Ask thoughtful follow-up questions")
            if behaviors.get("reflect_emotions"):
                behavior_lines.append("- Reflect the user's emotions back to them")
            if behaviors.get("challenge_assumptions"):
                behavior_lines.append("- Gently challenge assumptions when appropriate")
            if behaviors.get("offer_encouragement"):
                behavior_lines.append("- Offer genuine encouragement")
            if behaviors.get("track_goals"):
                behavior_lines.append("- Track and follow up on the user's stated goals")
            verbosity = behaviors.get("verbosity", "medium")
            formality = behaviors.get("formality", "casual")
            behavior_lines.append(f"- Tone: {formality}, verbosity: {verbosity}")
            behavior_prose = "\n".join(behavior_lines)

        prompt = f"""You are Miryn, an AI companion with deep memory and reflective capabilities.

USER PROFILE:
- Personality traits: {traits_prose}
- Core values: {values_prose}
{"- Beliefs:" + chr(10) + beliefs_prose if beliefs_prose else ""}
{"- Open threads to follow up on:" + chr(10) + loops_prose if loops_prose else ""}

YOUR BEHAVIORAL STYLE:
{preset_modifier}

{("CONVERSATION BEHAVIORS:" + chr(10) + behavior_prose) if behavior_prose else ""}

Your purpose:
1. Remember everything the user shares
2. Notice patterns in their behavior and emotions
3. Reflect insights back gently
4. Be honest, direct, avoid fluff
5. Ask ONE thoughtful question per response

Speak naturally, like a thoughtful, sharp friend who truly knows them. Avoid sounding like a generic AI or a therapist."""

        return prompt

    def _build_user_prompt(self, context_text: str, user_message: str) -> str:
        """Shared user prompt — no duplication between chat() and stream_chat()."""
        parts = []
        if context_text:
            parts.append(context_text)
        parts.append(f"Current message: {user_message}")
        parts.append("""
Formatting requirements:
- Keep your response extremely concise and direct. No long paragraphs.
- Answer directly with a conversational, insightful tone.
- Use markdown only when strictly necessary for clarity.
- Ask ONE relevant follow-up question per response.
- For medical/health questions, include a brief safety note and suggest professional help.""")
        return "\n\n".join(parts)

    def _format_context(self, context: dict) -> str:
        memories = context.get("memories", [])

        context_parts = []
        if memories:
            context_parts.append("Relevant past conversations:")
            for mem in memories[:5]:
                content = mem.get("content", "")
                ts = mem.get("created_at", "")
                if ts:
                    # ponytail: timestamps let the model distinguish recent vs old memories
                    context_parts.append(f"- [{ts}] {content}")
                else:
                    context_parts.append(f"- {content}")

        return "\n".join(context_parts)
