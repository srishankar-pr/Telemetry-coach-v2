# 🔌 Hardware Integration: ILI9225 2.0" TFT Display with ESP32

To move the telemetry off your main monitor and onto a physical display, you can use your **ESP32** connected via USB to your PC. 

The PC Python script will read Assetto Corsa data and send it over USB Serial to the ESP32, which will draw the UI on the 2-inch ILI9225 TFT.

---

## 1. Wiring the ILI9225 to an ESP32

The ESP32 is perfect for this because both the ESP32 and the ILI9225 use **3.3V logic**. You can connect the pins directly without any logic level shifters!

The ESP32 has multiple hardware SPI buses. The standard one used for displays is the **VSPI bus**.

| ILI9225 Pin | ESP32 Pin (VSPI) | Function |
|---|---|---|
| **VCC/5V** | 3V3 | Power supply (ESP32 3.3V out) |
| **GND** | GND | Ground |
| **SCL / SCK** | GPIO 18 | SPI Clock |
| **SDA / MOSI**| GPIO 23 | SPI Data Out (Master Out Slave In) |
| **CS** | GPIO 5 | Chip Select |
| **RS / DC** | GPIO 2 | Data / Command register select |
| **RST** | GPIO 4 | Reset pin |
| **LED** | 3V3 (or GPIO 12)* | Backlight power *(connect to a GPIO if you want PWM brightness control)* |

> *Note: If connecting `LED` directly to 3V3 is too bright, use a 100Ω resistor or connect it to an ESP32 PWM pin.*

---

## 2. The Python PC Side (Sender)

Your existing Python app uses `ac_reader.py` to get the telemetry. We will add `pyserial` to send a compressed data packet over USB 10 times per second.

Instead of sending JSON (which is heavy for the ESP32 to string-parse), we send a compact comma-separated string: `S240,R11500,G4\n`

### Example Snippet (PC side)
```python
# pip install pyserial
import serial
import time
import ac_reader

# Connect to the ESP32 (Replace COM3 with your actual port from Device Manager)
esp32 = serial.Serial('COM3', 115200, timeout=0.1)
time.sleep(2) # Wait for ESP32 to reset

def send_telemetry():
    physics = ac_reader.read_physics()
    if physics:
        speed = int(physics.SpeedKmh)
        rpm = int(physics.Rpms)
        gear = physics.Gear
        
        # Format: S<speed>,R<rpm>,G<gear>\n
        packet = f"S{speed},R{rpm},G{gear}\n"
        esp32.write(packet.encode('ascii'))
```

---

## 3. The ESP32 Side (Receiver & Display)

To drive the display on an ESP32, you can use the `TFT_22_ILI9225` library (install via Arduino Library Manager). 

The ESP32 constantly reads the Serial port via USB. When it sees new data, it parses the integers and updates the TFT blazingly fast thanks to its 240MHz dual-core processor.

### Example ESP32 Sketch (Arduino IDE)

```cpp
#include "SPI.h"
#include "TFT_22_ILI9225.h"

// ESP32 VSPI Pin definitions
#define TFT_RST 4
#define TFT_RS  2
#define TFT_CS  5     // SS
#define TFT_SDI 23    // MOSI
#define TFT_CLK 18    // SCK
#define TFT_LED 0     // 0 if wired directly to 3V3, otherwise a GPIO pin

// Initialize display (Uses hardware SPI automatically)
TFT_22_ILI9225 tft = TFT_22_ILI9225(TFT_RST, TFT_RS, TFT_CS, TFT_LED);

int current_speed = 0;
int current_rpm = 0;
int current_gear = 0;

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10); // Fast timeout for responsive parsing
  
  tft.begin();
  tft.setOrientation(1); // Landscape
  tft.clear();
  
  tft.setFont(Terminal12x16);
  tft.drawText(10, 10, "WAITING FOR AC...", COLOR_WHITE);
}

void loop() {
  // Check if Python script sent data over USB
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); // Read until newline
    
    // Simple parsing: expects "S240,R11500,G4"
    if (data.startsWith("S")) {
      int s_idx = data.indexOf('S');
      int r_idx = data.indexOf(",R");
      int g_idx = data.indexOf(",G");
      
      if (r_idx > 0 && g_idx > 0) {
        current_speed = data.substring(s_idx + 1, r_idx).toInt();
        current_rpm   = data.substring(r_idx + 2, g_idx).toInt();
        current_gear  = data.substring(g_idx + 2).toInt();
        
        updateDisplay();
      }
    }
  }
}

void updateDisplay() {
  // Clear the area where numbers are drawn to avoid overlapping text
  // ESP32 is fast enough to do this without noticeable flickering
  tft.fillRectangle(10, 40, 200, 100, COLOR_BLACK);
  
  String speedStr = "Speed: " + String(current_speed) + " km/h";
  String rpmStr   = "RPM: " + String(current_rpm);
  
  String gearStr;
  if(current_gear == 0) gearStr = "R";
  else if (current_gear == 1) gearStr = "N";
  else gearStr = String(current_gear - 1);
  
  tft.drawText(10, 40, speedStr, COLOR_GREEN);
  tft.drawText(10, 60, rpmStr, COLOR_YELLOW);
  tft.drawText(10, 80, "Gear: " + gearStr, COLOR_RED);
}
```

---

## 💡 Next Steps for Building This
1. **Wire it up:** Connect the 5 SPI pins, 3.3V power, and ground from the display to your ESP32.
2. **Library Installation:** Open Arduino IDE -> Sketch -> Include Library -> Manage Libraries. Search for `TFT_22_ILI9225` and install it.
3. **Test the display:** Run one of the built-in Examples from the `TFT_22_ILI9225` library in the Arduino IDE to verify your wiring is correct. (You may need to change the pin definitions at the top of the example sketch to match the ESP32 pins above).
4. **Write the integration:** Use the sketch above, and run a Python script to push fake telemetry matching the `S240,R11000,G3\n` format to test the serial parser!
