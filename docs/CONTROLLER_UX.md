# Controller UX: Modern-Shooter Checklist (openQ4 + 360)

Surveyed 2026-10-21 against openQ4 `cbe967f` plus our patches 0001–0004 and the 360 build. "Menu" means Settings > Game Options in the classic settings GUI (`content/baseoq4/pak0/guis/menu/settings/game.gui`); the retained main menu hands Settings off to it.

## What the 360 version offered (from its mainmenu.gui and strings)
- **CONTROLS > STICKS:** Default, Southpaw, Legacy, Legacy Southpaw (`pm_ThumbstickConfig`)
- **CONTROLS > BUTTONS:** 4 presets (`pm_ButtonConfig`, `cfg/controls_1-4.cfg`), plus **Customize Buttons** (free remapping)
- **SENSITIVITY:** separate Vertical and Horizontal sliders (`m_pitch`/`m_yaw`, 0.006–0.06, step 0.002)
- **Look inversion:** Non-inverted / Inverted (`pm_Inversion`)
- **Aim Assist:** On/Off, "Helps the aim accuracy when firing at enemies." (`pm_aimAssist`)
- **Vibration:** On/Off (`input_rumble`)
- Every option had a one-line description shown under the list
- **In-world screens:** HUD brackets said "Interactive" with **"USE D-PAD"** (the screen was D-pad navigable, via the GUI's `dpadGUI` value) or **"Press Use"**. Driven by `GUIIsNotUsingDPad`/`hideInteractive`, which the SDK still sets under `_XENON`.
- Button glyph art: `gfx/guis/mainmenu/controller_btn_a/b/x/y`, objectives (wristcomm) `gfx/guis/hud/obj_btn1-4`, and a D-pad taunt widget (`gfx/guis/hud/dpad_*`).

## Checklist

| Feature | Modern shooters | openQ4 today | 360 | Status |
|---|---|---|---|---|
| Glyphs in menus | ✔ | ✔ Xbox/PS/Nintendo/Deck/generic, automatic | ✔ Xbox | done |
| Glyph style override | ✔ | `in_promptStyle` | n/a | done: Controller > Button Prompts (patch 0005) |
| Glyphs in HUD prompts | ✔ | ✔ retained HUD (exit, respawn, quick chat) | ✔ | done |
| Single-player hint text | ✔ | ✔ already. `KeysFromBinding` picks the last-used device's binding and emits a `^ikHH` glyph token; objectives hint, Remastered vehicle HUDs (`oq4_key_jump`: "Exit" + glyph) and the retained loading screen all use it | "Press USE to exit", A/B art | done upstream. Only the optional classic HUD (`ui_hudLayout 0`) still shows the stock "[ Press JUMP to exit ]" |
| In-world screen prompt | n/a | none for controller | "Interactive / Press Use / USE D-PAD" | **gap** |
| D-pad navigation of in-world screens | n/a | no | ✔ (`dpadGUI`) | **gap**, needs 360 recon of its GUI d-pad handling |
| Separate H/V sensitivity | ✔ | single look sensitivity | ✔ | done in 360 mode (patch 0004); native mode still single |
| ADS / zoom sensitivity | ✔ | Scope Sensitivity (`pm_zoomedSlow`) | ✔ (30%) | done: 360 Zoomed Speed (patch 0004) |
| Response curve choice | ✔ (presets) | numeric curve | fixed 3-segment | partial: 360 mode on/off, `in_xenonLookCurve` cvar only |
| Inner/outer dead zone per stick | ✔ | one inner dead zone | fixed XInput | **gap** |
| Invert Y / X | ✔ / ✔ | Y only | Y only | X is a minor gap |
| Stick layouts | ✔ | Default, Southpaw | + Legacy, Legacy Southpaw | **gap:** Legacy layouts |
| Button presets | ✔ | full rebinding only | 4 presets + custom | **gap:** presets |
| Aim assist on/off | ✔ | cvar only before | ✔ | done (patch 0004) |
| Aim assist strength | ✔ | n/a | fixed 50% | done: Aim Assist Friction (patch 0004) |
| Aim assist bullet bend / magnetism | ✔ | n/a | `pm_AimAssistBump`/`Threshold` exist, code not in SDK | **gap:** 360 recon |
| Vehicle aim assist | n/a | no | 15% cone, 20000 units | **gap:** 360 recon |
| Analog walk/run | ✔ | analog | walk/run threshold | optional |
| Vibration + strength | ✔ | ✔ | on/off | done |
| Trigger threshold | some | ✔ | 64/255 | done (360 mode uses 64/255) |
| Gyro | ✔ (PS/Switch) | ✔ | n/a | done |
| Toggle zoom / crouch / sprint | ✔ | zoom in menu; `in_toggleCrouch`, `in_alwaysRun` cvars | ✔ | **gap:** crouch and run toggles not in menu |
| World FOV | ✔ | `g_fov` 90 (4:3 basis, Hor+ on wide screens) | fixed | done: Gameplay And View > Field of View 70–130, now archived (patch 0005) |
| Weapon FOV | ✔ | ✔ `cl_gunfov` | n/a | done |
| Option descriptions | ✔ | hover highlight only | ✔ | done for Game Options: help line under the list (patch 0007) |
| Grey out rows that don't apply | ✔ | n/a | n/a | **gap:** in 360 mode, openQ4's dead zone, curve and look sensitivity rows do nothing |
| Controller-navigable menus | ✔ | ✔, except settings pages | ✔ | done: settings pages fixed (patch 0006) |
| Weapon wheel | ✔ | ✔ (openQ4 feature) | no (cycle/D-pad) | done |

## Added in patch 0004 (Settings > Game Options > Controller, after "Controller Input")

| Row | Cvar | Range |
|---|---|---|
| 360 Controller Feel | `in_joystickXenon` | No / Yes |
| Aim Assist | `pm_AimAssist` | No (0) / Yes (2) |
| Aim Assist Friction | `pm_AimAssistSlow` | 10–100 % (lower = stickier) |
| 360 Horizontal Speed | `in_xenonYawScale` | 0.006–0.06 (360 slider range), default 0.0253 |
| 360 Vertical Speed | `in_xenonPitchScale` | 0.006–0.06, default 0.0209 |
| 360 Zoomed Speed | `in_xenonZoomedSlow` | 10–100 %, default 30 |

Every row below moved down 144 px. The content height (2066 → 2210), section jumps, scroll limit (73 → 79) and section-from-scroll thresholds were updated in `game.gui`, `game_hovers.gui` and `Session_menu.cpp`, along with the settings registry and the `settings_menu_coverage.py` expectations, which pass. Labels were added to all 12 `*_openq4.lang` tables (English text for now). Also fixed a pre-existing upstream bug: the Weapon Kick hover sat 22 px above its row.

**Verified:** coverage test passes. A static layout check found 87 rows with no overlaps, and every hover is aligned to its row. **Not verified:** how it looks on screen. My automated screenshot runs stalled in a hidden instance, so it needs a manual look.

## Added in patch 0005
- **Gameplay And View > Field of View** (`g_fov`, slider 70–130, step 1). `g_fov` is now `PC_CVAR_ARCHIVE | CVAR_NOCHEAT`, range 1–179, declared identically in the SP and MP modules. Before this, SP didn't archive it, so it reset to 90 every launch. Map scripts still apply their FOV as an offset (`openq4_scriptFovOffset`), and MP still clamps to 90–175.
- **Controller > Button Prompts** (`in_promptStyle`: Automatic, Xbox, PlayStation, Nintendo, Steam Deck, Generic).
- Rows were inserted with `tools/openq4_settings_rows.py` and the specs in `tools/settings_specs/`. The tool moves rows and hovers, section jumps, scroll range and thresholds, registry, strings and test expectations together. Coverage test passes; static layout check: 89 rows, no overlaps, 84 hovers aligned. Aim-assist smoke test still passes.

## Settings pages with a controller (patch 0006)
Reported: A and B worked, but the D-pad and stick did nothing on Settings > Game Options. The cause: each slider row also has a number box for typing the value. Moving down from a slider put focus in that box, and a text box takes every arrow key, so navigation got stuck at the first slider. Moving up or down over a slider also nudged its value. And because a row's highlight comes from a separate hover window that only the mouse reached, nothing on screen showed where focus was.

Fixed in openQ4's classic GUI code (`src/ui/Window.cpp`):
- Number boxes paired with a slider, and list scrollbars, are skipped.
- A direction goes to the focused control only if the control uses it: choices and sliders take left/right, lists take up/down. Every other direction moves focus. Edit boxes keep left/right, plus up/down only for wrapped text.
- **A** works like a click: on a choice it steps to the next value.
- Controller focus lights the row and plays the hover sound, as the mouse does.
- Focus moving off the visible part of the list scrolls it, by the smallest step that shows the whole row (`scrollIntoView`, handled in `Session_menu.cpp` with each page's scroll table).

Covered by openQ4's `tools/tests/menu_controller_navigation.py` (extended). **Not verified:** a hands-on pass with a controller.

## Help line (patch 0007)
A panel under the Game Options list says what the highlighted option does, for the mouse and for controller focus. All 84 rows have text, and a default hint shows when no row is highlighted. The strings live in `tools/settings_specs/help.json`. `tools/openq4_settings_help.py` adds the panel, wires each row's hover window and writes the strings to every `*_openq4.lang` table. Run it again after adding rows; rows already wired are skipped. Checked on screen: the longest text wraps to three lines and fits.

## Graphics: the "Quake 4 Tweaker" mod
[Quake 4 Tweaker](https://community.pcgamingwiki.com/files/file/1009-quake-4-tweaker/) (PCGamingWiki) is a `dinput.dll` proxy for the stock `Quake4.exe`. It forces an FPS cap above 60, high image quality (fixing texture bugs on modern GPUs), corpse time, FOV, intro skipping and custom resolutions. openQ4 covers all of these natively (`com_maxfps`, performance presets and image settings, Corpse Time, Field of View, `g_autoSkipCinematics`, custom resolutions), and a DLL injected into the stock exe doesn't apply to openQ4's executable. **Follow-up:** pick definitive-edition graphics defaults from openQ4's options (presets, MSAA/SMAA/TAA, shadow maps, screen-space lighting, texture quality), since stock out-of-the-box settings are bare.
