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
| `pm_AimAssist` | 2 | 0 off; 1 target focus and friction; 2 also the 360 muzzle aim (patch 0009, below). |
| `pm_AimAssistSlow` | 50 | Controller turn speed % while on target (friction) |
| `pm_AimAssistDistance` | 1000 | Max range (units) |
| `pm_AimAssistFOV` | 10 | Unused unless `pm_AimAssistTest 1`; the cone is the weapon def key `aimAssistFOV` (default 10% of vertical half-FOV) |
| `pm_showAimAssist` | 0 | Draws the cone (red box around the crosshair) |
| `pm_joystickSlow` | (runtime) | Bridge: current friction %, 0 = none |

## Verified

`tools/aim_assist_smoke.py` loads `game/airdefense1` hidden, spawns a grunt in front of the crosshair and reads the bridge cvar. It **passed 2/2 runs**, giving `no target = 0`, `on target = 50`, `pm_AimAssist 0 → 0`. The build is clean (MSVC 19.44) with no warnings in the touched files.

**Not yet verified:** that the stick actually turns at half speed on target. The engine multiply is a one-line change in `JoystickMove`, but it needs someone with a controller to try it. Use `pm_showAimAssist 1`, sweep the crosshair across an enemy, and compare with `pm_AimAssist 0`.

## Muzzle aim, the 360 "bullet bend" (patch 0009)

**How it was found.** Scanning `default.xex` for code that touches the aim-assist cvars showed that nothing reads `pm_AimAssistBump` or `pm_AimAssistThreshold` on the 360 either: their only references are the cvar constructors. The 360 game code looks these cvars up by name instead (`cvarSystem->GetCVarInteger("pm_AimAssist…")`). Following those name strings led to four functions. One of them is `rvWeapon::Attack` (`0x8250D670`, named by its `"rvWeapon::Attack"` profiling string), and it reads `pm_AimAssistDistance`, which PC `Attack` never does.

**What it does.** After `Attack` places the muzzle, and only if the weapon's `AllowAutoAim()` (vtable `+0x2C`, the same call the player code uses for the `autoaim` crosshair state) is true and the player has a `bestEnemy`:
1. Trace from the eye along the view, `pm_AimAssistDistance` units, with mask `0x801` (`MASK_SHOT_RENDERMODEL`). A hit on a bound part counts as its bind master.
2. If the trace hits the enemy, nothing changes.
3. If it hits a teammate (the `aiManager.GetAllyTeam(team)` list, walked through `teamNode`), the shot goes to the end of the view ray, never past the teammate.
4. Otherwise the eye and the ray end are moved into the enemy's model space. `0x824421A0` loops over every joint (`idAnimator::GetJointTransform`, `0x82441A70`) and keeps the one with the largest `dot(normalize(joint - eye), rayDir)`. That's the body part nearest the crosshair. If it's joint 1 or later, the target is its world position (`idAnimatedEntity::GetJointWorldTransform`, `0x823F6408`). If not, the target is the enemy's origin + 32 units up.
5. The muzzle axis becomes `(target - muzzleOrigin).ToMat3()`, for hitscan and projectile weapons alike.

The aim cone (`bestEnemy`) is the weapon's `aimAssistFOV` % (default 10) of the half view angle, about ±4°. So shots bend by a few degrees at most, and a crosshair that's already on the enemy is left alone, which keeps headshots.

**Differences from the 360.** The 360 applied this for every input and in multiplayer. On PC it's single player only, and only while aiming with the controller, so mouse aim is never bent. The Settings row is **No / Slowdown Only / Full (360) / Full (Wide)** (`pm_AimAssist` 0–3).

**Full (Wide), patches 0010–0011.** Hands-on, the 360 bend almost never fired. The 360's target search (kept as modes 1–2) only considers enemies whose bounds touch the box around the 768-unit view ray. Looking along a map axis that box is nearly a line, so an enemy just beside the crosshair is never a target; the ±4° cone only filters that list. Mode 3 searches the whole cone (`idPlayer::FindAimAssistTargetInCone`: hostile, alive, clear line from the eye) and doubles its width (`pm_AimAssistWideScale` 2, about ±8.5°). The first hands-on test also exposed the controller check: it used the last input of any kind, so typing in the console or a mouse twitch turned the bend off. The engine now publishes `in_aimWithController`, set by look-stick movement and cleared only by real mouse movement (3+ counts in a usercmd). With `pm_showAimAssist 1` every shot that isn't bent says why: Aim Assist not Full, aiming with the mouse, weapon without aim assist, or no enemy in the cone. Hands-on after the fix: "test was better", with the console showing shots bending to joints.

**Testing.** `python -I tools/aim_assist_bend_smoke.py <exe> "<Quake 4 install>" <work dir>` passed 2 of 2 runs. It checks four cases: off target the shot turns toward a joint (chest 12.2°, a hand 3.3°); mode 1 and mouse input give no turn; with the crosshair on the enemy there's no turn. The friction test still passes. In game, `pm_showAimAssist 1` logs the chosen joint and draws each corrected shot as a yellow arrow, and the cheat command `testMuzzleAim [aim]` prints (and optionally aims at) where a shot would go. **Not verified yet:** the feel in play with a controller.

## Known gaps (need the 360 disc)

1. ~~View/muzzle correction~~: done (patch 0009). `pm_AimAssist 1` ("change player view method") has no code on the 360 either, so on PC it means friction only.
2. **360 stick tuning.** openQ4's dead zone (0.18) and look curve (1.35) are its own. The 360 values live in the engine's `idUsercmdGen`, which is only in the XEX.
3. **Per-weapon cones.** The 360 key is `aimAssistFOV` (patch 0009 reads it). PC weapon defs don't set it, so the cone is a flat 10% unless the 360 defs are checked for values.
4. **Shipped defaults.** The 360 `default.cfg` may override the SDK defaults above.
5. **Multiplayer.** The MP aim-assist block (the `gameLocal.isMultiplayer` path in `game/Player.cpp`, and `mpgame/`) is still `_XENON`-only, on purpose, because of fairness against mouse players.
6. ~~Menu toggle~~: done (patch 0004; three-way since 0009).
7. **Vehicle aim assist** (`pm_VehicleAimAssistFOV`/`Distance`, used by the 360's vehicle weapon code at `0x82564300`): not ported yet.

## Licensing note
The patch touches `src/game`, which openQ4 derives from the Quake 4 SDK (id/Raven SDK EULA, not GPL). That's the same terms openQ4 itself publishes under. Keep it as a patch against openQ4 and don't copy SDK files into this repo.
