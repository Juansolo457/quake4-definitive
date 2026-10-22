# Quake 4 Definitive Edition

PC Quake 4. Xbox 360 controller feel. Modern settings. Native, sharp, fast.

> Unofficial. **No game data included.** Bring your own Quake 4 for PC (Steam or GOG).

## Why

Nostalgia. I played Quake 4 on the 360 and always wanted this mod: the PC version, but aiming like the 360. Tools like Claude Code finally make that doable for one person.

I'll keep tuning it until it feels right. **The controller tuning is human-tested.** I play every change and decide what feels right. Claude does the digging and the code; it doesn't get the final say on feel.

## What it is

Not a recompilation. Not a full decompilation.

- **Base:** [openQ4](https://github.com/themuffinator/openQ4), the open-source Quake 4 engine. It runs the PC game natively.
- **Added:** the 360's stick handling, reverse-engineered from the 360 executable and re-written as openQ4 patches.
- **Why not recompile:** the PC version is the same game, and the 360 textures were *lower* resolution. Only the controls were worth taking.
- The sister project, F.E.A.R. 360, will be a full static recompilation.

## Status

| | |
|---|---|
| ✅ 360 controller feel: square stick gate, XInput dead zones (7849 / 8689), 3-step look curve, smoothing, 360 turn speeds, 30% zoomed speed | patch 0003 · tuning ongoing |
| ✅ 360 aim assist (target cone + 50% friction) | patch 0001 |
| ✅ 360 bullet bend: shots aim at the enemy body part nearest the crosshair (controller only), plus a Wide mode | patches 0009–0011 |
| ✅ Real controller found among virtual pads (ViGEm, Steam) | patch 0002 |
| ✅ Settings menu rows for all of the above, plus Field of View and button prompt style | patches 0004–0005 |
| ✅ Settings pages fully usable with a controller (focus outline, LB/RB tabs, LT/RT scroll); help line explains each option | patches 0006–0007, 0013 |
| ✅ Performance trace: frame times plus Windows GPU %/VRAM per level (`-PerfTrace`) | patch 0008 |
| ✅ Graphics defaults: 4K, 240 fps cap, 4× MSAA + SMAA, 16× AF, soft shadows, 360 gamma/brightness | `config/definitive.cfg` |
| ✅ Uncompressed textures, hi-res packs load | `image_usePrecompressedTextures 2` |
| ⏳ 360 in-world screen prompts, Legacy stick layouts, button presets | next |
| ⏳ Vehicle aim assist | more reverse engineering |
| ⏳ Linux | untested |

Full debrief: [docs/PROGRESS.md](docs/PROGRESS.md).

## Install (Windows)

```powershell
git clone https://github.com/themuffinator/openQ4 reference/openQ4
cd reference/openQ4
git checkout cbe967f
git am ../../patches/openq4/*.patch
```
Build with openQ4's `BUILDING.md` (Meson + Ninja + Visual Studio). Gotchas: [docs/PC_BASELINE.md](docs/PC_BASELINE.md).

```powershell
pwsh tools/launch_definitive.ps1    # first launch applies the definitive defaults
```
Add `-PerfTrace` to record a performance trace, then `python -I tools/perf_report.py` ([GRAPHICS.md](docs/GRAPHICS.md#gpu-usage-and-the-performance-trace)).

## Settings

**Settings > Game Options > Controller:**

| Row | Cvar |
|---|---|
| 360 Controller Feel | `in_joystickXenon` |
| Aim Assist | `pm_AimAssist`: No / Slowdown Only / Full (360, adds bullet bend) / Full (Wide, default: bigger cone) |
| Aim Assist Friction | `pm_AimAssistSlow` (lower = stickier) |
| 360 Horizontal / Vertical Speed | `in_xenonYawScale` / `in_xenonPitchScale` (360 range 0.006–0.06) |
| 360 Zoomed Speed | `in_xenonZoomedSlow` |
| Button Prompts | `in_promptStyle` |

Console only: `in_xenonLookCurve 0/1` and `in_xenonSmoothing 0/1`, for comparing.

## How the 360 controls were recovered

All of this runs on **your own** 360 copy. Outputs stay local (`game/` is gitignored).

1. **Dump** your disc ([docs/RIPPING.md](docs/RIPPING.md)) to get `default.xex`.
2. **Read the headers:** `tools/xex_info.py` shows it's AES-encrypted, LZX-compressed, XDK 2.0.2099, and imports only `xam`/`xboxkrnl`.
3. **Unpack:** `tools/xexdump` uses XenonRecomp's loader to write the decrypted image (base `0x82000000`), its sections and its import thunks.
4. **Recover the cvars:** static `idCVar` objects sit in `.data` (vtable `0x8205FF18`, then name/default/description/flags). `tools/x360_cvars.py` reads all **813** of them. Finds: `m_yaw` 0.0253 and `m_pitch` 0.0209 are "stick scale", `pm_zoomedSlow` 30, vehicle aim assist.
5. **Find the input code:** `XamInputGetState` import ← `XInputGetState` wrapper (`0x82854560`) ← pad poll loop (`0x822B6180`).
6. **Disassemble** with `tools/ppc_func.py`, which resolves constants:
   - `0x822B6030`: circle → square. Stick length ÷ larger axis, clamp ±32767.
   - `0x822B5F68`: **dead zone**. `li r11,0x1EA9` (7849, left stick) / `0x21F1` (8689, right). Each axis on its own, then `(v − dz) / (32767 − dz) × 127`.
   - `0x822B63F0`: triggers. `cmplwi r8,0x40`, so pressed above 64/255.
7. **Find the look code:** trace reads of the `m_yaw` cvar to `JoystickMove` (`0x821C9AA8`):
   - curve (`0x821C9A08`): ×0.3 below 25%, ×0.6 to 75%, ×2.5 above
   - smoothing: `(previous + new) × 0.5`
   - turning: `m_yaw × 127` per 60 Hz tic, about 193°/s at full stick
8. **Port** it to openQ4 C++ behind a cvar (patch 0003), then add menu rows (patch 0004).
9. **Test:** an automated smoke test for aim assist (`tools/aim_assist_smoke.py`), then **human play-testing** for feel.

Addresses and details: [docs/X360_CONTROLS.md](docs/X360_CONTROLS.md).

## Hi-res textures (optional)

The stock textures are 256–512 px. openQ4 normally draws the compressed copies, and those block loose hi-res packs from loading. The definitive config sets `image_usePrecompressedTextures 2` to fix both. Recommended pack: *Quake 4: HiRes Textures & Models* (wachhabender, ModDB). Extract it into `Quake 4\baseoq4\`. Details: [docs/GRAPHICS.md](docs/GRAPHICS.md).

## Layout

```
patches/openq4/   openQ4 patches (git am, in order)
config/           definitive.cfg
docs/             findings, plan, progress
tools/            launcher, XEX tools, settings row/help tools, perf trace tools, tests
```

## Legal

- No assets, executables or proprietary code are distributed.
- The patches follow openQ4's licences: GPLv3 for the engine, the Quake 4 SDK EULA for `src/game` and `src/mpgame`.
- Our tools, docs and config are MIT ([LICENSE](LICENSE), [NOTICE](NOTICE)).
- Quake 4 is a trademark of ZeniMax Media / id Software. Not affiliated with id, Raven, Bethesda, ZeniMax, Activision or Microsoft.

## Credits

- id Software and Raven Software: Quake 4, the Doom 3 GPL source, the Quake 4 SDK
- themuffinator and DarkMatter Productions: [openQ4](https://github.com/themuffinator/openQ4)
- hedge-dev: [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) (XEX loader)
- Inspiration: [UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp), [Lost Odyssey Recomp](https://github.com/freefrank/LostOdysseyRecomp), [OpenCE](https://github.com/OpenCommunityEdition/OpenCE)
- wachhabender: *Quake 4: HiRes Textures & Models*
- Built with [Claude Code](https://claude.com/claude-code). Tuned by a human.
