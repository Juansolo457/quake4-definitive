# Quake 4 Xbox 360 Static Recompilation: Roadmap

Goal: run the **Xbox 360 release of Quake 4** (2005 launch title, ported by Raven) natively on Windows and Linux. That means no full-system emulator, the 360's console controller handling (aim assist, look acceleration, controller-first menus), a frame rate well above the original's often sub-30 fps, and game data supplied from the user's own disc.

Same pipeline as the F.E.A.R. project: **XenonRecomp** (PowerPC `default.xex` → C++) + **XenosRecomp** (shaders), with a runtime underneath. ReXGlue (used by the GoldenEye 360 PC build) is another toolchain to evaluate.

---

## Why Quake 4 is the easier first target

Quake 4 is id Tech 4, a lightly modified Doom 3 engine. We have far more reference source for it than for F.E.A.R.:

| Code | Reference available | Coverage of the 360 binary |
|---|---|---|
| Engine (renderer, idLib, filesystem, sound, cmd/cvar, collision) | **Doom 3 GPL source** (2011) + **Doom 3 BFG** (2012, which has console/360-era code paths) | Most of the engine, with Raven's modifications on top |
| Game logic (weapons, AI, vehicles, Strogg, MP) | **Quake 4 SDK** from Raven (game DLL source, under SDK EULA) | Nearly all gameplay |
| Raven engine additions (effects system "BSE", etc.) | Partly reimplemented by **openQ4** (open-source Q4 engine replacement, beta) | Partial |

Most recompiled functions can therefore be **named and understood by matching against real source**. That makes debugging the recomp much easier, and a later non-matching decompilation realistic.

## Two ways to get "Quake 4 with native controller support"

| | A. 360 recomp (this project) | B. Source port (openQ4 / dhewm3-style + PC data) |
|---|---|---|
| What you're playing | The actual 360 build: its tuning, menus, aim assist | The PC game with a controller added |
| Effort | High | Low/medium: add SDL3 gamepad to an existing port |
| Performance | Good after renderer work | Excellent, already native |
| Controller feel | Authentic out of the box | Has to be recreated |

**Plan:** do A, since it's what you want. We'll also use B as a cross-check: once the recomp shows exactly how the 360 build handles aim assist and stick curves, that logic could be ported back to openQ4 too.

---

## Phases

### Phase 0: Find and dump the disc
See [RIPPING.md](RIPPING.md). Quake 4 360 is an early XGD2 disc. Record hashes in `docs/DUMPS.md`, never the files. Also keep your PC Quake 4 install at hand for comparing data files.

### Phase 1: Recon
- Extract and decrypt `default.xex`. Load it in IDA/Ghidra (PPC + XEX loader).
- Check for leftover symbols, asserts, and `idLib` strings. id Tech 4 is very string-heavy (cvar names, cmd names, decl names), which makes it quick to anchor functions against the Doom 3 / Q4 SDK source.
- Build a **symbol map** by auto-matching strings and call graphs against a PC build compiled from Doom 3 GPL + Q4 SDK.
- Diff the 360 `.pk4` data against PC: find 360-only defs, GUIs and controller config (`*.cfg`, `guis/`).
- Boot it in Xenia and note the compatibility status and which kernel/GPU features it uses.
- **Find the controller code early.** Look for the 360 usercmd generation (the `idUsercmdGen` equivalent), XInput calls, and aim assist / "auto-aim" cvars. That's the feature we care most about preserving.

### Phase 2: First recompile
XenonAnalyse → TOML config (function boundaries, jump tables, setjmp, register save/restore helpers) → XenonRecomp → compile against a stub runtime.

### Phase 3: Runtime
- Kernel/XAM shims: threads, sync, file I/O mounting the dumped disc, profile/save stubs, Live stubbed (we'll likely drop 360 MP online at first)
- **Renderer:** id Tech 4 has a clean renderer front-end/back-end split (`RB_*` functions, known from GPL source). The best option is probably to **hook the back-end and replace it with a native Vulkan/D3D12 path** instead of emulating Xenos command buffers. This is where the big performance win comes from.
- Audio: XAudio2/XMA → SDL3 audio + XMA decoder
- Input: XInput → **SDL3 gamepad**, which supports Xbox, PlayStation, Switch and Steam Deck controllers on Linux and Windows. Keep the 360 game's own stick/aim processing untouched.
- **Exit criteria:** boots to the main menu.

### Phase 4: Playable
Full single-player playthrough. Saves go to the user directory. Then decide whether to support multiplayer (local split-screen, if the 360 build has it, or LAN).

### Phase 5: Enhancements
- **Frame rate:** id Tech 4 runs game logic at a fixed 60 Hz tic (`USERCMD_HZ`). Rendering above 60 needs interpolation between tics. dhewm3 and the Doom 3 BFG work show how others have done it.
- Native resolution, widescreen FOV, better shadows/AA, optional mouse and keyboard, gyro aim through SDL3
- Packaging: AppImage/Flatpak, Steam Deck testing

### Phase 6 (optional): Gradual decompilation
Swap recompiled functions for real source, starting from the matching Doom 3 GPL / Q4 SDK code. This is far more realistic here than for F.E.A.R.

---

## Legal ground rules
- No game data, XEX files, or generated `ppc/` code in the repo. Users dump their own disc.
- The Doom 3 source is GPLv3, so if we include it, the project must be GPLv3 too. The Q4 SDK is under Raven's EULA: use it as reference, and don't redistribute it wholesale.

## Next actions
1. **You:** find the Quake 4 360 disc and your PC copy, then dump the disc (RIPPING.md).
2. **You:** send the recomp/hybrid repos you've been looking at.
3. **Us:** set up the reference trees (Doom 3 GPL, Doom 3 BFG, Q4 SDK, openQ4) under `reference/` (gitignored), then do Phase 1 recon once the XEX exists.
