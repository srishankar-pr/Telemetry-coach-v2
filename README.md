# Assetto Corsa — Python Shared Memory Reader

A Python library that reads **real-time telemetry** from [Assetto Corsa] via Windows shared memory (`mmap`). The game exposes three memory-mapped regions containing physics, graphics/session, and static car/track data. This project defines matching `ctypes.Structure` classes and provides simple reader functions to access them.

---

## Project Structure

| File | Purpose |
|---|---|
| `ac_struct.py` | `ctypes.Structure` definitions for **Physics**, **Graphics**, and **StaticInfo**, plus enum constants |
| `ac_reader.py` | Functions to open shared memory regions and return populated struct instances |
| `main.py` | Example live-loop that prints speed, RPM, and gear every 3 seconds |
| `notes.txt` | Developer reference notes on C#→Python type mappings |

---

## Requirements

- **Python 3.6+** (uses f-strings)
- **Windows** (shared memory via `mmap` requires the named memory regions created by Assetto Corsa)
- **Assetto Corsa** must be running for the shared memory regions to exist

No external packages are needed — only the standard library (`ctypes`, `mmap`, `time`).

---

## Quick Start

```bash
# 1. Start Assetto Corsa and enter a session (practice, race, etc.)

# 2. Run the live telemetry loop
python main.py

# Or run the standalone reader for a one-shot printout
python ac_reader.py
```

---

## How It Works

1. Assetto Corsa writes raw bytes into three **named shared memory regions**:
   - `Local\acpmf_physics` — updated every frame
   - `Local\acpmf_graphics` — updated on session/lap events
   - `Local\acpmf_static` — set once per session
2. `ac_struct.py` defines `ctypes.Structure` classes whose field order, types, and sizes exactly mirror the C# structs from the [AssettoCorsa SharedMemory library](https://github.com/mdjarv/assettocorsasharedmemory).
3. `ac_reader.py` opens each region with `mmap.mmap()`, reads the bytes, and copies them into a struct instance with `ctypes.memmove()`.

### C# → Python Type Mapping

| C# Type | Python `ctypes` Type | Size |
|---|---|---|
| `int` | `ctypes.c_int` | 4 bytes |
| `float` | `ctypes.c_float` | 4 bytes |
| `float[N]` | `ctypes.c_float * N` | 4×N bytes |
| `string` (Unicode) | `ctypes.c_wchar * N` | 2×N bytes |
| `enum` | `ctypes.c_int` | 4 bytes |

---

## Enum Constants

### `AC_STATUS` — Game State

| Constant | Value | Meaning |
|---|---|---|
| `AC_OFF` | 0 | Game is not active |
| `AC_REPLAY` | 1 | Watching a replay |
| `AC_LIVE` | 2 | Actively driving |
| `AC_PAUSE` | 3 | Game is paused |

### `AC_SESSION_TYPE` — Session Type

| Constant | Value | Meaning |
|---|---|---|
| `AC_UNKNOWN` | -1 | Unknown session |
| `AC_PRACTICE` | 0 | Free practice |
| `AC_QUALIFY` | 1 | Qualifying |
| `AC_RACE` | 2 | Race |
| `AC_HOTLAP` | 3 | Hotlap mode |
| `AC_TIME_ATTACK` | 4 | Time attack |
| `AC_DRIFT` | 5 | Drift mode |
| `AC_DRAG` | 6 | Drag race |

### `AC_FLAG_TYPE` — Track Flags

| Constant | Value | Meaning |
|---|---|---|
| `AC_NO_FLAG` | 0 | No flag shown |
| `AC_BLUE_FLAG` | 1 | Faster car behind — let them pass |
| `AC_YELLOW_FLAG` | 2 | Caution — slow down |
| `AC_BLACK_FLAG` | 3 | Disqualified |
| `AC_WHITE_FLAG` | 4 | Slow car ahead |
| `AC_CHECKERED_FLAG` | 5 | Race finished |
| `AC_PENALTY_FLAG` | 6 | Penalty given |

---

## Graphics Parameters

**Shared memory region:** `Local\acpmf_graphics`
Session and lap data — status, times, position, flags.

| Field | Type | Description |
|---|---|---|
| `PacketId` | `c_int` | Increments each update |
| `Status` | `c_int` | Game state (`AC_STATUS` enum) |
| `Session` | `c_int` | Session type (`AC_SESSION_TYPE` enum) |
| `CurrentTime` | `c_wchar * 15` | Current lap time as string (e.g. `"1:23.456"`) |
| `LastTime` | `c_wchar * 15` | Last completed lap time as string |
| `BestTime` | `c_wchar * 15` | Session best lap time as string |
| `Split` | `c_wchar * 15` | Split time as string |
| `CompletedLaps` | `c_int` | Number of laps completed |
| `Position` | `c_int` | Race position (1 = P1) |
| `iCurrentTime` | `c_int` | Current lap time in milliseconds |
| `iLastTime` | `c_int` | Last lap time in milliseconds |
| `iBestTime` | `c_int` | Best lap time in milliseconds |
| `SessionTimeLeft` | `c_float` | Remaining session time (ms) |
| `DistanceTraveled` | `c_float` | Total distance driven (metres) |
| `IsInPit` | `c_int` | `1` if car is in pit box |
| `CurrentSectorIndex` | `c_int` | Current track sector |
| `LastSectorTime` | `c_int` | Last sector time (ms) |
| `NumberOfLaps` | `c_int` | Total laps in race |
| `TyreCompound` | `c_wchar * 33` | Current tyre compound name |
| `ReplayTimeMultiplier` | `c_float` | Replay speed multiplier |
| `NormalizedCarPosition` | `c_float` | Track position (0.0–1.0) |
| `CarCoordinates` | `c_float * 3` | Car world position `[X, Y, Z]` |
| `PenaltyTime` | `c_float` | Penalty time (seconds) |
| `Flag` | `c_int` | Current flag (`AC_FLAG_TYPE` enum) |
| `IdealLineOn` | `c_int` | `1` if ideal racing line is shown |
| `IsInPitLane` | `c_int` | `1` if car is in pit lane *(v1.5+)* |
| `SurfaceGrip` | `c_float` | Track surface grip level *(v1.5+)* |
| `MandatoryPitDone` | `c_int` | `1` if mandatory pit stop completed *(v1.13+)* |

---

## StaticInfo Parameters

**Shared memory region:** `Local\acpmf_static`
Data that stays constant within a session (car, track, player, settings). Only changes when you switch car/track or start a new session.

| Field | Type | Description |
|---|---|---|
| `SMVersion` | `c_wchar * 15` | Shared memory version string |
| `ACVersion` | `c_wchar * 15` | Assetto Corsa game version |
| `NumberOfSessions` | `c_int` | Number of sessions |
| `NumCars` | `c_int` | Number of cars on track |
| `CarModel` | `c_wchar * 33` | Car name (e.g. `"ferrari_458"`) |
| `Track` | `c_wchar * 33` | Track name (e.g. `"monza"`) |
| `PlayerName` | `c_wchar * 33` | Driver first name |
| `PlayerSurname` | `c_wchar * 33` | Driver surname |
| `PlayerNick` | `c_wchar * 33` | Driver nickname |
| `SectorCount` | `c_int` | Number of track sectors |
| `MaxTorque` | `c_float` | Peak torque (Nm) |
| `MaxPower` | `c_float` | Peak power (Watts) |
| `MaxRpm` | `c_int` | Engine redline RPM |
| `MaxFuel` | `c_float` | Full tank capacity (litres) |
| `SuspensionMaxTravel` | `c_float * 4` | Max suspension travel `[FL, FR, RL, RR]` |
| `TyreRadius` | `c_float * 4` | Tyre radius per wheel `[FL, FR, RL, RR]` |
| `MaxTurboBoost` | `c_float` | Max turbo boost pressure *(v1.5+)* |
| `Deprecated1` | `c_float` | *(was AirTemp — moved to Physics in v1.6)* |
| `Deprecated2` | `c_float` | *(was RoadTemp — moved to Physics in v1.6)* |
| `PenaltiesEnabled` | `c_int` | `1` if penalties are on *(v1.5+)* |
| `AidFuelRate` | `c_float` | Fuel consumption rate multiplier *(v1.5+)* |
| `AidTireRate` | `c_float` | Tyre wear rate multiplier *(v1.5+)* |
| `AidMechanicalDamage` | `c_float` | Damage rate multiplier *(v1.5+)* |
| `AidAllowTyreBlankets` | `c_int` | `1` if tyre blankets allowed *(v1.5+)* |
| `AidStability` | `c_float` | Stability aid level *(v1.5+)* |
| `AidAutoClutch` | `c_int` | `1` if auto-clutch enabled *(v1.5+)* |
| `AidAutoBlip` | `c_int` | `1` if auto-blip on downshift *(v1.5+)* |
| `HasDRS` | `c_int` | `1` if car has DRS *(v1.7.1+)* |
| `HasERS` | `c_int` | `1` if car has ERS *(v1.7.1+)* |
| `HasKERS` | `c_int` | `1` if car has KERS *(v1.7.1+)* |
| `KersMaxJoules` | `c_float` | Max KERS energy (joules) *(v1.7.1+)* |
| `EngineBrakeSettingsCount` | `c_int` | Number of engine brake settings *(v1.7.1+)* |
| `ErsPowerControllerCount` | `c_int` | Number of ERS power modes *(v1.7.1+)* |
| `TrackSPlineLength` | `c_float` | Track spline length (metres) *(v1.7.2+)* |
| `TrackConfiguration` | `c_wchar * 15` | Track layout variant name *(v1.7.2+)* |
| `ErsMaxJ` | `c_float` | Max ERS energy (joules) *(v1.10.2+)* |
| `IsTimedRace` | `c_int` | `1` if time-based race *(v1.13+)* |
| `HasExtraLap` | `c_int` | `1` if extra lap after time runs out *(v1.13+)* |
| `CarSkin` | `c_wchar * 33` | Car livery/skin name *(v1.13+)* |
| `ReversedGridPositions` | `c_int` | Number of reversed grid positions *(v1.13+)* |
| `PitWindowStart` | `c_int` | Pit window opens at this lap *(v1.13+)* |
| `PitWindowEnd` | `c_int` | Pit window closes at this lap *(v1.13+)* |

---

## Physics Parameters

**Shared memory region:** `Local\acpmf_physics`
Fast-changing car data updated every frame by the game.

> **Tyre index order:** `0 = FL, 1 = FR, 2 = RL, 3 = RR`

| Field | Type | Description |
|---|---|---|
| `PacketId` | `c_int` | Increments each update |
| `Gas` | `c_float` | Throttle pedal position (0.0–1.0) |
| `Brake` | `c_float` | Brake pedal position (0.0–1.0) |
| `Fuel` | `c_float` | Remaining fuel (litres) |
| `Gear` | `c_int` | Current gear (0=R, 1=N, 2=1st, 3=2nd…) |
| `Rpms` | `c_int` | Engine RPM |
| `SteerAngle` | `c_float` | Steering wheel angle |
| `SpeedKmh` | `c_float` | Car speed (km/h) |
| `Velocity` | `c_float * 3` | Car velocity vector `[X, Y, Z]` |
| `AccG` | `c_float * 3` | G-forces `[lateral, vertical, longitudinal]` |
| `WheelSlip` | `c_float * 4` | Tyre slip ratio per wheel |
| `WheelLoad` | `c_float * 4` | Load on each tyre (Newtons) |
| `WheelsPressure` | `c_float * 4` | Tyre pressure (PSI) |
| `WheelAngularSpeed` | `c_float * 4` | Rotational speed of each wheel |
| `TyreWear` | `c_float * 4` | Tyre wear level per wheel |
| `TyreDirtyLevel` | `c_float * 4` | Tyre dirtiness per wheel |
| `TyreCoreTemperature` | `c_float * 4` | Core temperature of each tyre |
| `CamberRad` | `c_float * 4` | Camber angle (radians) per wheel |
| `SuspensionTravel` | `c_float * 4` | Suspension compression per wheel |
| `Drs` | `c_float` | DRS activation |
| `TC` | `c_float` | Traction control level |
| `Heading` | `c_float` | Car yaw angle (radians) |
| `Pitch` | `c_float` | Car pitch angle (radians) |
| `Roll` | `c_float` | Car roll angle (radians) |
| `CgHeight` | `c_float` | Centre of gravity height |
| `CarDamage` | `c_float * 5` | Damage per zone (front, rear, left, right, ?) |
| `NumberOfTyresOut` | `c_int` | How many tyres are off track |
| `PitLimiterOn` | `c_int` | `1` if pit limiter is active |
| `Abs` | `c_float` | ABS activation level |
| `KersCharge` | `c_float` | KERS battery charge |
| `KersInput` | `c_float` | KERS input value |
| `AutoShifterOn` | `c_int` | `1` if auto-shift is enabled |
| `RideHeight` | `c_float * 2` | Ride height `[front, rear]` |
| `TurboBoost` | `c_float` | Turbo boost pressure *(v1.5+)* |
| `Ballast` | `c_float` | Ballast weight (kg) *(v1.5+)* |
| `AirDensity` | `c_float` | Air density *(v1.5+)* |
| `AirTemp` | `c_float` | Ambient air temperature (°C) *(v1.6+)* |
| `RoadTemp` | `c_float` | Road surface temperature (°C) *(v1.6+)* |
| `LocalAngularVelocity` | `c_float * 3` | Angular velocity `[X, Y, Z]` *(v1.6+)* |
| `FinalFF` | `c_float` | Final force feedback value *(v1.6+)* |
| `PerformanceMeter` | `c_float` | Delta vs best lap *(v1.7+)* |
| `EngineBrake` | `c_int` | Engine brake setting *(v1.7+)* |
| `ErsRecoveryLevel` | `c_int` | ERS recovery level *(v1.7+)* |
| `ErsPowerLevel` | `c_int` | ERS power deployment level *(v1.7+)* |
| `ErsHeatCharging` | `c_int` | ERS heat charging *(v1.7+)* |
| `ErsisCharging` | `c_int` | `1` if ERS is currently charging *(v1.7+)* |
| `KersCurrentKJ` | `c_float` | Current KERS energy (kJ) *(v1.7+)* |
| `DrsAvailable` | `c_int` | `1` if DRS is available *(v1.7+)* |
| `DrsEnabled` | `c_int` | `1` if DRS is currently enabled *(v1.7+)* |
| `BrakeTemp` | `c_float * 4` | Brake disc temperature per wheel *(v1.7+)* |
| `Clutch` | `c_float` | Clutch pedal position (0.0–1.0) *(v1.10+)* |
| `TyreTempI` | `c_float * 4` | Tyre inner temperature per wheel *(v1.10+)* |
| `TyreTempM` | `c_float * 4` | Tyre middle temperature per wheel *(v1.10+)* |
| `TyreTempO` | `c_float * 4` | Tyre outer temperature per wheel *(v1.10+)* |
| `IsAIControlled` | `c_int` | `1` if car is AI-controlled *(v1.10.2+)* |
| `TyreContactPoint` | `Coordinates * 4` | World position where tyre touches road *(v1.11+)* |
| `TyreContactNormal` | `Coordinates * 4` | Surface normal at tyre contact *(v1.11+)* |
| `TyreContactHeading` | `Coordinates * 4` | Tyre heading direction at contact *(v1.11+)* |
| `BrakeBias` | `c_float` | Front/rear brake balance *(v1.11+)* |
| `LocalVelocity` | `c_float * 3` | Velocity in car's local space `[X, Y, Z]` *(v1.12+)* |

### `Coordinates` Helper Struct

Used for per-tyre 3D contact data:

| Field | Type | Description |
|---|---|---|
| `X` | `c_float` | X coordinate |
| `Y` | `c_float` | Y coordinate |
| `Z` | `c_float` | Z coordinate |

---

## Reader Functions (`ac_reader.py`)

| Function | Returns | Shared Memory Region |
|---|---|---|
| `read_physics()` | `Physics` or `None` | `Local\acpmf_physics` |
| `read_graphics()` | `Graphics` or `None` | `Local\acpmf_graphics` |
| `read_static_info()` | `StaticInfo` or `None` | `Local\acpmf_static` |

Each function returns `None` with an error message if the shared memory region cannot be opened (i.e. Assetto Corsa is not running).

---

## License

This project is for educational / personal use. The shared memory struct definitions are based on the [AssettoCorsa SharedMemory](https://github.com/mdjarv/assettocorsasharedmemory) C# library.
