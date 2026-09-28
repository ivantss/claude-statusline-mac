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
