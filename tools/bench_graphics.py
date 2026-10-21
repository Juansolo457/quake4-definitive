"""Benchmark candidate graphics configurations in openQ4 at native resolution.

Each run launches openQ4 visibly (borderless desktop fullscreen, vsync off, 1000 fps
cap), loads a map, settles, then performs openQ4's reproducible 360 degree
benchmarkViewSweep while framePacingReset / framePacingSnapshot measure it, and
takes a screenshot.  openQ4's own renderer_gameplay_benchmark.py starts its windows
hidden, which openQ4 caps at 60 fps on Windows, so it can't measure high frame rates.

    python -P tools/bench_graphics.py <openQ4 exe> "<Quake 4 install>" <work dir> [config ...]
"""

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

MAPS = ["game/airdefense1", "game/storage2"]

COMMON = {
    "r_screenFraction": "100", "r_ssao": "0", "r_bloom": "0", "r_hdrToneMap": "0", "r_temporalAA": "2",
    "r_renderApi": "gl", "com_maxfps": "1000", "r_swapInterval": "0",
}
CONFIGS = {
    "balanced": {"r_multiSamples": "2", "r_postAA": "1", "image_anisotropy": "4", "r_useShadowMap": "0", "r_rendererBenchmarkPreset": "baseline"},
    "quality": {"r_multiSamples": "4", "r_postAA": "1", "image_anisotropy": "8", "r_useShadowMap": "1", "r_shadowMapSize": "1024", "r_rendererBenchmarkPreset": "modern"},
    "ultra": {"r_multiSamples": "8", "r_postAA": "1", "image_anisotropy": "16", "r_useShadowMap": "1", "r_shadowMapSize": "2048", "r_rendererBenchmarkPreset": "high-end"},
    "de": {"r_multiSamples": "4", "r_postAA": "1", "image_anisotropy": "16", "r_useShadowMap": "1", "r_shadowMapSize": "2048", "r_ssao": "1", "r_rendererBenchmarkPreset": "high-end"},
    "de-vk": {"r_renderApi": "vk", "r_multiSamples": "4", "r_postAA": "1", "image_anisotropy": "16", "r_useShadowMap": "1", "r_shadowMapSize": "2048", "r_ssao": "1", "r_rendererBenchmarkPreset": "high-end"},
    "de-taa": {"r_multiSamples": "0", "r_postAA": "0", "r_temporalAA": "1", "image_anisotropy": "16", "r_useShadowMap": "1", "r_shadowMapSize": "2048", "r_ssao": "1", "r_rendererBenchmarkPreset": "high-end"},
}

LAUNCH = {
    "win_allowMultipleInstances": "1", "r_fullscreen": "1", "r_fullscreenDesktop": "1", "r_mode": "-2",
    "s_noSound": "1", "in_joystick": "0", "in_mouse": "0", "com_skipLoadingContinue": "1",
    "g_autoSkipCinematics": "1", "logFile": "2", "g_autoExecAfterMapLoadDelayMs": "500",
}

BENCH_CFG = ["wait 360", "god", "notarget", "benchmarkViewSweep 360 12000", "framePacingReset",
             "waitMsec 13000", "framePacingSnapshot", "gfxInfo", "screenshot", "wait 5", "quit"]

SNAPSHOT = re.compile(r"Frame pacing snapshot \(SP\): bound=(\S+), samples=(\d+), present=([\d.]+) ms \(([\d.]+) Hz\), "
                      r"p50=(\d+) ms, p95=(\d+) ms, p99=(\d+) ms, max=(\d+) ms")


def run(exe, basepath, work, name, mapname):
    save = work / "save"                      # shared, so the image cache stays warm
    game = save / "baseoq4"
    (game / "logs").mkdir(parents=True, exist_ok=True)
    (game / "bench.cfg").write_text("\n".join(BENCH_CFG) + "\n", encoding="ascii")
    tag = f"{name}_{mapname.split('/')[-1]}"
    log = game / "logs" / f"{tag}.log"
    log.unlink(missing_ok=True)
    settings = dict(LAUNCH, **COMMON, **CONFIGS[name])
    settings.update({"fs_basepath": basepath, "fs_savepath": str(save), "logFileName": f"logs/{tag}.log",
                     "g_autoExecAfterMapLoad": "bench.cfg"})
    cmd = [str(exe)]
    for key, value in settings.items():
        cmd += ["+set", key, value]
    cmd += ["+map", mapname]
    started = time.monotonic()
    options = {}
    if sys.platform == "win32":
        # A parent started without a visible window passes that on; openQ4 caps
        # windows it thinks are hidden at 60 fps, so ask for a normal one.
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 1  # SW_SHOWNORMAL
        options["startupinfo"] = startup
    subprocess.run(cmd, cwd=exe.parent, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=600, **options)
    text = log.read_text(encoding="latin1") if log.exists() else ""
    m = SNAPSHOT.search(text)
    shots = sorted((game / "screenshots").glob("*.tga"), key=lambda p: p.stat().st_mtime) if (game / "screenshots").exists() else []
    if shots:
        dest = work / f"{tag}.tga"
        shutil.move(str(shots[-1]), dest)
    msaa = re.search(r"effective(?:MSAA)?[= ](\d+)", text)
    return {"config": name, "map": mapname, "seconds": round(time.monotonic() - started),
            "bound": m.group(1) if m else "-", "hz": float(m.group(4)) if m else None,
            "p50": m.group(5) if m else "-", "p95": m.group(6) if m else "-", "p99": m.group(7) if m else "-",
            "max": m.group(8) if m else "-", "errors": len(re.findall(r"^\^?1?ERROR", text, re.M))}


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    exe, basepath, work = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
    names = sys.argv[4:] or list(CONFIGS)
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in names:
        for mapname in MAPS:
            row = run(exe, basepath, work, name, mapname)
            rows.append(row)
            print(row, flush=True)
    print("\n| config | map | avg fps | P50 ms | P95 ms | P99 ms | worst ms | bound |")
    print("|---|---|---:|---:|---:|---:|---:|---|")
    for r in rows:
        print(f"| {r['config']} | {r['map'].split('/')[-1]} | {r['hz']} | {r['p50']} | {r['p95']} | {r['p99']} | {r['max']} | {r['bound']} |")


if __name__ == "__main__":
    main()
