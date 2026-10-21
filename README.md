# Quake 4 Definitive Edition

An unofficial project that brings the **Xbox 360 version's controller feel** to the PC version of Quake 4, running natively on modern Windows (and, via openQ4, Linux), with modern controller settings and clean high-resolution graphics.

> **No game data is included.** You need your own copy of Quake 4 for PC (Steam or GOG). Nothing here contains code, assets or binaries from id Software, Raven Software or Activision beyond what openQ4 already publishes.

## What this is (and isn't)

| Approach | Used here? |
|---|---|
| **Static recompilation** (translating the 360 executable to native code, like UnleashedRecomp or Lost Odyssey Recomp) | **No.** Planned for the sister project, F.E.A.R. 360 |
| **Full decompilation** (rebuilding source from the binary, like the Halo CE / OpenCE decomp) | **No** |
| **Source-port patches + targeted reverse engineering** | **Yes** |

The PC version already runs natively through [openQ4](https://github.com/themuffinator/openQ4), an open-source Quake 4 engine built from the GPL Doom 3 engine and Raven's Quake 4 SDK. The 360 game logic is the same game. What made the 360 version feel different was its **controller tuning**, which never shipped on PC. So this project:

1. reverse-engineers the specific 360 routines (stick processing, look curve, smoothing, aim-assist friction, triggers) by disassembling the 360 `default.xex`,
2. re-implements that behaviour in openQ4 as patches, behind settings you can switch on and off, and
3. adds the controller and graphics options a modern shooter is expected to have.

## Status

| Milestone | State |
|---|---|
| openQ4 builds and runs natively on Windows against Steam data | ✅ |
| 360 aim assist (target cone + friction), restored from the SDK's `_XENON` code | ✅ patch 0001 |
| Multiple Xbox-type pads: follows the one you actually use (virtual ViGEm/Steam pads no longer steal input) | ✅ patch 0002 |
| **360 controller feel**: square stick gate, per-axis XInput dead zones, 3-segment look curve, look smoothing, 360 turn speeds, 30% zoomed speed, 360 trigger threshold | ✅ patch 0003, hands-on rating "8.5/10", still being tuned |
| Settings menu: 360 Controller Feel, Aim Assist, Aim Assist Friction, Horizontal/Vertical/Zoomed speed | ✅ patch 0004 |
| Settings menu: Field of View (now saved), Button Prompts (Xbox/PlayStation/Nintendo/Steam Deck) | ✅ patch 0005 |
| Definitive graphics defaults (4K, 240 fps cap, 4× MSAA + SMAA, 16× AF, soft shadow maps) | ✅ `config/definitive.cfg` |
| Uncompressed textures plus support for hi-res texture packs | ✅ setting found and applied; pack install in progress |
| 360 in-world screen prompts / D-pad navigation, Legacy stick layouts, button presets | ⏳ next |
| Aim-assist "bullet bend" and vehicle aim assist (in the 360 binary, not in the SDK) | ⏳ needs more reverse engineering |
| Linux build and test | ⏳ untested (openQ4 supports Linux, but these patches haven't been built there yet) |

The full debrief is in [docs/PROGRESS.md](docs/PROGRESS.md).

## Getting started (Windows)

1. Install Quake 4 from Steam or GOG.
2. Build openQ4 with the patches:
   ```powershell
   git clone https://github.com/themuffinator/openQ4 reference/openQ4
   cd reference/openQ4
   git checkout cbe967f            # the commit the patches are made against
   git am ../../patches/openq4/*.patch
   ```
   Then follow openQ4's `BUILDING.md` (Meson + Ninja, Visual Studio). [docs/PC_BASELINE.md](docs/PC_BASELINE.md) has the exact recipe and the Windows gotchas we hit.
3. Launch with the definitive defaults (applied on first launch only; your menu changes stick afterwards):
   ```powershell
   pwsh tools/launch_definitive.ps1
   ```

### Controller settings
**Settings > Game Options > Controller**: *360 Controller Feel*, *Aim Assist*, *Aim Assist Friction*, *360 Horizontal Speed*, *360 Vertical Speed*, *360 Zoomed Speed*, *Button Prompts*. The console names are in [docs/X360_CONTROLS.md](docs/X360_CONTROLS.md) and [docs/AIM_ASSIST.md](docs/AIM_ASSIST.md).

### Hi-res textures (optional)
Quake 4's textures are mostly 256–512 px. [docs/GRAPHICS.md](docs/GRAPHICS.md) explains the `image_usePrecompressedTextures 2` setting that lets loose hi-res packs (such as *Quake 4: HiRes Textures & Models* on ModDB) actually load in openQ4, and where to install them.

## How the 360 behaviour was recovered
The 360 `default.xex` is decrypted and decompressed with XenonRecomp's loader (`tools/xexdump`). Cvar defaults are read straight from its static `idCVar` objects (`tools/x360_cvars.py`, 813 cvars), and the relevant functions are disassembled with constants resolved (`tools/ppc_func.py`). Findings, with addresses, are in [docs/X360_CONTROLS.md](docs/X360_CONTROLS.md). These tools need your own 360 copy; the outputs stay local (`game/` is gitignored).

## Repository layout
```
patches/openq4/   openQ4 patches (apply in order with git am)
config/           definitive.cfg (graphics + controller defaults)
docs/             findings, plans, progress, guides
tools/            launcher, XEX analysis, settings-menu row tool, smoke tests
```

## Legal
- Bring your own game. No assets, executables or proprietary code are distributed.
- The patches modify openQ4 and inherit its licensing: GPLv3 for engine files, and the Quake 4 SDK EULA for `src/game`/`src/mpgame` (as openQ4 publishes them).
- Everything else here (tools, docs, config) is MIT licensed; see [LICENSE](LICENSE) and [NOTICE](NOTICE).
- Quake 4 is a trademark of ZeniMax Media / id Software. This project isn't affiliated with or endorsed by id Software, Raven Software, Bethesda, ZeniMax, Activision or Microsoft.

## Credits
- **id Software and Raven Software**: Quake 4, the Doom 3 GPL source and the Quake 4 SDK
- **themuffinator and DarkMatter Productions**: [openQ4](https://github.com/themuffinator/openQ4), the engine this builds on
- **hedge-dev**: [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) (its XEX loader powers `xexdump`)
- Inspiration and patterns: [UnleashedRecomp](https://github.com/hedge-dev/UnleashedRecomp), [Lost Odyssey Recomp](https://github.com/freefrank/LostOdysseyRecomp), [OpenCE](https://github.com/OpenCommunityEdition/OpenCE)
- **wachhabender**: *Quake 4: HiRes Textures & Models* (recommended texture pack; download separately)
- Built with [Claude Code](https://claude.com/claude-code)
