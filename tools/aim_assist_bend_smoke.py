"""Smoke test for the Xbox 360 muzzle aim ("bullet bend", pm_AimAssist 2) in openQ4.

Loads Air Defense 1 in a hidden window, levels the view, spawns a grunt ahead and reads
testMuzzleAim (prints how far a shot fired now would be turned). The cone is widened
(pm_AimAssistTest/FOV) and pm_AimAssistAnyInput stands in for a controller. Expected:
    off target      turned toward one of the grunt's joints
    mode 1          not turned (slowdown only)
    mouse           not turned (controller only)
    on target       not turned, after "testMuzzleAim aim" puts the crosshair on that joint

    python -I tools/aim_assist_bend_smoke.py <openQ4-client_x64.exe> "<Quake 4 install>" <work dir>
"""

import re
import subprocess
import sys
from pathlib import Path

MAP = "game/airdefense1"
START = "10325 -6962 6.95 -105"   # the map's player start, view levelled

AFTER_LOAD = [
    "waitMsec 1500", "god", "notarget", "give weapon_machinegun", "waitMsec 1200",
    "set pm_showAimAssist 1", "set pm_AimAssistAnyInput 1", "set pm_AimAssistTest 1", "set pm_AimAssistFOV 100",
    f"setviewpos {START}", "waitMsec 200",
    "spawn monster_grunt", "waitMsec 300",
    "echo BEND_OFF_TARGET", "testMuzzleAim",
    "set pm_AimAssist 1", "echo BEND_MODE1", "testMuzzleAim", "set pm_AimAssist 2",
    "set pm_AimAssistAnyInput 0", "echo BEND_MOUSE", "testMuzzleAim", "set pm_AimAssistAnyInput 1",
    # same frame: the chosen joint may be a hand that moves on the next one
    "testMuzzleAim aim",
    "echo BEND_ON_TARGET", "testMuzzleAim",
    "quit",
]


def section(log, marker):
    after = log.split(marker, 1)[1] if marker in log else ""
    return after.split("BEND_", 1)[0]


def turned(text):
    match = re.search(r"shot turned (-?[\d.]+) degrees", text)
    return float(match.group(1)) if match else None


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    exe = Path(sys.argv[1]).resolve(strict=True)
    retail = Path(sys.argv[2]).resolve(strict=True)
    work = Path(sys.argv[3]).resolve()
    game_dir = work / "baseoq4"
    game_dir.mkdir(parents=True, exist_ok=True)
    (game_dir / "aim_assist_bend_smoke.cfg").write_text("\n".join(AFTER_LOAD) + "\n", encoding="ascii")
    log_path = game_dir / "logs" / "aim_assist_bend_smoke.log"
    if log_path.exists():
        log_path.unlink()

    settings = {
        "win_allowMultipleInstances": "1", "r_fullscreen": "0", "r_fullscreenDesktop": "0",
        "r_borderless": "0", "r_borderlessDefaultMigrated": "1", "r_mode": "-1",
        "r_customWidth": "1280", "r_customHeight": "720", "s_noSound": "1",
        "logFile": "2", "logFileName": "logs/aim_assist_bend_smoke.log", "in_mouse": "0",
        "in_joystick": "0", "r_hiddenWindow": "1",
        "developer": "1", "com_skipLoadingContinue": "1", "g_autoSkipCinematics": "1",
        "fs_basepath": str(retail), "fs_savepath": str(work), "fs_cachepath": str(work / "cache"),
        "si_gameType": "singleplayer", "pm_AimAssist": "2",
        "g_autoExecAfterMapLoad": "aim_assist_bend_smoke.cfg", "g_autoExecAfterMapLoadDelayMs": "500",
    }
    command = [str(exe)]
    for key, value in settings.items():
        command += ["+set", key, value]
    command += ["+map", MAP]

    process = subprocess.run(command, cwd=exe.parent, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
    log = log_path.read_text(encoding="latin1") if log_path.exists() else ""
    off, mode1, mouse, on = (section(log, m) for m in ("BEND_OFF_TARGET", "BEND_MODE1", "BEND_MOUSE", "BEND_ON_TARGET"))
    joint = re.search(r"muzzle aim: \S+ joint (\S+)", off)
    print(f"exit={process.returncode}")
    print(f"off target: turned {turned(off)} deg toward joint {joint.group(1) if joint else None}")
    print(f"mode 1: turned {turned(mode1)} deg; mouse: turned {turned(mouse)} deg")
    on_enemy = "muzzle aim: crosshair on" in on
    print(f"on target: turned {turned(on)} deg, crosshair on enemy: {on_enemy}")
    print(f"log={log_path}")
    ok = (turned(off) or 0) > 1.0 and joint is not None and \
        turned(mode1) is not None and turned(mode1) < 0.1 and \
        turned(mouse) is not None and turned(mouse) < 0.1 and \
        turned(on) is not None and turned(on) < 0.1 and on_enemy
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
