# Progress Debrief

_Last updated 2026-10-21._

## Where we are
The project started as a plan to statically recompile the Xbox 360 version of Quake 4. Early recon showed that wasn't needed for what matters most:
- openQ4 already runs the PC version natively, with modern rendering.
- Raven's Quake 4 SDK still contains the 360 **game** code (`#ifdef _XENON`), including the aim assist.
- The 360 **engine** differences that matter for feel (stick processing, look curve, speeds) are small, self-contained routines. They could be reverse-engineered from the 360 executable and re-implemented directly.
- The 360 textures were *downsized* compared with PC (`x360build.cfg`: 512 px cap), so PC assets look better.

So this became a **"definitive edition"**: openQ4 + PC assets + the 360 controller feel + modern controller and graphics options. The full recompilation approach moves to the F.E.A.R. 360 project, where there's no PC source port to build on.

**Biggest milestone so far: the 360 controller feel runs on PC.** That covers the 360's own dead zones, stick gate, look curve, smoothing, turn speeds and zoom slowdown, all recovered from the binary and selectable in the settings menu. Hands-on: "test was really good, about 8.5 out of 10… the feel is great". Remaining work is testing and tuning.

## What was done

### 1. Baseline
- Built openQ4 (VS 2022 / MSVC 19.44, Meson + Ninja) against the Steam install; worked through three Windows build gotchas ([PC_BASELINE.md](PC_BASELINE.md)).
- Inventoried the PC data: 40 paks, 32,702 files, no console or controller data at all.

### 2. Aim assist (patch 0001)
- Found the 360 aim assist in the SDK's `_XENON` code: a target cone (10% of the view, 1000 units), a line-of-sight check, and turn **friction** (50%) through `usercmdGen->SetSlowJoystick`.
- Compiled it for PC behind `pm_AimAssist`, rebuilt the missing `rvWeapon::AllowAutoAim`/`GetAutoAimFOV`, and bridged friction to the engine with a cvar (`pm_joystickSlow`, the same pattern as `pm_isZoomed`).
- Smoke test (`tools/aim_assist_smoke.py`): friction 0 → 50 on target → 0 with assist off. Passes.
- **Bullet bend (patch 0009):** recovered from the 360's `rvWeapon::Attack`. When the crosshair is near but not on an enemy, each shot leaves the muzzle toward the enemy joint nearest the crosshair (chest height without joints). Teammates under the crosshair are never shot past. `pm_AimAssistBump`/`Threshold` turned out to be dead cvars on the 360 too. PC limits it to single player with a controller. Aim Assist is now No / Slowdown Only / Full (360). Smoke test `tools/aim_assist_bend_smoke.py` passes. Details: [AIM_ASSIST.md](AIM_ASSIST.md#muzzle-aim-the-360-bullet-bend-patch-0009).

### 3. Controller detection fix (patch 0002)
- The test PC had four Xbox-type pads (virtual ViGEm/Steam/Oculus pads plus the real Series X pad). openQ4 opened only the first, so the real pad was dead. Now every pad stays open and the one you press becomes active.

### 4. 360 recon (no recompilation)
- Decrypted and decompressed `default.xex` with XenonRecomp's loader (`tools/xexdump`). It's a 2005 launch title (XDK 2.0.2099, title `415607D2`) with a single executable.
- Rebuilt all **813 cvar defaults** from static `idCVar` objects. Notable: `m_yaw` 0.0253 and `m_pitch` 0.0209 are "stick yaw/pitch scale", `pm_zoomedSlow` 30, `pm_AimAssistThreshold` 6.0, and vehicle aim assist (15% cone, 20000 units), which isn't in the SDK.
- Disassembled the stick pipeline ([X360_CONTROLS.md](X360_CONTROLS.md)):
  1. circle→square gate (`0x822B6030`)
  2. **per-axis XInput dead zones 7849 / 8689** (`0x822B5F68`)
  3. **3-segment look curve** (`0x821C9A08`)
  4. 2-sample smoothing
  5. 60 Hz tic integration (`0x821C9AA8`)
  6. trigger threshold 64/255
- Frame timing: game logic is a fixed 60 Hz on the 360 too (`com_syncGameFrame` exists but is never set).
- The 360 options menu offered stick layouts (Default/Southpaw/Legacy/Legacy Southpaw), 4 button presets plus custom mapping, Vertical/Horizontal sensitivity, inversion, Aim Assist on/off and Vibration.

### 5. 360 controller feel (patch 0003)
- `in_joystickXenon 1` reproduces the whole pipeline. Tuning cvars: `in_xenonYawScale`, `in_xenonPitchScale`, `in_xenonZoomedSlow`, `in_xenonLookCurve`, `in_xenonSmoothing`.
- Hands-on: zoomed aiming fixed (30% instead of openQ4's 50%); overall "8.5/10".

### 6. Settings menu (patches 0004–0007)
- Controller rows for everything above, plus Field of View (`g_fov`, now saved between sessions) and Button Prompts.
- `tools/openq4_settings_rows.py` inserts rows and keeps the GUI layout, scroll table, settings registry and openQ4's coverage test in step. Also fixed an upstream hover misalignment.
- Survey against a modern-shooter checklist: [CONTROLLER_UX.md](CONTROLLER_UX.md). Glyphs were already device-aware in openQ4's default HUD.
- **Controller navigation on settings pages (0006):** the D-pad got stuck in each slider's number box. Fixed, along with row highlighting under controller focus, auto-scrolling the list and A as a click.
- **Help line (0007):** a panel under the Game Options list explains the highlighted option (all 84 rows).

### 7. Graphics
- Definitive defaults ([GRAPHICS.md](GRAPHICS.md), `config/definitive.cfg`): native 4K borderless, **240 fps cap**, adaptive vsync, **FOV 90**, 4× MSAA + SMAA, 16× AF, 2048 soft shadow maps, authored look. Applied once by `tools/launch_definitive.ps1`.
- **Low-res textures:** the sources are 256–512 px, and openQ4 was drawing the stock DXT-compressed copies. Worse, those copies inside the PK4s always beat loose hi-res pack files. `image_usePrecompressedTextures 2` fixes both.
- *HiRes Textures & Models* x2 packs (ModDB) installed and verified: all 822 pack-covered images on Air Defense 1 load at 2×. Level load goes from about 5 s to 16 s once cached (44 s on the first visit). Hands-on (Hangar 1): "looks way better with the texture pack".
- **Performance trace (0008):** `launch_definitive.ps1 -PerfTrace` logs per-second frame and GPU timings in game plus Windows' GPU counters; `tools/perf_report.py` breaks GPU use down by level, menu and load. First finding: level loads with the hi-res packs push the GPU to 30–57%.

### 8. Fixes along the way
- **Broken saves:** a shallow clone gave openQ4 build number 2, so every save failed validation. Fetching the full history (build 1686) fixed it.
- Two apparent "crashes" were the assistant force-closing the game to rebuild. That's now off-limits.

## Open items and next steps
1. **Tune the 360 feel** with more play; compare `in_xenonLookCurve 0/1` and `in_xenonSmoothing 0/1`.
2. **v0.1 release** with a ready-to-run build, then outreach (PCGamingWiki text ready in [OUTREACH.md](OUTREACH.md)).
3. **360 in-world screens:** "Interactive / Press Use / USE D-PAD" prompts and D-pad navigation.
4. **Legacy stick layouts and 360 button presets.**
5. **More recon:** vehicle aim assist (`0x82564300`), 360 walk/run threshold, per-weapon `aimAssistFOV` values from the 360 weapon defs.
6. **Linux:** build the patched openQ4 and test.
7. **Upstream:** offer patches 0002 (multi-pad), 0006 (settings navigation) and the hover fix to openQ4.
8. **Performance:** play a few levels with `-PerfTrace` and read the report before changing any defaults.

## Sister project
`fear360-recomp` (F.E.A.R. + F.E.A.R. Files, Xbox 360): a true static recompilation is planned there, using what we learned here about XEX tooling.
