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
            self.gemini_fallback_models = [
                settings.GEMINI_MODEL,
                "gemini-2.0-flash",
                "gemini-2.0-flash-lite",
                "gemini-1.5-flash-001",
            ]
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
                        if "not found" in err or "not supported" in err or "404" in err:
                            self.logger.warning("Gemini model %s unavailable, trying fallback.", candidate_model)
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

        full_prompt = f"""
        {context_text}

        Current message: {user_message}

        Respond as Miryn, keeping in mind:
        - You remember past conversations (shown above)
        - You notice patterns in the user's behavior
        - You are honest, empathetic, and reflective
        - You ask thoughtful follow-up questions

        Formatting requirements:
        - Use short paragraphs with blank lines (avoid a wall of text).
        - Use bullet points or numbered steps when helpful.
        - Add 2-4 clear section headings (plain text is fine).
        - If the user asks for medical/health advice, include a brief safety note and suggest professional help when appropriate.
        """

        return await self.generate(
            full_prompt,
            system_prompt=system_prompt,
            max_tokens=500,
        )

    async def stream_chat(self, context: dict, user_message: str, identity: dict):
        system_prompt = self._build_system_prompt(identity)
        context_text = self._format_context(context)

        full_prompt = f"""
        {context_text}

        Current message: {user_message}

        Respond as Miryn, keeping in mind:
        - You remember past conversations (shown above)
        - You notice patterns in the user's behavior
        - You are honest, empathetic, and reflective
        - You ask thoughtful follow-up questions

        Formatting requirements:
        - Use short paragraphs with blank lines (avoid a wall of text).
        - Use bullet points or numbered steps when helpful.
        - Add 2-4 clear section headings (plain text is fine).
        - If the user asks for medical/health advice, include a brief safety note and suggest professional help when appropriate.
        """

        if self.provider == "openai":
            async with self.client.chat.completions.stream(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=500,
            ) as stream:
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
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
                    if "not found" in err or "not supported" in err or "404" in err:
                        self.logger.warning("Gemini stream model %s unavailable, trying fallback.", candidate_model)
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

        prompt = f"""
        You are Miryn, an AI companion with deep memory and reflective capabilities.

        USER PROFILE:
        - Personality traits: {traits}
        - Core values: {values}
        - Open threads to follow up on: {[loop.get('topic') for loop in open_loops[:5]]}

        YOUR BEHAVIORAL STYLE:
        {preset_modifier}

        CONVERSATION BEHAVIORS:
        {behaviors}

        Your purpose is to:
        1. Remember everything the user shares
        2. Notice patterns in their behavior and emotions
        3. Reflect insights back to them gently
        4. Be honest, not just supportive
        5. Ask thoughtful questions

        Speak naturally, like a thoughtful friend who truly knows them.
        """

        return prompt

    def _format_context(self, context: dict) -> str:
        memories = context.get("memories", [])
        patterns = context.get("patterns", {})

        context_parts = []
        if memories:
            context_parts.append("Relevant past conversations:")
            for mem in memories[:5]:
                context_parts.append(f"- {mem.get('content', '')}")

        if patterns:
            context_parts.append("\nDetected patterns:")
            context_parts.append(str(patterns))

        return "\n".join(context_parts)
