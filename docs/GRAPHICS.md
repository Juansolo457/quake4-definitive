# Graphics Defaults (Definitive Edition)

Applied by [`tools/launch_definitive.ps1`](../tools/launch_definitive.ps1) from [`config/definitive.cfg`](../config/definitive.cfg) on a profile's first launch. After that, the in-game settings win (`-Reapply` applies them again).

## Graphics tiers
The defaults below are the **ultra** tier, tuned on an RTX 4090. Not every PC has that headroom, so on first launch the launcher reads the largest graphics card's video memory and applies a tier file after `definitive.cfg`. It uses the registry's exact 64-bit size; Windows' `AdapterRAM` stops at 4 GB.

| Tier | Video memory | On top of the defaults |
|---|---|---|
| ultra | 12 GB or more | nothing (4× MSAA + SMAA, 2048 shadow maps, 16× AF, 240 fps cap, uncompressed textures and hi-res packs) |
| high | 8 to 12 GB | `tier_high.cfg`: 2× MSAA, 1024 shadow maps, 8× AF, 144 fps cap |
| medium | 4 to 8 GB, or unknown | `tier_medium.cfg`: SMAA only, stock stencil shadows, 4× AF, compressed textures (about a quarter of the memory; hi-res packs not loaded), 120 fps cap |
| low | under 4 GB | `tier_low.cfg`: as medium, plus 85% render scale resolved back to native by TAA, 2× AF, 60 fps cap |

Picture (gamma/brightness), FOV and the controller settings are the same in every tier. The values follow openQ4's own performance presets (quality / balanced / performance), and each tier sets the matching menu label. `pwsh tools/launch_definitive.ps1 -ShowTier` prints the choice; `-Tier high` (and so on) forces one, together with `-Reapply` for an existing profile. Video memory is a stand-in for GPU speed, so a fast 8 GB card may want `-Tier ultra` and a slow 12 GB one `-Tier high`.

## Decisions (user, 2026-10-21)
- **Frame rate:** cap at **240** (`com_maxfps 240`), never higher. Adaptive vsync (`r_swapInterval -1`).
- **FOV:** **90** base (`g_fov`, 4:3 basis, about 106° horizontal at 16:9); lower it only if performance needs it.
- No benchmark iteration for now. The game is old and runs well; performance work (and any rewriting, now that both the PC SDK/openQ4 source and the 360 binary are available) comes later if needed.
- **Picture:** the 360's `r_gamma 1.3` and `r_brightness 1.2` are the default (see [below](#what-the-360-renderer-did-differently)).

## The defaults

| Area | Setting | Why |
|---|---|---|
| Display | borderless desktop fullscreen at native resolution, `r_screenFraction 100` | Clean 4K with no mode switch |
| AA | `r_multiSamples 4` + `r_postAA 1` (SMAA medium), alpha-to-coverage on | MSAA for geometry, SMAA for shader edges. 8× costs a lot more for little gain |
| Textures | `com_machineSpec 3`, no downsizing, `image_picmip 0`, **`image_anisotropy 16`** | Full resolution, sharp at angles |
| Texture source | **`image_usePrecompressedTextures 2`** | See below: uncompressed sources and hi-res packs |
| Shadows | `r_useShadowMap 1`, `r_shadowMapSize 2048`, PCSS-lite filtering | Soft, stable shadow maps instead of hard stencil volumes (the `ultra` preset's size) |
| Lighting | baked light grids on. SSAO, bloom, tone mapping, motion blur off | Keep Quake 4's authored look as the baseline, as openQ4's presets do |
| Picture | `r_gamma 1.3`, `r_brightness 1.2` | The Xbox 360's defaults; brighter, shinier highlights |
| Controller | `in_joystickXenon 1`, `pm_AimAssist 3` (Full, Wide), automatic button prompts | The recovered 360 feel |

**Opt-ins to try in game** (Settings > System and the console): `r_ssao 1` (ambient occlusion), `r_bloom 1`, `r_hdrToneMap 1`, `r_temporalAA 1` (TAA at native in place of SMAA), `r_renderApi vk` (Vulkan, stable on Windows).

## Why the textures look low-res, and the fix

Quake 4's PC textures are mostly **256×256–512×512** (it's a 2005 game). Each also ships as a pre-compressed `.dds` beside the `.tga`, the same size but DXT1/DXT5 (normal maps RXGB), which is lossy. A sample of 60 world and model pairs: every `.dds` matched its `.tga` size. Stock Quake 4 used the uncompressed TGAs only at "Ultra".

openQ4 finds an image in this order: `dds/<program>.dds`, `dds/<path>.dds`, **`<path>.dds` beside the original**, then the source. Files inside a PK4 carry no timestamp, so the stock `.dds` copies are never considered stale. With the default `image_usePrecompressedTextures 1`:
1. The game draws the **compressed** DDS copies, not the TGA sources.
2. **A loose hi-res texture pack is ignored** for every texture that has a stock `.dds` (6,351 of them), because the packed DDS wins first.

Note: choosing a Performance Preset or "Recommended" in the menu (`applyPerformancePreset`, `execMachineSpec`) writes it back to `1`. Relaunch with `-Reapply`, or run `seta image_usePrecompressedTextures 2; vid_restart`.

`image_usePrecompressedTextures 2` ignores DXT/RXGB `.dds` data (stock copies and the `progimg/` precomputed results) but still accepts BC7 packs. That gives uncompressed sources ("Ultra" quality) and lets loose pack files override. The costs are more VRAM (fine on 24 GB) and longer first loads; openQ4's binary image cache speeds up later loads.

## Hi-res texture packs (user downloads)

| Pack | Notes |
|---|---|
| [Quake 4: HiRes Textures & Models](https://www.moddb.com/mods/hires-textures-models) (wachhabender, Jun–Aug 2026) | **Recommended.** Real-ESRGAN 4× upscales "without changing the overall look". Separate **textures** and **models** downloads in **x2** and **x4**. The author warns x4 needs >6 GB VRAM and loads slowly; x2 models had black railgun/hyperblaster skins, fixed 2026-08-21 |
| [Quake 4 4X AI Textures](https://www.moddb.com/mods/quake-4-4x-ai-textures-by-deeppurple1968) (deeppurple1968, 2020) | Older Topaz Gigapixel 4× pack, 6.3 GB |
| [Quake 4 Hi Def](https://www.moddb.com/mods/quake-4-hi-def) (v3.3, ~14 GB) | Also replaces models and changes more. Asset parts may work, but anything relying on the stock game DLL won't run on openQ4 |

**Install for openQ4:** extract the pack's folders (`textures/`, `models/`, …) into **`<Quake 4 install>\baseoq4\`** (create it), not `q4base`. openQ4 searches `baseoq4` first, and a Steam file verification won't delete it. Keep `image_usePrecompressedTextures 2`.

**Verified (2026-10-21), *textures x2*** (`textures.zip`, MD5 `44dfb87dd150bf9ece1452fc9d290f81`):
- 6,076 `.tga` files under `textures/`, 3.19 GiB, with no executables or configs. A sample of 80 were all exactly 2× the stock size (256×256 → 512×512).
- `game/airdefense1` with `listImages`:
  - **mode 1:** 475 of 478 pack-covered textures loaded at **stock size as DXT1**. The pack is ignored. (This is why a ModDB commenter saw "no difference" with openQ4.)
  - **mode 2:** **478 of 478 loaded at the pack's 2× size, uncompressed RGBA8**.
- *models x2* (`models.1.zip`, MD5 `10d3112f7694f7bf4db11c135619c798`, the 2026-08-21 fixed upload): 2,887 `.tga` model textures, 14.2 GiB, with no executables or configs. The archive nests everything under an extra `models/` folder (`models/models/...`). Install it so the files land at `baseoq4/models/...`.
- **Both packs, mode 2, `game/airdefense1`:** all **822 pack-covered images** (478 world + 344 model) loaded at the pack's size, none at stock size.
- **Load time** for `game/airdefense1` (24 GB GPU, NVMe): about 5 s stock. With both packs, **44 s** on the first visit (building openQ4's binary image cache) and **16 s** after that. The largest single image is the Dark Matter Gun glow map, 85 MB uncompressed.

ModDB limits each connection to about 1.2 MB/s. Splitting the download into ranged requests across its mirrors (7 connections) gave about 7.6 MB/s.

## Measurement note
Automated 4K runs, both openQ4's `renderer_gameplay_benchmark.py` and my visible-window launcher `tools/bench_graphics.py`, reported a flat 60.0 fps "simulation-bound" in every configuration. openQ4 caps windows it considers hidden at 60 fps on Windows, and launches from this tool shell appear to trigger that. The numbers aren't the game's real performance and weren't used. Check in game with `com_showFPS 1` instead.

## What the 360 renderer did differently
Hands-on: the marines' yellow visors looked shinier on the 360. The visor material is byte-identical on both (`models/characters/marine/helmet`, `m_helmet`, `t_helmet`). A mask written to destination alpha, then `cubeMap gfx/env/marhelmet` with `texgen reflect`, `blend GL_DST_ALPHA, GL_ONE`, tinted by the entity color. openQ4 draws it with the stock bumpy-environment program, and a Hangar 1 screenshot of a medic shows the gold reflection. The 360 also ships its own `gfx/env/marhelmet` (and `sheen`, `medic`) inside its XPR2 texture bundles; extracting those needs an XPR2/tiled-texture decoder (not done).

The 360's renderer defaults (from `default.xex`'s cvar table) against openQ4:

| Cvar | 360 | openQ4 | Notes |
|---|---|---|---|
| `r_gamma` | **1.3** | 1.0 | brighter mid-tones; reflections and specular stand out more |
| `r_brightness` | **1.2** | 1.0 | brighter overall |
| `r_multiSamples` | 2 | 0 (definitive: 4) | |
| `image_anisotropy` | 1 | 16 (definitive) | ours is sharper |
| `r_lightDetailLevel` | 9 | 0 | openQ4 skips lights *below* this level, so the 360 dropped minor lights; PC renders all |
| `image_downSizeBumpLimit` / `SpecularLimit` | 0 (64) | 256 / 64 | 360 textures were downsized |

So the one 360 look worth taking is its gamma and brightness. openQ4 applies both in a shader (they show in screenshots); a side-by-side in Hangar 1 at 1.3/1.2 is visibly brighter. They are now the definitive defaults (user decision, 2026-10-21).

## GPU usage and the performance trace
Reported (2026-10-21): GPU usage near 40%, sometimes spiking. On the test PC (RTX 4090, 4K, 240 Hz) that's headroom, not a problem: at a 240 fps cap the GPU renders 240 frames a second and idles between them. The usage figure follows how heavy each frame is (open areas, many shadowed lights, effects) and how many frames are drawn. Levers, if needed: a lower `com_maxfps` (144 or 120 cuts GPU work roughly in proportion), `r_multiSamples 2`, `r_shadowMapSize 1024`.

To find where spikes come from, play with the trace on:
```powershell
pwsh tools/launch_definitive.ps1 -PerfTrace
python -I tools/perf_report.py        # after quitting: per level, per menu, loads, stalls
```
- **In game, `com_perfTrace 1`** (patch 0008) writes `<profile>/baseoq4/perftrace/trace_*.csv`. Each second gets a row with the level, the screen (game or a menu), fps, frame time, game logic time, renderer front/back end time, the renderer's whole-frame GPU time and the scene size. Frames of 50 ms or more (`com_perfTraceHitchMsec`) get their own row, and so does each level load. The whole-frame GPU time spans the buffer swap, so it includes waiting for the display and isn't GPU load.
- **Outside the game, `tools/perf_sampler.ps1`** (started by `-PerfTrace`) records Windows' own GPU counters every second into `gpu_*.csv`: the game's 3D utilization (Task Manager's number), the whole adapter's 3D utilization and the game's dedicated VRAM.
- **`tools/perf_report.py`** joins the two by time: GPU % and VRAM per level and per menu, the highest samples, the longest frames and the level loads.

First test (hidden 720p window, `game/airdefense1`, both hi-res packs): GPU 30–57% **while the level loaded** (texture uploads), then about 3% in play; VRAM about 1 GB. So asset loading alone can produce a GPU spike.
