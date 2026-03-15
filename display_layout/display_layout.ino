#include "SPI.h"
#include "TFT_22_ILI9225.h"

// ESP32 VSPI Pin definitions
#define TFT_RST 4
#define TFT_RS  2
#define TFT_CS  5     // SS
#define TFT_SDI 23    // MOSI
#define TFT_CLK 18    // SCK
#define TFT_LED 0     // 0 if wired directly to 3.3V

// Initialize display
TFT_22_ILI9225 tft = TFT_22_ILI9225(TFT_RST, TFT_RS, TFT_CS, TFT_LED);

// Telemetry State
int current_rpm = 0;
int max_rpm = 9000;
String current_gear_str = "N";
int current_speed = 0;
float current_brake = 0.0;
float t_FL = 0, t_FR = 0, t_RL = 0, t_RR = 0;
String current_laptime = "0:00.000";

// Formatting helpers
String padLeft(String str, int len, char padChar=' ') {
  while(str.length() < len) str = String(padChar) + str;
  return str;
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10); // Fast timeout for responsiveness
  
  tft.begin();
  tft.setOrientation(0); // 0 = Portrait (Vertical) usually 176x220
  tft.clear();
  
  tft.setFont(Terminal12x16);
  tft.drawText(10, 100, "WAITING DATA", COLOR_WHITE);

  // Draw static UI elements once
  drawStaticUI();
}

void drawStaticUI() {
  tft.clear();
  tft.setFont(Terminal6x8);
  
  // RPM Label
  tft.drawText(5, 5, "RPM", COLOR_LIGHTGRAY);
  
  // Gear Box
  tft.drawRectangle(5, 30, 75, 120, COLOR_DARKGRAY);
  tft.drawText(10, 35, "GEAR", COLOR_LIGHTGRAY);
  tft.drawText(10, 95, "KM/H", COLOR_LIGHTGRAY);

  // Laptime Box
  tft.drawRectangle(85, 30, 170, 70, COLOR_DARKGRAY);
  tft.drawText(90, 35, "LAP", COLOR_LIGHTGRAY);

  // Brake Box
  tft.drawRectangle(85, 80, 170, 120, COLOR_DARKGRAY);
  tft.drawText(90, 85, "BRK", COLOR_LIGHTGRAY);
  
  // Tyres Box
  tft.drawRectangle(5, 130, 170, 215, COLOR_DARKGRAY);
  tft.drawText(10, 135, "TYRES C", COLOR_LIGHTGRAY);
  
  // Car Outline (Crude top-down representation)
  tft.drawRectangle(70, 150, 105, 205, COLOR_GRAY); // Body
}

void loop() {
  // Check if Python script sent data over USB
  // Format: R<rpm>,M<max_rpm>,G<gear_str>,S<speed>,L<laptime>,B<brake>,T<fl,fr,rl,rr>\n
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); 
    
    if (data.startsWith("R")) {
      parseData(data);
      updateDynamicUI();
    }
  }
}

void parseData(String data) {
  int i_M = data.indexOf(",M");
  int i_G = data.indexOf(",G");
  int i_S = data.indexOf(",S");
  int i_L = data.indexOf(",L");
  int i_B = data.indexOf(",B");
  int i_T = data.indexOf(",T");
  
  if(i_M > 0 && i_G > 0 && i_S > 0 && i_L > 0 && i_B > 0 && i_T > 0) {
    current_rpm = data.substring(1, i_M).toInt();
    max_rpm = data.substring(i_M + 2, i_G).toInt();
    if(max_rpm == 0) max_rpm = 9000;
    
    current_gear_str = data.substring(i_G + 2, i_S);
    current_speed = data.substring(i_S + 2, i_L).toInt();
    current_laptime = data.substring(i_L + 2, i_B);
    current_brake = data.substring(i_B + 2, i_T).toFloat();
    
    // Parse Tyres (FL,FR,RL,RR) e.g., "T85.5,86.2,90.1,91.0"
    String tyreStr = data.substring(i_T + 2);
    int t1 = tyreStr.indexOf(',');
    int t2 = tyreStr.indexOf(',', t1+1);
    int t3 = tyreStr.indexOf(',', t2+1);
    
    if(t1>0 && t2>0 && t3>0) {
      t_FL = tyreStr.substring(0, t1).toFloat();
      t_FR = tyreStr.substring(t1+1, t2).toFloat();
      t_RL = tyreStr.substring(t2+1, t3).toFloat();
      t_RR = tyreStr.substring(t3+1).toFloat();
    }
  }
}

// Map value to color (Cold=Blue, Good=Green, Warm=Yellow, Hot=Red)
uint16_t getTyreColor(float temp) {
  if(temp < 60) return COLOR_BLUE;
  if(temp < 85) return COLOR_GREEN;
  if(temp < 105) return COLOR_YELLOW;
  return COLOR_RED;
}

void updateDynamicUI() {
  // --- 1. RPM BAR (Horizontal at top using small circles) ---
  float rpm_ratio = (float)current_rpm / max_rpm;
  if(rpm_ratio > 1.0) rpm_ratio = 1.0;
  
  tft.fillRectangle(5, 15, 171, 26, COLOR_BLACK); // Clear entire RPM bar area
  int num_circles = 15;
  int active_circles = (int)(rpm_ratio * num_circles);
  
  for(int i = 0; i < num_circles; i++) {
    int cx = 10 + i * 11;
    int cy = 20;
    int r = 4;
    
    if(i < active_circles) {
      uint16_t c_color = COLOR_GREEN;
      if(i >= num_circles * 0.7) c_color = COLOR_YELLOW;
      if(i >= num_circles * 0.9) c_color = COLOR_RED;
      tft.fillCircle(cx, cy, r, c_color);
    } else {
      tft.fillCircle(cx, cy, r, COLOR_DARKGRAY); // Inactive state
    }
  }
  
  // --- 2. GEAR & SPEED ---
  tft.setFont(Trebuchet_MS16x21); // Big font for gear
  tft.fillRectangle(25, 45, 55, 90, COLOR_BLACK); // Clear gear background
  tft.drawText(30, 55, current_gear_str, COLOR_WHITE);
  
  tft.setFont(Terminal6x8); // Font for speed
  tft.fillRectangle(10, 105, 70, 115, COLOR_BLACK); // Clear speed background
  tft.drawText(20, 105, String(current_speed), COLOR_WHITE);
  
  // --- 3. LAPTIME ---
  tft.setFont(Terminal6x8); // Smaller font
  tft.fillRectangle(95, 45, 165, 65, COLOR_BLACK);
  tft.drawText(95, 50, current_laptime, COLOR_YELLOW);
  
  // --- 4. BRAKE PRESSURE BAR ---
  int max_brk_width = 70;
  int brk_width = (int)(current_brake * max_brk_width); // brake is 0.0 to 1.0
  tft.fillRectangle(90, 100, 90 + brk_width, 110, COLOR_RED);
  tft.fillRectangle(90 + brk_width + 1, 100, 90 + max_brk_width, 110, COLOR_BLACK);
  
  // --- 5. TYRES ---
  tft.setFont(Terminal6x8);
  
  // Draw colored rectangles for tyres and text beside them
  
  // FL Tyre
  tft.fillRectangle(14, 150, 24, 170, getTyreColor(t_FL));
  tft.fillRectangle(28, 155, 55, 165, COLOR_BLACK);
  tft.drawText(28, 155, String((int)t_FL), COLOR_WHITE);

  // FR Tyre
  tft.fillRectangle(150, 150, 160, 170, getTyreColor(t_FR));
  tft.fillRectangle(120, 155, 145, 165, COLOR_BLACK);
  tft.drawText(120, 155, String((int)t_FR), COLOR_WHITE);

  // RL Tyre
  tft.fillRectangle(14, 180, 24, 200, getTyreColor(t_RL));
  tft.fillRectangle(28, 185, 55, 195, COLOR_BLACK);
  tft.drawText(28, 185, String((int)t_RL), COLOR_WHITE);

  // RR Tyre
  tft.fillRectangle(150, 180, 160, 200, getTyreColor(t_RR));
  tft.fillRectangle(120, 185, 145, 195, COLOR_BLACK);
  tft.drawText(120, 185, String((int)t_RR), COLOR_WHITE);
}
