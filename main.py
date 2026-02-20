import time #to set refresh times
import ac_reader #to read the data from shared memory 


#static info doesnt change and  hence no need to refresh 

static=ac_reader.read_static_info() #ctypes Strucutre 
#storing the static info as  a ctypes structure 

if static:
    print(f"Car:{static.CarModel}")
    print(f"Track:{static.Track}")
    print(f"Max RPM:{static.MaxRpm}")
    print(f"Max Fuel:{static.MaxFuel:.1f} L")
    print(f"Max Power:{static.MaxPower:.0f} W")


#reading the physics info  and graphic 

while True:
    p=ac_reader.read_physics()
    g=ac_reader.read_graphics()
    if p and g:
        print(f"Speed:{p.SpeedKmh:.1f} km/h | RPM:{p.Rpms} | Gear:{p.Gear}")
        time.sleep(3) #approx 60fps
    else:
        print("Waiting for AC to start...")
        time.sleep(1)