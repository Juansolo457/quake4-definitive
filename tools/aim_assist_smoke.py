"""Smoke test for the Xenon aim assist port in openQ4 (branch q4x360/aim-assist).

Loads a single player map, spawns a grunt in front of the crosshair, and reads
pm_joystickSlow (the SetSlowJoystick friction bridge) before the spawn, on target, and
with aim assist turned off.  Expected: 0, pm_AimAssistSlow (50), 0.  Spawned monsters
wander off within a second or two, so the on-target read happens 300 ms after the spawn.

    python -I tools/aim_assist_smoke.py <openQ4-client_x64.exe> "<Quake 4 install>" <work dir>
"""

import os
import re
import subprocess
import sys
from pathlib import Path

MAP = "game/airdefense1"

AFTER_LOAD = [
    "waitMsec 1500",
    "god",
    "notarget",
    "set pm_showAimAssist 1",
    "echo AIM_SMOKE_NONE",
    "pm_joystickSlow",
    "spawn monster_grunt",
    "waitMsec 300",
    "echo AIM_SMOKE_ON",
    "pm_joystickSlow",
    "screenshot",
    "set pm_AimAssist 0",
    "waitMsec 200",
    "echo AIM_SMOKE_OFF",
    "pm_joystickSlow",
    "quit",
]


def read_slow(log, marker):
    after = log.split(marker, 1)[1] if marker in log else ""
    match = re.search(r'"pm_joystickSlow" is:"(-?\d+)', after)
    return int(match.group(1)) if match else None


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    exe = Path(sys.argv[1]).resolve(strict=True)
    retail = Path(sys.argv[2]).resolve(strict=True)
    work = Path(sys.argv[3]).resolve()
    game_dir = work / "baseoq4"
    game_dir.mkdir(parents=True, exist_ok=True)
    (game_dir / "aim_assist_smoke.cfg").write_text("\n".join(AFTER_LOAD) + "\n", encoding="ascii")
    log_path = game_dir / "logs" / "aim_assist_smoke.log"
    if log_path.exists():
        log_path.unlink()

    settings = {
        "win_allowMultipleInstances": "1", "r_fullscreen": "0", "r_fullscreenDesktop": "0",
        "r_borderless": "0", "r_borderlessDefaultMigrated": "1", "r_mode": "-1",
        "r_customWidth": "1280", "r_customHeight": "720", "s_noSound": "1",
        "logFile": "2", "logFileName": "logs/aim_assist_smoke.log", "in_mouse": "0",
        "developer": "1", "com_skipLoadingContinue": "1", "g_autoSkipCinematics": "1",
        "fs_basepath": str(retail), "fs_savepath": str(work), "fs_cachepath": str(work / "cache"),
        "si_gameType": "singleplayer", "pm_AimAssist": "2",
        "g_autoExecAfterMapLoad": "aim_assist_smoke.cfg", "g_autoExecAfterMapLoadDelayMs": "500",
    }
    command = [str(exe)]
    for key, value in settings.items():
        command += ["+set", key, value]
    command += ["+map", MAP]

    process = subprocess.run(command, cwd=exe.parent, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
    log = log_path.read_text(encoding="latin1") if log_path.exists() else ""
    none = read_slow(log, "AIM_SMOKE_NONE")
    on = read_slow(log, "AIM_SMOKE_ON")
    off = read_slow(log, "AIM_SMOKE_OFF")
    shots = sorted((game_dir / "screenshots").glob("*"), key=os.path.getmtime) if (game_dir / "screenshots").exists() else []
    print(f"exit={process.returncode} no_target_slow={none} on_target_slow={on} assist_off_slow={off}")
    print(f"log={log_path}")
    if shots:
        print(f"screenshot={shots[-1]}")
    ok = none == 0 and on == 50 and off == 0
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
