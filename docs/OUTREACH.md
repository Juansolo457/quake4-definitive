# Outreach (after v0.1)

Plan: post once a **v0.1 GitHub release** exists with a ready-to-run build. Wiki editors tend to remove build-from-source-only entries.

## PCGamingWiki: Quake 4 page
Edit needs a PCGamingWiki account (maintainer posts; the site's bot check blocks automated edits).

**Other information > Modifications**, after *Quake 4 4X AI Textures* (use the same heading level as that entry):
```
===Quake 4 Definitive Edition===
{{++}} Brings the Xbox 360 version's controller feel to the PC version as patches for [https://github.com/themuffinator/openQ4 openQ4]: the 360's per-axis XInput dead zones, look acceleration curve, look smoothing and turn speeds, and the 360 aim assist.
{{ii}} Reverse-engineered from the Xbox 360 executable. No game data included.<ref>{{Refurl|url=https://github.com/Juansolo457/quake4-definitive|title=GitHub - Juansolo457/quake4-definitive|date=2026-10-21}}</ref>
{{ii}} Adds in-game settings for these, plus a Field of View slider and controller button prompt styles.
```
Once a release exists, change the second bullet to point at the release download.

Under *Quake 4 4X AI Textures* (applies to any loose texture pack):
```
{{ii}} With openQ4, loose texture packs only load with <code>image_usePrecompressedTextures 2</code>; the default <code>1</code> keeps using the compressed textures inside the game's PK4 files.<ref>{{Refurl|url=https://github.com/Juansolo457/quake4-definitive/blob/master/docs/GRAPHICS.md|title=quake4-definitive - Graphics notes|date=2026-10-21}}</ref>
```

## Other places
1. ModDB mod page (next to the HiRes pack)
2. r/quake; openQ4 GitHub Discussions / Discord
3. Recomp/decomp list sites, filed as "related / reverse-engineered"
4. A short clip of the 360-feel aiming, linked from the README

## Repo-side findability (not applied yet)
- More topics: `xbox-360`, `quake-4`, `source-port`, `game-mod`, `gamepad`, `aim-assist`, `xinput`, `sdl3`, `steam-deck`, `windows`, `linux`, `xenonrecomp`
- Search words in the description and README opening ("Xbox 360 controller feel for Quake 4 on PC, an alternative to a full Xbox 360 recomp")
- Social preview image (GitHub Settings page, manual)
