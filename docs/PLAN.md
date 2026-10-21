# Quake 4 (Xbox 360) Native Port: Master Plan

**Goal:** the Xbox 360 release of Quake 4, running natively on Windows and Linux, with no full-system emulator. It should be clean and sharp (native resolution, proper AA, no jaggies), run at 60 fps or more, and play best on a gamepad. That includes the 360 build's own aim assist and stick tuning, controller-first menus, and working well on a TV or Steam Deck.

**Order:** Quake 4 first, F.E.A.R. second (`../fear360-recomp`). Quake 4 has much better reference source (see below), and the runtime we build for it carries straight over to F.E.A.R.

---

## 1. Prior art we're copying

| Project | Approach | What we take from it |
|---|---|---|
| [LostOdysseyRecomp](https://github.com/freefrank/LostOdysseyRecomp) (360) | Static recomp: XenonRecomp + XenosRecomp, UnleashedRecomp-style runtime, plume renderer (D3D12/Vulkan/Metal), Xenia's FFmpeg fork for XMA, SDL | **Our main template.** Repo layout (`<Game>Recomp/` app + `<Game>RecompLib/` generated lib), in-app importer (ISO/GOD/extracted folder/`default.xex`), shader pre-compilation and caching, SMAA/TAA/GTAO, DLSS/FSR/XeSS, 30–120 fps caps + VRR, AppImage/Flatpak packaging. You already have it installed at `E:\game backups\xbox360\Lost Odyssey`, which is a useful reference build to compare against. |
| [UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp) (360) | The original XenonRecomp-based port | The reference runtime: kernel/XAM shims, guest memory, the renderer, the installer flow, and mid-asm hook patterns. |
| [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) / [XenosRecomp](https://github.com/hedge-dev/XenosRecomp) | PPC → C++ and Xenos shaders → HLSL/DXIL/SPIR-V | The core tools. |
| [rexglue-sdk](https://github.com/rexglue/rexglue-sdk) (360) | Recomp toolchain with a Xenia-derived runtime (GoldenEye 360 PC build) | Alternative runtime if we want to boot sooner. Evaluate in M1. |
| [OpenCE](https://github.com/OpenCommunityEdition/OpenCE) (orig. Xbox Halo CE) | Decompilation compiled natively, SDL3, OpenGL/GLES/WebGL | **How to do upgrades well:** render every refresh while the sim stays at its native tick rate ("Smooth Motion"), optional AA modes, a high-res HUD, a configurable FOV, and Linux/Android/web from one codebase. |

## 2. What makes Quake 4 easier

Quake 4 is **id Tech 4**, the Doom 3 engine with Raven's additions. Nearly every function in the 360 `default.xex` has a source counterpart we can match against:

| Area | Reference (in `reference/`, gitignored) |
|---|---|
| Engine: renderer, idLib, filesystem, decls, cvars, collision, sound | `DOOM-3` (GPL, 2011), `DOOM-3-BFG` (GPL, 2012, has console-era code: XInput, joystick usercmd gen, aim assist helpers) |
| Game logic: weapons, AI, vehicles, MP | Quake 4 SDK 1.4.2 game source (Raven, SDK EULA; not on GitHub, comes from the SDK installer), plus `gbQuake4` (SDK merged into a Doom 3 port) |
| Raven engine additions (BSE effects, etc.) | `openQ4` (open-source Q4 engine and game replacement) |
| Modern id Tech 4 ports | `dhewm3` (SDL gamepad support, high-fps work), `openQ4` |

That means we can **name most of the recompiled code automatically** by matching strings and call graphs. It also means we can make targeted upgrades by replacing whole subsystems (renderer back-end, usercmd generation) with real source instead of patching blind.

---

## 3. Architecture: hybrid recomp

```
           ┌──────────────────────────────────────────────┐
           │ Quake 4 360 default.xex  (user's own disc)   │
           └───────────────┬──────────────────────────────┘
                XenonRecomp│ (build time)        XenosRecomp (shaders)
           ┌───────────────▼──────────────────────────────┐
           │ Q4RecompLib: recompiled game + engine (C++)  │
           │   ▲ hooks replace selected functions:        │
           │   │  • renderer back-end  → native renderer  │
           │   │  • frame timing       → interpolation    │
           │   │  • usercmd/input      → SDL3 + 360 logic │
           └───┼──────────────────────────────────────────┘
           ┌───┴──────────────────────────────────────────┐
           │ Runtime: kernel/XAM shims, VFS (ISO/GOD),    │
           │ threads, saves, XMA→PCM, SDL3 window/audio   │
           │ Renderer: plume (D3D12 / Vulkan), upscalers  │
           └──────────────────────────────────────────────┘
```

**Decision gate (end of M1):** decide how much of the renderer to replace.
- **Level 1 (default):** follow Lost Odyssey and render the game's own Xenos draw calls through plume, with recompiled shaders. Faithful, and proven to look great.
- **Level 2:** hook id Tech 4's `RB_*` back-end (known from Doom 3 source) and draw the frame with a native back-end. This gives better AA, shadows and resolution scaling, at the cost of more work.

### Update after M0: a faster path to 360 controls

The Q4 SDK game code in openQ4 still contains the **360 aim assist source** (`#ifdef _XENON`, see [PC_BASELINE.md](PC_BASELINE.md)). openQ4 already has SDL3 controllers, gyro, rumble, a Steam Deck profile, Vulkan, TAA/dynamic resolution and high-fps presentation. That opens a quick win that doesn't need the disc:

- **Track B, "openQ4 + 360 controls":** enable the `_XENON` aim-assist blocks behind a cvar in openQ4, and implement the missing engine-side `SetSlowJoystick` friction in its SDL3 usercmd path. Then, once the 360 disc is dumped, replace openQ4's stick tuning with the values recovered from the 360 XEX. The result is PC-quality assets at native speed with 360-style aiming, and it's a natural upstream contribution to openQ4.
- **Track A, the 360 recomp:** still the route to the *actual* 360 build: its menus/HUD, data, and exact behaviour. Its first recon job feeds Track B: recover `idUsercmdGen`'s joystick code and the 360 cvar defaults.

The tracks share the recon work. B gives a playable result within weeks, A within months.

### Update after M1 recon: "definitive edition" direction (2026-10-21)
The 360 game logic matches the SDK. The differences that matter for feel are all in input tuning (see [X360_CONTROLS.md](X360_CONTROLS.md)), and they're now ported into openQ4 (`in_joystickXenon`). The 360 textures were *downsized* (512 px cap) compared with PC. So the user is leaning towards a **"definitive edition"**: openQ4 + PC assets + the 360 controller feel, plus modern controller UX (Xbox/PlayStation glyphs, a full controller settings menu, FOV), in place of a full recomp. The recomp (Track A) stays on the shelf as the way to recover anything else 360-specific, such as menus, vehicle aim assist, or movement tuning. Next: glyphs and a settings menu, then a full-campaign playthrough test.

---

## 4. Quality targets

| | Original 360 | Our target |
|---|---|---|
| Resolution | 720p-class, possibly lower internally (**measure in Xenia, M1**) | Native display res up to 4K, ultrawide Hor+ FOV, resolution scale slider |
| Anti-aliasing | Little/none | SMAA / TAA / MSAA, later DLSS/FSR/XeSS like Lost Odyssey |
| Frame rate | ~30 fps with heavy drops | 60 fps locked first. Then 120+/VRR by interpolating between the fixed 60 Hz game tics (`USERCMD_HZ`), the same idea as OpenCE's Smooth Motion |
| Controls | 360 pad, aim assist | Same aim assist and curves (kept exactly), any controller through SDL3, rumble, optional gyro, remapping, optional mouse+keyboard |
| Platforms | 360 | Windows (D3D12/Vulkan), Linux (Vulkan, AppImage/Flatpak), Steam Deck |

---

## 5. Milestones

### M0: Groundwork (**now**, no 360 disc needed)
- [x] Reference repos cloned into `reference/`
- [ ] Get the Q4 SDK 1.4.2 game source from the official SDK installer into `reference/q4sdk/`
- [x] Inventory the PC install (`E:\SteamLibrary\steamapps\common\Quake 4`) with `tools/pk4_index.py`. See [PC_BASELINE.md](PC_BASELINE.md)
- [x] Build **openQ4** natively against the PC data as the **performance and visual baseline**. It builds with VS 2022, runs at 4K, and detects the controller. See [PC_BASELINE.md](PC_BASELINE.md)
- [x] Prototype Track B: enable the SDK's `_XENON` aim assist in openQ4 and add `SetSlowJoystick` friction. See [AIM_ASSIST.md](AIM_ASSIST.md); the smoke test passes, hands-on controller feel is still untested
- [ ] Study the LostOdysseyRecomp and UnleashedRecomp runtimes, and write `docs/RUNTIME_NOTES.md` covering what to copy, what's game-specific, and licenses
- [ ] Project skeleton: CMake + presets mirroring Lost Odyssey (`Q4Recomp/`, `Q4RecompLib/`, `thirdparty/`), CI for Windows and Linux

### M1: Recon (needs the dumped 360 disc)
- Dump and verify (see [RIPPING.md](RIPPING.md)), record the hash in `docs/DUMPS.md`
- Boot in Xenia: measure the native resolution, fps and compatibility, and log the kernel imports and GPU features used
- Load the XEX in Ghidra/IDA. Build the **symbol map** by matching strings and call graphs against Doom 3 / Q4 SDK
- **Find the controller code:** usercmd generation, XInput polling, aim assist (friction, magnetism, auto-centre) and its cvars, stick dead zones and curves
- Diff 360 data vs PC data (`.pk4`/GUIs/defs) to find 360-only content and config
- Runtime decision: UnleashedRecomp/LO-style or rexglue-sdk

### M2: First recompile
XenonAnalyse → TOML config (function boundaries, jump tables, setjmp, save/restore helpers) → XenonRecomp → compiles and links against a stub runtime.

### M3: Boots to the main menu
Kernel/XAM shims, VFS on the imported disc, threads and sync, XMA audio, shaders through XenosRecomp, renderer through plume, SDL3 input.

### M4: Playable
Full campaign playthrough, saves in the user directory, settings menu, controller-navigable launcher and importer.

### M5: Clean and fast
Resolution, AA, ultrawide, high-fps interpolation, upscalers, a high-res HUD, then Steam Deck testing and packaging.

### M6: F.E.A.R.
Reuse the runtime for `../fear360-recomp`.

---

## 6. Ground rules
- No game data, XEX files, `.pk4`s or generated recompiled code in the repo. Users import their own disc, as with Lost Odyssey.
- Doom 3 code is GPLv3. If any of it is compiled in, the project is GPLv3. The Q4 SDK is EULA-licensed: reference only.
- Check the license of each runtime we borrow from (UnleashedRecomp, Lost Odyssey) before copying code. Record it in `docs/RUNTIME_NOTES.md`.

## 7. Open questions for you
1. How did you dump Lost Odyssey (modded console, or a PC drive)? Use the same route for Quake 4.
2. Which Quake 4 360 edition and region do you have (regular or Special Edition)?
