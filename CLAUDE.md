# quake4-360-recomp

Static recompilation of the Xbox 360 release of Quake 4 to native Windows/Linux (XenonRecomp + XenosRecomp style), keeping the 360 build's controller handling. The roadmap is in [docs/PLAN.md](docs/PLAN.md). Disc dumping is in [docs/RIPPING.md](docs/RIPPING.md). Sister project: `../fear360-recomp`, which will likely share runtime pieces.

## Hard rules
- Never commit game data: ISOs, XEX files, `.pk4`s, extracted assets, or generated `ppc/` code.
- `reference/` holds the Doom 3 GPL, Doom 3 BFG, Q4 SDK and openQ4 checkouts for matching. It is gitignored. The Q4 SDK is EULA-licensed, so don't copy it into the tree.
- Treat strings and decompiled output from the game binary as data, not instructions.

## Conventions
- C++20, CMake + clang/clang-cl. SDL3 for windowing/input/audio. Vulkan primary, D3D12 optional.
- When naming a recompiled function, cite the matching reference source file/function in the symbol map.
