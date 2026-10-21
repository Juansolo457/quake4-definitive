# Xbox 360 Controls, Recovered from default.xex

Everything here comes from the decrypted 360 executable (see [DUMPS.md](DUMPS.md) for the hash). Addresses are virtual addresses in that image. The behaviour is reproduced in openQ4 as `in_joystickXenon 1` ([`patches/openq4/0003-xenon-controller-feel.patch`](../patches/openq4/0003-xenon-controller-feel.patch)).

## Pipeline

```
XInputGetState (0x822B6180 polls 4 pads)
  └─ per stick: circle→square (0x822B6030)  →  per-axis dead zone + linear rescale to ±127 (0x822B5F68)
       └─ idUsercmdGenLocal::JoystickMove (0x821C9AA8)
            ├─ stick routing by pm_ThumbstickConfig, pitch flip by pm_Inversion
            ├─ look curve (0x821C9A08)
            ├─ 2-sample smoothing
            └─ yaw -= m_yaw·v·slow, pitch += m_pitch·v·slow   (per 60 Hz tic)
```

### 1. Circle → square (`0x822B6030`)
`len = |(x, y)|` (fast inverse sqrt, magic `0x5F3759DF` with one Newton step), then `k = len / max(|x|, |y|)` and `(x, y) *= k`, clamped to ±32767. A full diagonal push therefore gives full deflection on both axes.

### 2. Per-axis dead zone (`0x822B5F68`)
| Stick | Dead zone (of 32767) | Constant |
|---|---|---|
| Left | 7849 (24.0%) | `XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE` |
| Right | 8689 (26.5%) | `XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE` |

`out = (v ∓ dz) / (32767 − dz) · 127` outside the dead zone, otherwise 0, truncated to an int. Each axis is handled on its own (an "axial" or cross-shaped dead zone), not radially. Y is negated so that up is negative.

### 3. Look curve (`0x821C9A08`)
`x` is the axis as a fraction of full (0..1), and the sign is kept:

| Range | Output |
|---|---|
| x < 0.25 | 0.3·x |
| 0.25 ≤ x < 0.75 | 0.075 + 0.6·(x − 0.25) |
| x ≥ 0.75 | 0.375 + 2.5·(x − 0.75) |

### 4. Smoothing
Per tic, `filter = (filter + curved) · 0.5`, reset to 0 when the axis reads 0. That's a one-pole low-pass with about one tic of lag, and part of why the 360 felt "smooth" rather than snappy.

### 5. Speed
`yaw -= m_yaw · filter · slow` and `pitch += m_pitch · filter · slow` once per 60 Hz usercmd tic, with `filter` in ±127 units.
- `m_yaw` **0.0253** ("stick yaw scale"), `m_pitch` **0.0209** ("stick pitch scale"). The 360 Sensitivity menu slides them over 0.006–0.06 in 0.002 steps.
- Full stick: 0.0253·127·60 ≈ **193°/s yaw**, ≈ **159°/s pitch**. Half stick ≈ 22°/s.
- `slow` = the `SetSlowJoystick` percent ÷ 100: `pm_zoomedSlow` (**30**) while zoomed, otherwise the aim-assist friction (`pm_AimAssistSlow` 50 on target, else 100).
- An extra **×0.75** applies when an entity handle at `idPlayer+0x1250` is valid, most likely when in a vehicle. Not ported.

### 6. Triggers and buttons
- A trigger counts as pressed when its byte is **> 64 of 255**, with no hysteresis (`0x822B63F0`).
- Button layouts are `cfg/controls_1-4.cfg`, chosen by `pm_ButtonConfig`.
- Stick layouts come from `pm_ThumbstickConfig`: 0 Default, 1 Southpaw, 2 Legacy, 3 Legacy Southpaw. Legacy splits move and look across the sticks: left Y moves forward, right X strafes, left X yaws, right Y pitches.

### 7. Movement
The move stick doesn't feed analog speed directly. If either axis is above `pm_walkspeed / pm_speed · 127`, the run button is set and the axes pass through unchanged. Below that, the axes are rescaled so the walk range covers the full stick. **Not ported yet.**

## 360 cvar defaults that differ

Full table: `python -P tools/x360_cvars.py game/xex/default` (813 cvars; output stays local).

| Cvar | 360 | SDK / openQ4 |
|---|---|---|
| `m_yaw` / `m_pitch` | 0.0253 / 0.0209 (stick scales) | 0.022 / 0.022 (mouse) |
| `pm_zoomedSlow` | 30 | 50 |
| `pm_AimAssistThreshold` | 6.0 | 1.0 |
| `pm_VehicleAimAssistFOV` / `Distance` | 15 / 20000 | not in SDK |
| weapon key | `aimAssistFOV` | patch 0001 reads `autoAimFOV` (to rename) |
| `com_syncGameFrame` | 0, and never set by code | n/a |

## Frame timing
`com_syncGameFrame` ("run one game frame for every rendered frame") exists, defaults to 0, and nothing in the code sets it. Game logic ran at a fixed 60 Hz no matter the frame rate, the same as PC, so at ~25 fps the 360 ran 2–3 game tics per drawn frame. How the 360 actually presented frames (its Direct3D `PresentationInterval` or immediate-present threshold) is **not found yet**. The `r_swapInterval` cvar (0) is a leftover from PC.

## openQ4 mapping (`in_joystickXenon 1`)

| 360 step | openQ4 |
|---|---|
| circle→square, per-axis dead zone | `SDL3_XenonStickAxes` (sdl3_backend.cpp), per physical stick; southpaw swaps the dead zones with the roles |
| trigger > 64/255 | `SDL3_UpdateTriggerButtons` |
| curve, smoothing, m_yaw/m_pitch, zoomed 30 | `idUsercmdGenLocal::XenonJoystickLook` (UsercmdGen.cpp). Smoothing is time-corrected (`0.5^tics`) for usercmd rates other than 60 Hz |
| tuning | `in_xenonYawScale` 0.0253, `in_xenonPitchScale` 0.0209, `in_xenonZoomedSlow` 30, `in_xenonLookCurve` 1, `in_xenonSmoothing` 1 |

In 360 mode, openQ4's `in_joystickDeadZone`, `in_joystickLookCurve`, `in_joystickLookSensitivity` and `in_yawspeed` don't affect the controller. The weapon wheel keeps openQ4's own handling.

**Verified:** builds clean, and the aim-assist smoke test passes 2/2 with the mode in place. **Not verified:** hands-on feel. The math is a direct port, but nobody has played with it on a controller yet.
