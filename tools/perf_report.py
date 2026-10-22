"""Summarize a performance trace: openQ4's com_perfTrace CSV joined with perf_sampler.ps1's GPU counters.

    python -I tools/perf_report.py [perftrace folder | trace.csv [gpu.csv]]

With a folder (default: the launcher profile's baseoq4/perftrace), the newest trace_*.csv
and gpu_*.csv are used. Each GPU sample is matched to the trace interval that covers it, so
GPU usage can be read per level and per screen (game or a menu). Prints per-level averages,
the highest GPU samples, the longest frames and the level loads.
"""
import bisect
import csv
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "reference/openQ4/.home/baseoq4/perftrace"


def newest(folder, pattern):
    files = sorted(folder.glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def main():
    args = [Path(a) for a in sys.argv[1:]]
    if args and not args[0].exists():
        sys.exit(f"not found: {args[0]}")
    if not args or args[0].is_dir():
        folder = args[0] if args else DEFAULT_DIR
        trace_path, gpu_path = newest(folder, "trace_*.csv"), newest(folder, "gpu_*.csv")
    else:
        trace_path, gpu_path = args[0], (args[1] if len(args) > 1 else None)
    if trace_path is None:
        sys.exit(f"no trace_*.csv found ({__doc__.splitlines()[2].strip()})")
    trace = load(trace_path)
    intervals = [r for r in trace if r["kind"] == "interval"]
    gpu = load(gpu_path) if gpu_path else []
    print(f"trace {trace_path}" + (f"\ngpu   {gpu_path}" if gpu_path else "\ngpu   (none: run with launch_definitive.ps1 -PerfTrace)"))

    # Rows are written at the end of what they cover: an interval its frames, a map
    # row the load. GPU samples outside every row (before the trace opened) are dropped.
    spans = []
    for row in trace:
        end = num(row["unix_time"])
        if row["kind"] == "interval":
            spans.append((end - num(row["frames"]) / max(num(row["fps"]), 0.001), end, row))
        elif row["kind"] == "map":
            spans.append((end - num(row["frame_ms_max"]) / 1000.0, end, dict(row, screen="loading")))
    spans.sort(key=lambda s: s[1])
    ends = [s[1] for s in spans]

    def interval_at(t):
        i = bisect.bisect_left(ends, t)
        if i < len(spans) and spans[i][0] <= t:
            return spans[i][2]
        return None

    levels = defaultdict(lambda: {"seconds": 0.0, "frames": 0, "gpu": [], "vram": 0.0, "hitches": 0, "worst": 0.0})
    for row in intervals:
        level = levels[(row["map"], row["screen"])]
        span = num(row["frames"]) / max(num(row["fps"]), 0.001)
        level["seconds"] += span
        level["frames"] += int(num(row["frames"]))
        level["hitches"] += int(num(row["hitches"]))
        level["worst"] = max(level["worst"], num(row["frame_ms_max"]))
    for row in trace:
        if row["kind"] == "map":
            levels[(row["map"], "loading")]["seconds"] += num(row["frame_ms_max"]) / 1000.0
    matched = []
    for sample in gpu:
        row = interval_at(num(sample["unix_time"]))
        if row is None:
            continue
        level = levels[(row["map"], row["screen"])]
        level["gpu"].append(num(sample["game_3d_pct"]))
        level["vram"] = max(level["vram"], num(sample["game_vram_mb"]))
        matched.append((sample, row))

    print("\nper level and screen")
    print(f"  {'map':34} {'screen':22} {'time':>7} {'fps':>6} {'gpu avg':>8} {'gpu max':>8} {'vram MB':>8} {'hitches':>8} {'worst ms':>9}")
    for (map_name, screen), v in sorted(levels.items(), key=lambda kv: -kv[1]["seconds"]):
        fps = v["frames"] / v["seconds"] if v["seconds"] else 0.0
        g = v["gpu"]
        avg = f"{sum(g) / len(g):.0f}%" if g else "-"
        top = f"{max(g):.0f}%" if g else "-"
        vram = f"{v['vram']:.0f}" if g else "-"
        print(f"  {map_name[:34]:34} {screen[:22]:22} {v['seconds']:6.0f}s {fps:6.0f} {avg:>8} {top:>8} {vram:>8} {v['hitches']:8d} {v['worst']:9.0f}")

    if matched:
        print("\nhighest GPU samples")
        for sample, row in sorted(matched, key=lambda m: -num(m[0]["game_3d_pct"]))[:10]:
            print(f"  t={num(row['time_s']):7.0f}s gpu {num(sample['game_3d_pct']):5.1f}% (adapter {num(sample['adapter_3d_pct']):5.1f}%) "
                  f"vram {num(sample['game_vram_mb']):6.0f} MB fps {num(row['fps']):6.0f} frame max {num(row['frame_ms_max']):6.1f} ms  {row['map']} [{row['screen']}]")

    hitches = sorted((r for r in trace if r["kind"] == "hitch"), key=lambda r: -num(r["frame_ms_max"]))
    if hitches:
        print(f"\nlongest frames ({len(hitches)} at or over the hitch threshold)")
        for r in hitches[:10]:
            print(f"  t={num(r['time_s']):7.1f}s {num(r['frame_ms_max']):7.1f} ms  game {num(r['game_ms_avg']):5.1f} fe {num(r['frontend_ms_avg']):4.0f} "
                  f"be {num(r['backend_ms_avg']):4.0f}  {r['map']} [{r['screen']}]")

    loads = [r for r in trace if r["kind"] == "map"]
    if loads:
        print("\nlevel loads")
        for r in loads:
            print(f"  t={num(r['time_s']):7.1f}s {num(r['frame_ms_max']) / 1000.0:6.1f} s  {r['map']}")


if __name__ == "__main__":
    main()
