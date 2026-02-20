import mmap
import ctypes
from ac_struct import Physics, Graphics, StaticInfo

def read_physics():
    # Open "Local\\acpmf_physics", read bytes, return Physics struct
    
    #size of the data 
    size=ctypes.sizeof(Physics)

    #opening the shared memory region with its name 
    try:
        mm=mmap.mmap(-1,size,"Local\\acpmf_physics")
    except Exception as e:
        print(f"Could not connect to Physics shared memory: {e}")
        print("Is Assetto Corsa running?")
        return None

    buf=mm.read(size)

    data=Physics() #creating an empty structure 

    ctypes.memmove(ctypes.byref(data),buf,size)

    #using memmove to copy the data from struct to reader structure 
    #ctypes.byref is used for destination
    #buf is the source (raw bytes from shared memory)
    #size is the number of bytes to copy

    mm.close()
    return data 


def read_graphics():
    # Open "Local\\acpmf_graphics", read bytes, return Graphics struct

    size=ctypes.sizeof(Graphics)#reading the size of the Graphics struct 

    try:
        mm=mmap.mmap(-1,size,"Local\\acpmf_graphics")
    except Exception as e:
        print(f"Could not connect to Graphics shared memory: {e}")
        print("Is Assetto Corsa running?")
        return None

    buf=mm.read(size)

    data=Graphics() #creating an empty structure for graphics(reader structure)

    ctypes.memmove(ctypes.byref(data),buf,size)

    #using memmove to copy the data from struct to reader structure 
    #ctypes.byref is used for destination
    #buf is the source (raw bytes from shared memory)
    #size is the number of bytes to copy

    mm.close()

    return data 

def read_static_info():
    # Open "Local\\acpmf_static", read bytes, return StaticInfo struct

    size=ctypes.sizeof(StaticInfo)

    try:
        mm=mmap.mmap(-1,size,"Local\\acpmf_static")
    except Exception as e:
        print(f"Could not connect to StaticInfo shared memory: {e}")
        print("Is Assetto Corsa running?")
        return None

    buf=mm.read(size)

    data=StaticInfo() #creating an empty structure for static info(reader structure)

    ctypes.memmove(ctypes.byref(data),buf,size)

    #using memmove to copy the data from struct to reader structure 
    #ctypes.byref is used for destination
    #buf is the source (raw bytes from shared memory)
    #size is the number of bytes to copy

    mm.close()

    return data 


if __name__ == "__main__":
    #run code if its being run through this file and not when imported
    #can be used as a stand alone library as well as a program 
    print("Reading data from shared memory...")

    # --- Physics ---
    physics_data = read_physics()
    if physics_data:
        print("\n=== Physics Data ===")
        print(f"  PacketId: {physics_data.PacketId}")
        print(f"  Speed: {physics_data.SpeedKmh:.1f} km/h")
        print(f"  RPM: {physics_data.Rpms}")
        print(f"  Gear: {physics_data.Gear}")
        print(f"  Gas: {physics_data.Gas:.2f}")
        print(f"  Brake: {physics_data.Brake:.2f}")
        print(f"  Fuel: {physics_data.Fuel:.1f} L")
        print(f"  SteerAngle: {physics_data.SteerAngle:.2f}")
        print(f"  TurboBoost: {physics_data.TurboBoost:.2f}")
        print(f"  AirTemp: {physics_data.AirTemp:.1f} °C")
        print(f"  RoadTemp: {physics_data.RoadTemp:.1f} °C")
        print(f"  BrakeBias: {physics_data.BrakeBias:.2f}")
        print(f"  DRS: {physics_data.Drs}  Available: {physics_data.DrsAvailable}")
        print(f"  Tyre Core Temps: FL={physics_data.TyreCoreTemperature[0]:.0f}° FR={physics_data.TyreCoreTemperature[1]:.0f}° RL={physics_data.TyreCoreTemperature[2]:.0f}° RR={physics_data.TyreCoreTemperature[3]:.0f}°")
        print(f"  Brake Temps: FL={physics_data.BrakeTemp[0]:.0f}° FR={physics_data.BrakeTemp[1]:.0f}° RL={physics_data.BrakeTemp[2]:.0f}° RR={physics_data.BrakeTemp[3]:.0f}°")
        print(f"  Tyre Pressure: FL={physics_data.WheelsPressure[0]:.1f} FR={physics_data.WheelsPressure[1]:.1f} RL={physics_data.WheelsPressure[2]:.1f} RR={physics_data.WheelsPressure[3]:.1f}")

    # --- Graphics ---
    graphics_data = read_graphics()
    if graphics_data:
        print("\n=== Graphics Data ===")
        print(f"  Status: {graphics_data.Status}")
        print(f"  Session: {graphics_data.Session}")
        print(f"  Current Time: {graphics_data.CurrentTime}")
        print(f"  Last Time: {graphics_data.LastTime}")
        print(f"  Best Time: {graphics_data.BestTime}")
        print(f"  Completed Laps: {graphics_data.CompletedLaps}")
        print(f"  Position: P{graphics_data.Position}")
        print(f"  Total Laps: {graphics_data.NumberOfLaps}")
        print(f"  Tyre Compound: {graphics_data.TyreCompound}")
        print(f"  In Pit: {graphics_data.IsInPit}")
        print(f"  Flag: {graphics_data.Flag}")

    # --- Static Info ---
    static_info_data = read_static_info()
    if static_info_data:
        print("\n=== Static Info ===")
        print(f"  Car Model: {static_info_data.CarModel}")
        print(f"  Track: {static_info_data.Track}")
        print(f"  Player: {static_info_data.PlayerName} {static_info_data.PlayerSurname}")
        print(f"  Max RPM: {static_info_data.MaxRpm}")
        print(f"  Max Fuel: {static_info_data.MaxFuel:.1f} L")
        print(f"  Max Power: {static_info_data.MaxPower:.0f} W")
        print(f"  Has DRS: {static_info_data.HasDRS}")
        print(f"  Has ERS: {static_info_data.HasERS}")
        print(f"  SM Version: {static_info_data.SMVersion}")
        print(f"  AC Version: {static_info_data.ACVersion}")

    print("\nDone!")