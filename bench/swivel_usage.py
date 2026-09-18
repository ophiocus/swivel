"""Measure what swivel costs and does inside real Claude Code sessions.

Reads every session transcript (*.jsonl) under a Claude Code projects directory
that loaded the swivel skill, and reports per session:

  - API calls, compactions, context size before/after swivel loaded
  - swivel file reads/writes and their token footprint
  - "carried" tokens: each .swivel read/write re-sent on every later call
    until the next compaction
  - how many compactions were followed by a .swivel read (lane reload)

Usage:
  python swivel_usage.py [--root ~/.claude/projects] [--exclude SESSION_ID]
"""
import argparse
import glob
import json
import os
import statistics as st

MARK = "Launching skill: swivel"


def text_of(content):
    if isinstance(content, str):
        return content
    out = []
    for b in content or []:
        if isinstance(b, dict):
            if b.get("type") == "text":
                out.append(b.get("text", ""))
            elif b.get("type") == "tool_result":
                out.append(text_of(b.get("content")))
    return "\n".join(out)


def analyse(path):
    seq = 0
    seen = set()
    ctx = []
    compact_at = []
    swivel_at = None
    events = []
    pending = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            t = r.get("type")
            if t == "system" and r.get("subtype") == "compact_boundary":
                compact_at.append(seq)
            msg = r.get("message") or {}
            if t == "assistant":
                mid, u = msg.get("id"), msg.get("usage")
                if mid and u and mid not in seen:
                    seen.add(mid)
                    seq += 1
                    ctx.append((seq, u.get("input_tokens", 0)
                                + u.get("cache_creation_input_tokens", 0)
                                + u.get("cache_read_input_tokens", 0)))
                for b in msg.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        s = json.dumps(b.get("input", {}))
                        if ".swivel" in s:
                            kind = "write" if b.get("name") in ("Write", "Edit") else "read"
                            pending[b.get("id")] = [seq, len(s), kind]
            elif t == "user":
                c = msg.get("content")
                if swivel_at is None and MARK in text_of(c):
                    swivel_at = seq
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
                            p = pending.pop(b.get("tool_use_id"))
                            p[1] += len(text_of(b.get("content")))
                            events.append(tuple(p))
    return ctx, compact_at, swivel_at, events, seq


def summarise(path):
    ctx, compact_at, swivel_at, events, end = analyse(path)
    if not ctx:
        return None
    total = sum(c for _, c in ctx)
    before = [c for s, c in ctx if swivel_at is not None and s <= swivel_at]
    after = [c for s, c in ctx if swivel_at is not None and s > swivel_at]
    direct = carried = 0
    for s, chars, _ in events:
        tok = chars // 4
        direct += tok
        nxt = next((c for c in compact_at if c >= s), end)
        carried += tok * max(nxt - s, 0)
    reloads = sum(1 for c in compact_at
                  if any(k == "read" and c < s <= c + 8 for s, _, k in events))
    return {
        "session": os.path.basename(path)[:8],
        "calls": end,
        "compactions": len(compact_at),
        "reloads_after_compaction": reloads,
        "peak_ctx": max(c for _, c in ctx),
        "median_ctx_before": int(st.median(before)) if before else "",
        "median_ctx_after": int(st.median(after)) if after else "",
        "swivel_reads": sum(1 for e in events if e[2] == "read"),
        "swivel_writes": sum(1 for e in events if e[2] == "write"),
        "direct_tok": direct,
        "carried_tok": carried,
        "input_tok": total,
        "carried_pct": round(100 * carried / total, 2) if total else 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--exclude", action="append", default=[],
                    help="session id to skip (e.g. the session running this)")
    args = ap.parse_args()

    rows = []
    for p in glob.glob(os.path.join(args.root, "*", "*.jsonl")):
        if any(x in p for x in args.exclude):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            if MARK not in fh.read():
                continue
        s = summarise(p)
        if s:
            rows.append(s)
    if not rows:
        print("no sessions loaded swivel under", args.root)
        return
    rows.sort(key=lambda r: -r["input_tok"])
    cols = list(rows[0])
    print("\t".join(cols))
    for r in rows:
        print("\t".join(str(r[c]) for c in cols))

    tin = sum(r["input_tok"] for r in rows)
    tcar = sum(r["carried_tok"] for r in rows)
    tcomp = sum(r["compactions"] for r in rows)
    trel = sum(r["reloads_after_compaction"] for r in rows)
    up = sum(1 for r in rows if r["median_ctx_before"] != "" and r["median_ctx_after"] != ""
             and r["median_ctx_after"] > r["median_ctx_before"])
    print(f"\nsessions={len(rows)} input={tin} carried={tcar} ({100 * tcar / tin:.2f}%) "
          f"compactions={tcomp} reloads={trel} median_ctx_rose={up}/{len(rows)}")


if __name__ == "__main__":
    main()
