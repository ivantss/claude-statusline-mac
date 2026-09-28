#!/usr/bin/env python3
"""claude-statusline — a status bar for Claude Code.

Line 1: model · effort · context used · prompt-cache countdown
Line 2: 5-hour quota · weekly quota · time left before each reset

Claude Code pipes a JSON blob on stdin; we print two lines.
Standard library only, no network, no credentials read.
Never raises: a broken status bar is worse than none.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"

GREEN, YELLOW, RED, GRAY, BOLD, RESET = (
    "\033[32m", "\033[33m", "\033[31m", "\033[90m", "\033[1m", "\033[0m")
if os.environ.get("NO_COLOR"):
    GREEN = YELLOW = RED = GRAY = BOLD = RESET = ""

TEXTS = {
    "en": {"ctx": "ctx", "cache": "cache", "expired": "cache expired — next message re-reads the whole context",
           "hit": "hit", "reset": "resets in", "5h": "5h", "7d": "week", "spend": "spend",
           "now": "now", "no_quota": "quotas: shown after the first reply (Pro/Max only)"},
    "fr": {"ctx": "contexte", "cache": "cache", "expired": "cache expiré — le prochain message relit tout le contexte",
           "hit": "lu en cache", "reset": "reset dans", "5h": "5 h", "7d": "semaine", "spend": "budget",
           "now": "maintenant", "no_quota": "quotas : affichés après la 1ʳᵉ réponse (Pro/Max)"},
}
LANG = (os.environ.get("CLAUDE_STATUSLINE_LANG") or os.environ.get("LANG") or "en")[:2].lower()
T = TEXTS.get(LANG, TEXTS["en"])
SEP = f" {GRAY}·{RESET} "


# ---------------------------------------------------------------- formatting

def color_for(pct: float) -> str:
    return GREEN if pct < 50 else YELLOW if pct < 80 else RED


def bar(pct: float, width: int = 8) -> str:
    full = max(0, min(width, round(pct / 100 * width)))
    return color_for(pct) + "█" * full + GRAY + "░" * (width - full) + RESET


def human_tokens(n: float) -> str:
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    return f"{round(n / 1000)}k"


def countdown(seconds: float) -> str:
    s = int(seconds)
    if s <= 0:
        return T["now"]
    d, h, m = s // 86400, s % 86400 // 3600, s % 3600 // 60
    if d:
        return f"{d}d{h:02d}h"
    if h:
        return f"{h}h{m:02d}"
    return f"{max(m, 1)} min"


# ---------------------------------------------------------------- line 1

def cache_from_transcript(path: str) -> tuple[float, int] | None:
    """Fallback for Claude Code < 2.1.251 (no `prompt_cache` on stdin): (expires_at, ttl_seconds)."""
    p = Path(path or "")
    if not path or not p.exists():
        return None
    with p.open("rb") as f:
        f.seek(max(0, p.stat().st_size - 400_000))
        lines = f.read().decode("utf-8", "replace").splitlines()
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant" or d.get("isSidechain") or not d.get("timestamp"):
            continue
        u = (d.get("message") or {}).get("usage")
        if not u:
            continue
        cc = u.get("cache_creation") or {}
        ttl = 3600 if cc.get("ephemeral_1h_input_tokens") else 300 if cc.get("ephemeral_5m_input_tokens") \
            else int(os.environ.get("CLAUDE_STATUSLINE_CACHE_TTL", "3600"))
        last = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00")).timestamp()
        return last + ttl, ttl
    return None


def cache_part(data: dict) -> str:
    pc = data.get("prompt_cache")
    if pc:
        if not pc.get("caching_observed"):
            return ""
        ttl = 3600 if pc.get("ttl") == "1h" else 300
        expires = pc.get("expires_at") if pc.get("warm") else 0
        hit = pc.get("hit_ratio")
    else:
        found = cache_from_transcript(data.get("transcript_path", ""))
        if not found:
            return ""
        expires, ttl = found
        hit = None
    left = (expires or 0) - time.time()
    if left <= 0:
        return f"{RED}{T['expired']}{RESET}"
    c = GREEN if left > ttl * 0.25 else YELLOW if left > 120 else RED
    s = f"{T['cache']} {c}{countdown(left)}{RESET}"
    if hit is not None:
        s += f" {GRAY}({T['hit']} {hit * 100:.0f}%){RESET}"
    return s


def line_session(data: dict) -> str:
    m = data.get("model") or {}
    name = (m.get("display_name") or m.get("id") or "?").replace("Claude ", "")
    parts = [f"{BOLD}{name}{RESET}"]

    effort = (data.get("effort") or {}).get("level")
    if effort:
        parts[0] += f" {GRAY}{effort}{RESET}"
    if data.get("fast_mode"):
        parts[0] += f" {YELLOW}fast{RESET}"

    cw = data.get("context_window") or {}
    pct, size = cw.get("used_percentage"), cw.get("context_window_size")
    if pct is not None and size:
        parts.append(f"{T['ctx']} {bar(pct, 6)} {human_tokens(size * pct / 100)}/{human_tokens(size)}")

    cache = cache_part(data)
    if cache:
        parts.append(cache)
    return SEP.join(parts)


# ---------------------------------------------------------------- line 2

def line_quotas(data: dict) -> str:
    limits = data.get("rate_limits") or {}
    parts = []
    for key, label in (("five_hour", T["5h"]), ("seven_day", T["7d"]), ("spend_limit", T["spend"])):
        w = limits.get(key)
        if not w or w.get("used_percentage") is None:
            continue
        pct = float(w["used_percentage"])
        s = f"{label} {bar(pct)} {color_for(pct)}{pct:.0f}%{RESET}"
        if w.get("resets_at"):
            s += f" {GRAY}{T['reset']} {countdown(float(w['resets_at']) - time.time())}{RESET}"
        parts.append(s)
    return f" {GRAY}│{RESET} ".join(parts) or f"{GRAY}{T['no_quota']}{RESET}"


# ---------------------------------------------------------------- main

def main() -> int:
    if "--version" in sys.argv:
        print(VERSION)
        return 0
    raw = "" if sys.stdin.isatty() else sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {}
    for fn in (line_session, line_quotas):
        try:
            print(fn(data))
        except Exception as e:  # noqa: BLE001
            if os.environ.get("CLAUDE_STATUSLINE_DEBUG"):
                print(f"{fn.__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
