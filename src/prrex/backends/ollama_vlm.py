# DRAFT 2026-10-28 (bulk scaffold): NOT IMPLEMENTED-VERIFIED. Untested; refine + add tests before use. See docs/drafts/BULK-SCAFFOLD-2026-10-28.md
"""Local VLM supervisor via Ollama HTTP API (local-first, no paid API, §6). Model is a setting, e.g. a small
vision model that fits the RTX 4060's 8 GB. Output must be JSON; malformed output -> confidence 0, no subgoals."""

from __future__ import annotations

import base64
import io
import json
import time
import urllib.request

from PIL import Image

from .base import Subgoal, SupervisorOutput, register_supervisor

PROMPT = """You are the supervisor of a game-playing companion. The player directs; you plan.
World state (observed facts with confidence and age):
{world}
Player goal: {goal}
Recent history: {history}
Images: high-resolution regions of interest from the current frame.
Reply ONLY with JSON: {{"phase": "menu|gameplay|loading|cutscene|paused|unknown", "objective": str|null,
"subgoals": [{{"text": str, "success_check": str|null, "timeout_s": number}}], "explanation": str, "confidence": 0..1}}
Say "unknown" and low confidence when unsure. Never claim to see things not in the images."""


def _b64(img) -> str:
    buf = io.BytesIO()
    Image.fromarray(img).save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


class OllamaSupervisor:
    def __init__(
        self,
        model: str = "qwen2.5vl:3b",
        host: str = "http://127.0.0.1:11434",
        timeout_s: float = 30.0,
        max_images: int = 3,
    ):
        self.model, self.host, self.timeout_s, self.max_images = model, host, timeout_s, max_images
        self.name = f"ollama:{model}"

    def assess(self, rois, world_text, player_goal, history):
        t0 = time.monotonic()
        body = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "user",
                    "content": PROMPT.format(
                        world=world_text or "(none)",
                        goal=player_goal or "(none)",
                        history="; ".join(history[-5:]) or "(none)",
                    ),
                    "images": [_b64(v) for v in list(rois.values())[: self.max_images]],
                }
            ],
        }
        req = urllib.request.Request(
            self.host + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as r:
            raw = json.loads(r.read())["message"]["content"]
        ms = (time.monotonic() - t0) * 1000
        try:
            d = json.loads(raw)
            subs = [
                Subgoal(s["text"], s.get("success_check"), float(s.get("timeout_s", 30))) for s in d.get("subgoals", [])
            ]
            return SupervisorOutput(
                d.get("phase"),
                d.get("objective"),
                subs,
                d.get("explanation", ""),
                float(d.get("confidence", 0)),
                ms,
                self.name,
                raw,
            )
        except Exception as e:
            return SupervisorOutput(None, None, [], f"unparseable output: {e!r}", 0.0, ms, self.name, raw)


register_supervisor("ollama", lambda **o: OllamaSupervisor(**o))
