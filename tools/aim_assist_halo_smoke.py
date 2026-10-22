"""Smoke test for the Halo-style Full (Wide) aim assist (pm_AimAssist 3) in openQ4.

Two runs of game/airdefense1. The first reads the player's start. The second freezes the AI,
spawns a grunt DISTANCE units ahead and, for each tuned weapon, turns the view a set number of
degrees off it and runs testMuzzleAim, which prints the autoaim and magnetism levels, the
adhesion and friction sent to the engine, and how far a shot would bend. It also checks the
machinegun zoomed (the cones shrink), a strafe (adhesion follows the target), an untuned weapon
in mode 3 (the wide 360 joint bend) and the machinegun in mode 2 (the 360 bend, unchanged).

    python -I tools/aim_assist_halo_smoke.py <openQ4-client_x64.exe> "<Quake 4 install>" <work dir> [distance]
"""

import math
import re
import subprocess
import sys
from pathlib import Path

MAP = "game/airdefense1"
DISTANCE = 280.0       # in front of the wall ahead of the start
VIEW_HEIGHT = 68.0
OFFSETS = [0, 3, 6, 9, 12, 15, 18, 24]
ZOOM_OFFSETS = [0, 6, 9, 12]
TUNED = ["weapon_machinegun", "weapon_blaster", "weapon_shotgun"]


def run(exe, retail, work, name, commands):
    game_dir = work / "baseoq4"
    game_dir.mkdir(parents=True, exist_ok=True)
    (game_dir / f"{name}.cfg").write_text("\n".join(commands) + "\n", encoding="ascii")
    log_path = game_dir / "logs" / f"{name}.log"
    if log_path.exists():
        log_path.unlink()
    settings = {
        "win_allowMultipleInstances": "1", "r_fullscreen": "0", "r_fullscreenDesktop": "0",
        "r_borderless": "0", "r_borderlessDefaultMigrated": "1", "r_mode": "-1",
        "r_customWidth": "1280", "r_customHeight": "720", "s_noSound": "1",
        "logFile": "2", "logFileName": f"logs/{name}.log", "in_mouse": "0",
        "in_joystick": "0", "r_hiddenWindow": "1", "g_fov": "90",
        "developer": "1", "com_skipLoadingContinue": "1", "g_autoSkipCinematics": "1",
        "fs_basepath": str(retail), "fs_savepath": str(work), "fs_cachepath": str(work / "cache"),
        "si_gameType": "singleplayer", "pm_AimAssist": "3",
        "g_autoExecAfterMapLoad": f"{name}.cfg", "g_autoExecAfterMapLoadDelayMs": "500",
    }
    command = [str(exe)]
    for key, value in settings.items():
        command += ["+set", key, value]
    command += ["+map", MAP]
    process = subprocess.run(command, cwd=exe.parent, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    log = log_path.read_text(encoding="latin1") if log_path.exists() else ""
    return process.returncode, log, log_path


def cases(log):
    """Each HALO_CASE marker with the testMuzzleAim lines after it."""
    found = {}
    for block in log.split("HALO_CASE ")[1:]:
        label, _, rest = block.partition("\n")
        text = rest.split("HALO_CASE", 1)[0]
        found[label.strip()] = text
    return found


def number(pattern, text):
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


def main():
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    distance = float(sys.argv[4]) if len(sys.argv) == 5 else DISTANCE
    exe = Path(sys.argv[1]).resolve(strict=True)
    retail = Path(sys.argv[2]).resolve(strict=True)
    work = Path(sys.argv[3]).resolve()

    code, log, log_path = run(exe, retail, work, "halo_start", ["waitMsec 1500", "echo HALO_START", "getviewpos", "quit"])
    match = re.search(r"HALO_START.*?\((-?[\d.]+) (-?[\d.]+) (-?[\d.]+)\) (-?[\d.]+)", log, re.S)
    if not match:
        print(f"FAIL: no start position (exit {code}, log {log_path})")
        return 1
    x, y, z, yaw = (float(v) for v in match.groups())
    gx = x + distance * math.cos(math.radians(yaw))
    gy = y + distance * math.sin(math.radians(yaw))
    gz = z - VIEW_HEIGHT + 1.0
    eye = f"{x:.1f} {y:.1f} {z:.1f}"

    commands = ["waitMsec 1500", "god", "notarget", "give all", "set ai_freeze 1", "set pm_AimAssistAnyInput 1",
                "set pm_showAimAssist 1",
                f'spawn monster_grunt origin "{gx:.1f} {gy:.1f} {gz:.1f}" angle "{yaw + 180:.1f}" name halo_grunt',
                "waitMsec 500", f"setviewpos {eye} {yaw:.2f}", "waitMsec 200", "screenshot"]

    def check(label, offset, extra=()):
        commands.extend([f"setviewpos {eye} {yaw + offset:.2f}", *extra, "waitMsec 150", f"echo HALO_CASE {label}", "testMuzzleAim"])

    for weapon in TUNED:
        commands.extend([f"testWeaponScope {weapon}", "waitMsec 1500"])
        for offset in OFFSETS:
            check(f"{weapon} {offset}", offset)
    commands.extend(["testWeaponScope weapon_machinegun", "waitMsec 1500", "openq4_testInput 4000 zoom", "waitMsec 800"])
    for offset in ZOOM_OFFSETS:
        check(f"weapon_machinegun zoomed {offset}", offset)
    commands.extend(["openq4_testInput 0", "waitMsec 800"])
    # still strafing when measured: the grunt slides across the view
    check("weapon_machinegun strafe", 0, ["openq4_testInput 600 right 127", "waitMsec 250"])
    # the friction lets go over about pm_AimAssistFrictionRelease (0.15 s) after the aim leaves the
    # target: still partly held 50 ms later, gone 400 ms later
    commands.extend(["openq4_testInput 0", "waitMsec 500", f"setviewpos {eye} {yaw:.2f}", "waitMsec 300",
                     f"setviewpos {eye} {yaw + OFFSETS[-1]:.2f}", "waitMsec 50", "echo HALO_CASE release early", "testMuzzleAim",
                     "waitMsec 350", "echo HALO_CASE release late", "testMuzzleAim"])
    commands.extend(["testWeaponScope weapon_hyperblaster", "waitMsec 1500"])
    check("weapon_hyperblaster 9", 9)
    commands.extend(["testWeaponScope weapon_machinegun", "waitMsec 1500", "set pm_AimAssist 2"])
    check("mode2 weapon_machinegun 9", 9)
    commands.append("quit")

    code, log, log_path = run(exe, retail, work, "halo_aim", commands)
    found = cases(log)
    print(f"exit={code} start=({eye}) yaw={yaw:.1f} grunt={distance:.0f} ahead, log={log_path}")
    print(f"{'case':34} {'autoaim':>7} {'magnet':>7} {'keeps%':>6} {'adh yaw':>7} {'bent':>6}  notes")
    rows = {}
    for label, text in found.items():
        autoaim = number(r"autoaim level ([\d.]+), magnetism", text)
        magnetism = number(r"magnetism level ([\d.]+)", text)
        keeps = number(r"friction keeps (\d+)%", text)
        adhesion = number(r"adhesion (-?[\d.]+) ", text)
        bent = number(r"shot turned ([\d.]+) degrees", text)
        note = ""
        for pattern in (r"\(Halo\): (crosshair on [^\n]*)", r"\(Halo\): (shot not bent, [^\n]*)", r"muzzle aim: (\S+ joint [^\n]*)",
                        r"muzzle aim: (shot not bent, [^\n]*)", r"muzzle aim: (crosshair on [^\n]*)"):
            m = re.search(pattern, text)
            if m:
                note = m.group(1)
                break
        rows[label] = (autoaim, magnetism, keeps, adhesion, bent)
        fmt = lambda v, f: (f % v) if v is not None else "-"
        print(f"{label:34} {fmt(autoaim, '%.2f'):>7} {fmt(magnetism, '%.2f'):>7} {fmt(keeps, '%.0f'):>6} "
              f"{fmt(adhesion, '%.1f'):>7} {fmt(bent, '%.2f'):>6}  {note}")

    problems = []
    expected_cases = len(TUNED) * len(OFFSETS) + len(ZOOM_OFFSETS) + 1 + 2 + 1 + 1
    if len(rows) != expected_cases:
        problems.append(f"{len(rows)} of {expected_cases} cases ran")
    for weapon in TUNED:
        levels = [rows.get(f"{weapon} {o}", (None,) * 5) for o in OFFSETS]
        if any(level[0] is None for level in levels):
            problems.append(f"{weapon}: no Halo levels")
            continue
        autoaim = [level[0] for level in levels]
        magnetism = [level[1] for level in levels]
        if autoaim[0] != 1.0 or magnetism[0] != 1.0:
            problems.append(f"{weapon}: not full strength on the target")
        if any(b > a + 1e-6 for a, b in zip(autoaim, autoaim[1:])) or any(b > a + 1e-6 for a, b in zip(magnetism, magnetism[1:])):
            problems.append(f"{weapon}: levels do not fall off with the angle")
        if autoaim[-1] != 0.0 or magnetism[-1] != 0.0:
            problems.append(f"{weapon}: still assisted {OFFSETS[-1]} degrees off")
        if not any(0.0 < a < 1.0 for a in autoaim + magnetism):
            problems.append(f"{weapon}: no partial (falloff) level seen")
    # zoomed, the cones shrink by the magnification: never more assist, and less somewhere
    pairs = [(rows.get(f"weapon_machinegun zoomed {o}"), rows.get(f"weapon_machinegun {o}")) for o in ZOOM_OFFSETS]
    sums = [(z[0] + z[1], u[0] + u[1]) for z, u in pairs if z and u and None not in z[:2] and None not in u[:2]]
    if len(sums) != len(ZOOM_OFFSETS) or any(z > u + 1e-6 for z, u in sums) or not any(z < u - 1e-6 for z, u in sums):
        problems.append("machinegun zoomed: cones did not shrink")
    strafe = rows.get("weapon_machinegun strafe")
    if not strafe or not strafe[3] or abs(strafe[3]) < 1.0:
        problems.append("strafe: no adhesion")
    early, late = rows.get("release early"), rows.get("release late")
    if not early or not late or early[2] is None or late[2] is None or not 40 < early[2] < 100 or late[2] < 99:
        problems.append("friction release: not eased (partly held at 50 ms, gone at 400 ms)")
    if "joint" not in found.get("weapon_hyperblaster 9", ""):
        problems.append("hyperblaster in mode 3: no 360 joint bend")
    if "joint" not in found.get("mode2 weapon_machinegun 9", "") or "(Halo)" in found.get("mode2 weapon_machinegun 9", ""):
        problems.append("machinegun in mode 2: not the 360 joint bend")
    for problem in problems:
        print("problem:", problem)
    print("PASS" if not problems else "FAIL")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
