# Xbox 360 Aim Assist in openQ4 (Track B)

The Quake 4 SDK's game code still contains Raven's Xbox 360 aim assist, compiled out on PC with `#ifdef _XENON` / `_XBOX`. This patch compiles it on every platform, gates it at runtime, and adds the engine half (stick friction) that the SDK never shipped.

- Patch: [`patches/openq4/0001-xenon-aim-assist.patch`](../patches/openq4/0001-xenon-aim-assist.patch) against openQ4 `cbe967f`
- Local branch: `reference/openQ4` → `q4x360/aim-assist` (commit `aa2295c`, not pushed)
- Test: `python -I tools/aim_assist_smoke.py <openQ4-client_x64.exe> "<Quake 4 install>" <work dir>`

## How the 360 version works (from the SDK source)

Every frame `idPlayer::UpdateFocus` does the following:
1. Builds an **aim frustum** from the eye: `pm_AimAssistDistance` (1000 units) deep, `GetAutoAimFOV()`% (10%) of the vertical view half-angle wide.
2. Walks the clip models along the 768-unit view ray. A living, hostile `idAI` whose bounds intersect the frustum and isn't hidden behind something closer becomes `bestEnemy`, with the nearest one winning.
3. If a trace from the eye to `bestEnemy`'s origin + 35 units (chest height) hits it, the game calls `usercmdGen->SetSlowJoystick(pm_AimAssistSlow)`. That's **friction**: stick turn speed drops to 50% while you're on target. Otherwise it calls `SetSlowJoystick(100)`. When zoomed, `pm_zoomedSlow` replaces it.
4. Sets the crosshair GUI states `autoaim` and `enemyFocus`.

The rocket launcher, grenade launcher and Dark Matter Gun opt out (`AllowAutoAim() → false`).

## What the patch changes

| Where | Change |
|---|---|
| `game/gamesys/SysCvar.*` | `pm_AimAssist*` are defined and declared unconditionally. `pm_AimAssist` (archived, default **2** as on 360) is the on/off switch. `pm_AimAssistSlow` is archived. New `pm_joystickSlow` is the bridge cvar. |
| `game/Player.*` | The SP aim-assist code runs at runtime, not behind `_XENON`. `bestEnemy` is always a member. `SetSlowJoystick` is replaced by `Player_SetJoystickSlow()`, which writes `pm_joystickSlow` and is reset on cinematic, spectator and perf-test early-outs. |
| `game/Weapon.*`, `game/weapon/*` | Restores the base `rvWeapon::AllowAutoAim()` (true) and `GetAutoAimFOV()` (weapon key `autoAimFOV`, default `pm_AimAssistFOV`), which the SDK omitted. The per-weapon opt-outs are no longer `#ifdef`'d. |
| `framework/UsercmdGen.cpp` | `GetJoystickSlowScale()` multiplies **controller look only** (the mouse is never slowed) by `pm_joystickSlow`%. Reset on map load. |

The game DLL talks to the engine through a cvar, the same pattern PC Quake 4 already uses for `pm_isZoomed`. That means no engine↔game interface or ABI change.

## Cvars

| Cvar | Default | Meaning |
|---|---|---|
| `pm_AimAssist` | 2 | 0 off; 1 or 2 on. On 360, 1 and 2 picked view vs muzzle correction, which isn't in the SDK (see gaps). |
| `pm_AimAssistSlow` | 50 | Controller turn speed % while on target (friction) |
| `pm_AimAssistDistance` | 1000 | Max range (units) |
| `pm_AimAssistFOV` | 10 | Cone size, % of vertical half-FOV (per weapon: `autoAimFOV` def key) |
| `pm_showAimAssist` | 0 | Draws the cone (red box around the crosshair) |
| `pm_joystickSlow` | (runtime) | Bridge: current friction %, 0 = none |

## Verified

`tools/aim_assist_smoke.py` loads `game/airdefense1` hidden, spawns a grunt in front of the crosshair and reads the bridge cvar. It **passed 2/2 runs**, giving `no target = 0`, `on target = 50`, `pm_AimAssist 0 → 0`. The build is clean (MSVC 19.44) with no warnings in the touched files.

**Not yet verified:** that the stick actually turns at half speed on target. The engine multiply is a one-line change in `JoystickMove`, but it needs someone with a controller to try it. Use `pm_showAimAssist 1`, sweep the crosshair across an enemy, and compare with `pm_AimAssist 0`.

## Known gaps (need the 360 disc)

1. **View/muzzle correction.** `pm_AimAssist 1/2`, `pm_AimAssistBump` and `pm_AimAssistThreshold` are declared but no SDK code uses them. The 360 build may bend the shot towards `bestEnemy`. Recover this from `default.xex` (search for xrefs to the `pm_AimAssistBump` string).
2. **360 stick tuning.** openQ4's dead zone (0.18) and look curve (1.35) are its own. The 360 values live in the engine's `idUsercmdGen`, which is only in the XEX.
3. **Per-weapon cones.** The 360 weapon defs may set `autoAimFOV`. PC defs don't, so the cone is a flat 10% for now.
4. **Shipped defaults.** The 360 `default.cfg` may override the SDK defaults above.
5. **Multiplayer.** The MP aim-assist block (the `gameLocal.isMultiplayer` path in `game/Player.cpp`, and `mpgame/`) is still `_XENON`-only, on purpose, because of fairness against mouse players.
6. **Menu toggle.** For now it's a cvar only. A row in `Settings → Game Options → Controller` (`content/baseoq4/pak0/guis/menu/settings/game.gui`) is a follow-up.

## Licensing note
The patch touches `src/game`, which openQ4 derives from the Quake 4 SDK (id/Raven SDK EULA, not GPL). That's the same terms openQ4 itself publishes under. Keep it as a patch against openQ4 and don't copy SDK files into this repo.
