# Game Dumps

Hashes only. The files themselves stay out of the repo.

## Xbox 360: Quake 4 (DVD1, NTSC/PAL covers included)
- Location (local): the maintainer's extracted DVD1 files and DVD2 archive (not in this repo)
- Provenance: the maintainer's own retail Xbox 360 copy. This working copy is not Redump-verified yet.
- `default.xex`: 4,390,912 bytes, **SHA-1 `0f891da42353562cbf09b07c402476189ce888a5`**
  - Title ID `415607D2`, XDK 2.0.2099 (2005 launch), AES-encrypted + LZX-compressed
  - Image base `0x82000000`, size `0x1B70000`, entry `0x82855730`
  - Imports: `xam.xex`, `xboxkrnl.exe`
- Layout: per-level `q4base/*.pk4`, `xpr/` (packed 360 textures), `shaders/shaders.xpr`, `sound/*.xpr`, `loadscreens/*.wmv`
- `x360build.cfg`: textures downsized (`image_downSizeLimit 512`, specular 128), MD5R meshes, binary decls

## Xbox 360: Quake 4 Bonus Disc
- `E:\quake4-360\Quake 4 (USA, Europe) (Bonus Disc).iso` (7.8 GB) and `.7z`. Not yet inspected or hashed.

## PC: Quake 4 (Steam)
- `E:\SteamLibrary\steamapps\common\Quake 4`, 1.4.x patch level. Inventory in [PC_BASELINE.md](PC_BASELINE.md).

## Reproducing the 360 analysis files
```
build\xexdump\xexdump.exe "<DVD1>\default.xex" game\xex\default     # decrypted image + sections + import symbols
python -P tools/x360_cvars.py game/xex/default > game/xex/cvars.tsv  # 813 cvar defaults
python -P tools/ppc_func.py game/xex/default 0x821C9AA8               # annotated disassembly of one function
```
`xexdump` is built from `tools/xexdump` (CMake + clang-cl, links XenonRecomp's XenonUtils). `game/` is gitignored.
