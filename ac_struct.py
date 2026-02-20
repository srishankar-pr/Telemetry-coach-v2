

import ctypes


# ---------------------------------------------------------------------------
# Enums from Graphics.cs
# These are NOT ctypes types — just Python constants for readability.
# In the struct fields, enums are stored as ctypes.c_int.
# ---------------------------------------------------------------------------

class AC_STATUS:
    """Game status — read from Graphics.Status field"""
    AC_OFF    = 0
    AC_REPLAY = 1
    AC_LIVE   = 2
    AC_PAUSE  = 3


class AC_SESSION_TYPE:
    """Session type — read from Graphics.Session field"""
    AC_UNKNOWN     = -1
    AC_PRACTICE    = 0
    AC_QUALIFY     = 1
    AC_RACE        = 2
    AC_HOTLAP      = 3
    AC_TIME_ATTACK = 4
    AC_DRIFT       = 5
    AC_DRAG        = 6

class AC_FLAG_TYPE:
    """Track flag status — read from Graphics.Flag field"""
    AC_NO_FLAG        = 0
    AC_BLUE_FLAG      = 1  # faster car behind, let them pass
    AC_YELLOW_FLAG    = 2  # caution, slow down
    AC_BLACK_FLAG     = 3  # disqualified
    AC_WHITE_FLAG     = 4  # slow car ahead
    AC_CHECKERED_FLAG = 5  # race finished
    AC_PENALTY_FLAG   = 6  # penalty given


# ---------------------------------------------------------------------------
# Helper struct used by Physics for 3D coordinates (X, Y, Z)
# Matches C#: struct Coordinates { float X, Y, Z; }
# ---------------------------------------------------------------------------

class Coordinates(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("X", ctypes.c_float),
        ("Y", ctypes.c_float),
        ("Z", ctypes.c_float)
    ]


# ---------------------------------------------------------------------------
# Physics struct — from Physics.cs
# Shared memory region: "Local\\acpmf_physics"
# Fast-changing car data updated every frame by the game.
# ---------------------------------------------------------------------------

class Physics(ctypes.Structure):
    _pack_ = 4  # byte alignment — must match C#'s Pack = 4
    _fields_ = [
        # --- Core driving data ---
        ("PacketId", ctypes.c_int),       # increments each update
        ("Gas", ctypes.c_float),          # throttle pedal position (0.0 to 1.0)
        ("Brake", ctypes.c_float),        # brake pedal position (0.0 to 1.0)
        ("Fuel", ctypes.c_float),         # remaining fuel in litres
        ("Gear", ctypes.c_int),           # current gear (0=Reverse, 1=Neutral, 2=1st, 3=2nd...)
        ("Rpms", ctypes.c_int),           # engine RPM
        ("SteerAngle", ctypes.c_float),   # steering wheel angle
        ("SpeedKmh", ctypes.c_float),     # car speed in km/h

        # --- 3D motion vectors (X, Y, Z components) ---
        ("Velocity", ctypes.c_float * 3),            # car velocity vector [X, Y, Z]
        ("AccG", ctypes.c_float * 3),                 # G-forces [lateral, vertical, longitudinal]

        # --- Per-tyre data: index 0=FL, 1=FR, 2=RL, 3=RR ---
        ("WheelSlip", ctypes.c_float * 4),            # tyre slip ratio per wheel
        ("WheelLoad", ctypes.c_float * 4),             # load on each tyre in Newtons
        ("WheelsPressure", ctypes.c_float * 4),        # tyre pressure in PSI
        ("WheelAngularSpeed", ctypes.c_float * 4),     # rotational speed of each wheel
        ("TyreWear", ctypes.c_float * 4),              # tyre wear level per wheel
        ("TyreDirtyLevel", ctypes.c_float * 4),        # how dirty each tyre is
        ("TyreCoreTemperature", ctypes.c_float * 4),   # core temp of each tyre
        ("CamberRad", ctypes.c_float * 4),             # camber angle in radians per wheel
        ("SuspensionTravel", ctypes.c_float * 4),      # suspension compression per wheel

        # --- Car orientation and systems ---
        ("Drs", ctypes.c_float),          # DRS activation
        ("TC", ctypes.c_float),           # traction control level
        ("Heading", ctypes.c_float),      # car yaw angle (radians)
        ("Pitch", ctypes.c_float),        # car pitch angle (radians)
        ("Roll", ctypes.c_float),         # car roll angle (radians)
        ("CgHeight", ctypes.c_float),     # centre of gravity height

        ("CarDamage", ctypes.c_float * 5),  # damage per zone (5 zones: front, rear, left, right, ?)

        ("NumberOfTyresOut", ctypes.c_int),   # how many tyres are off track
        ("PitLimiterOn", ctypes.c_int),       # 1 if pit limiter is active
        ("Abs", ctypes.c_float),              # ABS activation level

        ("KersCharge", ctypes.c_float),       # KERS battery charge
        ("KersInput", ctypes.c_float),        # KERS input value
        ("AutoShifterOn", ctypes.c_int),      # 1 if auto-shift is enabled
        ("RideHeight", ctypes.c_float * 2),   # ride height [front, rear]

        # --- since v1.5 ---
        ("TurboBoost", ctypes.c_float),   # turbo boost pressure
        ("Ballast", ctypes.c_float),      # ballast weight in kg
        ("AirDensity", ctypes.c_float),   # air density

        # --- since v1.6 ---
        ("AirTemp", ctypes.c_float),      # ambient air temperature (°C)
        ("RoadTemp", ctypes.c_float),     # road surface temperature (°C)
        ("LocalAngularVelocity", ctypes.c_float * 3),  # angular velocity [X, Y, Z]
        ("FinalFF", ctypes.c_float),      # final force feedback value

        # --- since v1.7 ---
        ("PerformanceMeter", ctypes.c_float),  # delta vs best lap
        ("EngineBrake", ctypes.c_int),         # engine brake setting
        ("ErsRecoveryLevel", ctypes.c_int),    # ERS recovery level
        ("ErsPowerLevel", ctypes.c_int),       # ERS power deployment level
        ("ErsHeatCharging", ctypes.c_int),     # ERS heat charging
        ("ErsisCharging", ctypes.c_int),       # 1 if ERS is currently charging
        ("KersCurrentKJ", ctypes.c_float),     # current KERS energy in kilojoules
        ("DrsAvailable", ctypes.c_int),        # 1 if DRS is available
        ("DrsEnabled", ctypes.c_int),          # 1 if DRS is currently enabled
        ("BrakeTemp", ctypes.c_float * 4),     # brake disc temperature per wheel [FL, FR, RL, RR]

        # --- since v1.10 ---
        ("Clutch", ctypes.c_float),            # clutch pedal position (0.0 to 1.0)
        ("TyreTempI", ctypes.c_float * 4),     # tyre inner temperature per wheel
        ("TyreTempM", ctypes.c_float * 4),     # tyre middle temperature per wheel
        ("TyreTempO", ctypes.c_float * 4),     # tyre outer temperature per wheel

        # --- since v1.10.2 ---
        ("IsAIControlled", ctypes.c_int),      # 1 if car is AI-controlled

        # --- since v1.11 ---
        # Each is an array of 4 Coordinates structs (one per tyre), each containing X, Y, Z
        ("TyreContactPoint", Coordinates * 4),    # world position where tyre touches road
        ("TyreContactNormal", Coordinates * 4),   # surface normal at tyre contact point
        ("TyreContactHeading", Coordinates * 4),  # tyre heading direction at contact point
        ("BrakeBias", ctypes.c_float),             # front/rear brake balance

        # --- since v1.12 ---
        ("LocalVelocity", ctypes.c_float * 3)     # velocity in car's local space [X, Y, Z]
    ]


# ---------------------------------------------------------------------------
# Graphics struct — from Graphics.cs
# Shared memory region: "Local\\acpmf_graphics"
# Session and lap data — status, times, position, flags.
# ---------------------------------------------------------------------------

class Graphics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("PacketId", ctypes.c_int),
        ("Status", ctypes.c_int),             # AC_STATUS enum — game state (off/live/pause/replay)
        ("Session", ctypes.c_int),            # AC_SESSION_TYPE enum — practice/qualify/race/etc.

        # Lap times as Unicode strings (e.g. "1:23.456")
        ("CurrentTime", ctypes.c_wchar * 15), # current lap time
        ("LastTime", ctypes.c_wchar * 15),    # last completed lap time
        ("BestTime", ctypes.c_wchar * 15),    # session best lap time
        ("Split", ctypes.c_wchar * 15),       # split time

        ("CompletedLaps", ctypes.c_int),      # number of laps completed
        ("Position", ctypes.c_int),           # race position (1 = P1)

        # Lap times as integers (milliseconds) — easier for calculations
        ("iCurrentTime", ctypes.c_int),       # current lap time in ms
        ("iLastTime", ctypes.c_int),          # last lap time in ms
        ("iBestTime", ctypes.c_int),          # best lap time in ms

        ("SessionTimeLeft", ctypes.c_float),  # remaining session time in ms
        ("DistanceTraveled", ctypes.c_float), # total distance driven in metres
        ("IsInPit", ctypes.c_int),            # 1 if car is in pit box
        ("CurrentSectorIndex", ctypes.c_int), # which sector the car is in
        ("LastSectorTime", ctypes.c_int),     # last sector time in ms
        ("NumberOfLaps", ctypes.c_int),       # total laps in the race
        ("TyreCompound", ctypes.c_wchar * 33),# current tyre compound name (Unicode string)

        ("ReplayTimeMultiplier", ctypes.c_float),  # replay speed multiplier
        ("NormalizedCarPosition", ctypes.c_float), # track position 0.0–1.0
        ("CarCoordinates", ctypes.c_float * 3),    # car world position [X, Y, Z]

        ("PenaltyTime", ctypes.c_float),      # penalty time in seconds
        ("Flag", ctypes.c_int),               # AC_FLAG_TYPE enum — current track flag
        ("IdealLineOn", ctypes.c_int),        # 1 if ideal racing line is shown

        # --- since v1.5 ---
        ("IsInPitLane", ctypes.c_int),        # 1 if car is in pit lane (not box)
        ("SurfaceGrip", ctypes.c_float),      # track surface grip level

        # --- since v1.13 ---
        ("MandatoryPitDone", ctypes.c_int)    # 1 if mandatory pit stop completed
    ]


# ---------------------------------------------------------------------------
# StaticInfo struct — from StaticInfo.cs
# Shared memory region: "Local\\acpmf_static"
# Data that stays constant within a session (car, track, player, settings).
# Only changes when you switch car/track or start a new session.
# ---------------------------------------------------------------------------

class StaticInfo(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("SMVersion", ctypes.c_wchar * 15),    # shared memory version string
        ("ACVersion", ctypes.c_wchar * 15),    # Assetto Corsa game version

        # --- Session info ---
        ("NumberOfSessions", ctypes.c_int),
        ("NumCars", ctypes.c_int),             # number of cars on track
        ("CarModel", ctypes.c_wchar * 33),     # car name (e.g. "ferrari_458")
        ("Track", ctypes.c_wchar * 33),        # track name (e.g. "monza")
        ("PlayerName", ctypes.c_wchar * 33),   # driver first name
        ("PlayerSurname", ctypes.c_wchar * 33),# driver surname
        ("PlayerNick", ctypes.c_wchar * 33),   # driver nickname
        ("SectorCount", ctypes.c_int),         # number of track sectors

        # --- Car performance limits ---
        ("MaxTorque", ctypes.c_float),         # peak torque in Nm
        ("MaxPower", ctypes.c_float),          # peak power in watts
        ("MaxRpm", ctypes.c_int),              # engine redline RPM
        ("MaxFuel", ctypes.c_float),           # full tank capacity in litres
        ("SuspensionMaxTravel", ctypes.c_float * 4),  # max suspension travel [FL, FR, RL, RR]
        ("TyreRadius", ctypes.c_float * 4),    # tyre radius per wheel [FL, FR, RL, RR]

        # --- since v1.5 ---
        ("MaxTurboBoost", ctypes.c_float),     # max turbo boost pressure
        ("Deprecated1", ctypes.c_float),       # was AirTemp — moved to Physics in v1.6
        ("Deprecated2", ctypes.c_float),       # was RoadTemp — moved to Physics in v1.6
        ("PenaltiesEnabled", ctypes.c_int),    # 1 if penalties are on
        ("AidFuelRate", ctypes.c_float),       # fuel consumption rate multiplier
        ("AidTireRate", ctypes.c_float),       # tyre wear rate multiplier
        ("AidMechanicalDamage", ctypes.c_float),  # damage rate multiplier
        ("AidAllowTyreBlankets", ctypes.c_int),   # 1 if tyre blankets allowed
        ("AidStability", ctypes.c_float),      # stability aid level
        ("AidAutoClutch", ctypes.c_int),       # 1 if auto-clutch enabled
        ("AidAutoBlip", ctypes.c_int),         # 1 if auto-blip on downshift

        # --- since v1.7.1 ---
        ("HasDRS", ctypes.c_int),              # 1 if car has DRS system
        ("HasERS", ctypes.c_int),              # 1 if car has ERS system
        ("HasKERS", ctypes.c_int),             # 1 if car has KERS system
        ("KersMaxJoules", ctypes.c_float),     # max KERS energy in joules
        ("EngineBrakeSettingsCount", ctypes.c_int),  # number of engine brake settings
        ("ErsPowerControllerCount", ctypes.c_int),   # number of ERS power modes

        # --- since v1.7.2 ---
        ("TrackSPlineLength", ctypes.c_float),       # track spline length in metres
        ("TrackConfiguration", ctypes.c_wchar * 15), # track layout variant name

        # --- since v1.10.2 ---
        ("ErsMaxJ", ctypes.c_float),           # max ERS energy in joules

        # --- since v1.13 ---
        ("IsTimedRace", ctypes.c_int),         # 1 if race is time-based (not lap-based)
        ("HasExtraLap", ctypes.c_int),         # 1 if extra lap after time runs out
        ("CarSkin", ctypes.c_wchar * 33),      # car livery/skin name
        ("ReversedGridPositions", ctypes.c_int),  # number of reversed grid positions
        ("PitWindowStart", ctypes.c_int),      # pit window opens at this lap
        ("PitWindowEnd", ctypes.c_int)         # pit window closes at this lap
    ]