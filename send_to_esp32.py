import serial
import time
import ac_reader

# ⚠️ CHANGE THIS to your ESP32's COM port (check Device Manager or Arduino IDE)
SERIAL_PORT = 'COM16' 
BAUD_RATE = 115200

def format_laptime(time_str):
    """Ensure lap time cuts off milliseconds cleanly for the small display."""
    if not time_str or time_str == "":
        return "0:00.0"
    # The string from AC looks like "1:23.456"
    return time_str.split('\x00')[0][:8]

def main():
    print(f"Connecting to ESP32 on {SERIAL_PORT}...")
    try:
        esp32 = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        time.sleep(2) # Wait for auto-reset
        print("Connected! Waiting for Assetto Corsa...")
    except Exception as e:
        print(f"FAILED TO CONNECT: {e}")
        return

    _max_rpm = 9000

    try:
        while True:
            physics = ac_reader.read_physics()
            static = ac_reader.read_static_info()
            graphics = ac_reader.read_graphics()
            
            if physics and static and graphics:
                if static.MaxRpm > 0:
                    _max_rpm = static.MaxRpm

                rpm = physics.Rpms
                raw_gear = physics.Gear
                if raw_gear == 0:
                    gear_str = "R"
                elif raw_gear == 1:
                    gear_str = "N"
                else:
                    gear_str = str(raw_gear - 1)
                
                speed = int(physics.SpeedKmh)
                brake = physics.Brake # 0.0 to 1.0
                laptime = format_laptime(graphics.CurrentTime)
                
                # Tyre Core Temps [FL, FR, RL, RR]
                t_fl = physics.TyreCoreTemperature[0]
                t_fr = physics.TyreCoreTemperature[1]
                t_rl = physics.TyreCoreTemperature[2]
                t_rr = physics.TyreCoreTemperature[3]
                
                # Fuel
                fuel = physics.Fuel
                max_fuel = static.MaxFuel

                # Format payload matching Arduino parse logic:
                # R<rpm>,M<max_rpm>,G<gear_str>,S<speed>,L<laptime>,B<brake>,T<fl,fr,rl,rr>,F<fuel,max_fuel>\n
                
                payload = f"R{rpm},M{_max_rpm},G{gear_str},S{speed},L{laptime},B{brake:.2f},T{t_fl:.1f},{t_fr:.1f},{t_rl:.1f},{t_rr:.1f},F{fuel:.1f},{max_fuel:.1f}\n"
                
                esp32.write(payload.encode('ascii'))
                print(f"Sent: {payload.strip()}")
                
            time.sleep(0.1) # 10Hz is perfect for ESP32 serial

    except KeyboardInterrupt:
        print("\nStopping telemetry sender.")
        esp32.close()

if __name__ == "__main__":
    main()
