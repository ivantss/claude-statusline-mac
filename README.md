# claude-statusline

A two-line status bar for [Claude Code](https://code.claude.com): model, context, **prompt-cache countdown**, and **time left on each quota**.

```
Opus 5.5 (1M context) high · ctx █░░░░░ 84k/1M · cache 41 min (hit 91%)
5h ██░░░░░░ 24% resets in 2h13 │ week ███████░ 86% resets in 2d07h
```

- **Model** and effort level (and `fast` when fast mode is on).
- **Context** used / context window.
- **Cache**: minutes before the prompt cache expires. After that, your next message re-reads the whole context at full price. Turns yellow then red as it gets close.
- **Quotas** (Pro / Max): 5-hour and weekly usage, with the time left before each reset. Green < 50 %, yellow < 80 %, red above.

## Why it matters

### The cache timer saves you tokens

Every message you send makes Claude re-read the **whole conversation**: files read, tool results, everything. The prompt cache makes this cheap: a cached token is billed at **10 %** of the normal input price.

But the cache expires. After **1 hour** without a message (5 minutes on some accounts), it is gone. Your next message, even a one-word "ok", re-processes the entire context and writes it back to the cache at **1.25× to 2×** the normal price.

Example with a 400k-token conversation:

| Next message | Cost in input tokens |
|---|---|
| Cache still warm | ≈ 40k (400k × 0.1) |
| Cache expired (1 h cache) | ≈ 800k (400k × 2) |

That is **20× more** for the same message. On a Pro / Max plan, this comes out of your quota. On the API, out of your bill. Claude Code does not tell you when it happens. This bar does.

### How to use it

- **Watch the countdown when you step away.** Yellow = less than a quarter of the time left. Red = a couple of minutes.
- **Coming back to the same task?** Send your next message before it hits zero. The cache is renewed with each message.
- **Task finished?** Run `/clear` instead of continuing. A fresh session costs almost nothing. An expired 500k one costs a full re-read.
- **Big context and a long break ahead?** Run `/compact` first, or accept the re-read, but choose it.
- **"cache expired" in red** = your next message is the expensive one. If it's a new topic, `/clear` first.

### The quotas tell you when to push and when to wait

Pro and Max plans have two limits: a rolling **5-hour** window and a **weekly** one. Claude Code only warns you when you're close to the wall.

- **5h bar**: how much of the current window is used, and when it resets. At 85 % with 20 min left, wait for the reset before starting a big task.
- **Week bar**: the one that really stops you. At 70 % on day 3 of 7, slow down or use a lighter model. At 30 % the day before the reset, you have room for heavy work.
- Colors: green < 50 %, yellow < 80 %, red above.

## Install

One line (macOS / Linux, needs `python3`):

```sh
curl -fsSL https://raw.githubusercontent.com/ivantss/claude-statusline/main/install.sh | bash
```

Then restart Claude Code.

The installer copies `statusline.py` to `~/.claude/claude-statusline/` and sets `statusLine` in `~/.claude/settings.json` (backup saved as `settings.json.bak-statusline`; your previous status line is kept and restored on uninstall).

## Uninstall

```sh
curl -fsSL https://raw.githubusercontent.com/ivantss/claude-statusline/main/install.sh | bash -s -- --uninstall
```

## Options (environment variables)

| Variable | Effect |
|---|---|
| `CLAUDE_STATUSLINE_LANG=fr` | French labels (default: from `$LANG`, English otherwise) |
| `NO_COLOR=1` | No colors |
| `CLAUDE_STATUSLINE_CACHE_TTL=300` | Cache lifetime in seconds, only used by old Claude Code versions when it can't be detected |

## Privacy

Everything comes from the JSON Claude Code passes to the status line. No network call, no credentials read, standard library only (~180 lines — read it).

Cache and quota fields need Claude Code ≥ 2.1.251. On older versions the cache countdown is computed from the session transcript.

## License

MIT
