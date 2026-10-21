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
| Glyph style override | ✔ | `in_promptStyle` cvar | n/a | **gap:** not in menu |
| Glyphs in HUD prompts | ✔ | ✔ retained HUD (exit, respawn, quick chat) | ✔ | done |
| Single-player hint text | ✔ | objectives hint uses `KeysFromBinding` (key names), `Player.cpp:5944` | ✔ | **gap:** switch to `KeysFromBindingForPrompt` |
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
| World FOV | ✔ | `g_fov` 90, not archived, not in menu | fixed | **gap:** add a slider and archive it |
| Weapon FOV | ✔ | ✔ `cl_gunfov` | n/a | done |
| Option descriptions | ✔ | hover highlight only | ✔ | **gap** |
| Grey out rows that don't apply | ✔ | n/a | n/a | **gap:** in 360 mode, openQ4's dead zone, curve and look sensitivity rows do nothing |
| Controller-navigable menus | ✔ | ✔ | ✔ | done |
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
