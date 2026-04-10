#include "SPI.h"
#include "TFT_22_ILI9225.h"
#include <math.h>

// RGB565 color conversion macro
#define RGB565(r, g, b) (((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3))

// Custom colors
#define COLOR_DIM_GRAY    RGB565(60, 60, 60)
#define COLOR_MID_GRAY    RGB565(100, 100, 100)
#define COLOR_DARK_LINE   RGB565(50, 50, 50)
#define COLOR_BORDER_GRAY RGB565(80, 80, 80)

// ESP32 VSPI Pin definitions
#define TFT_RST 4
#define TFT_RS  2
#define TFT_CS  5     // SS
#define TFT_SDI 23    // MOSI
#define TFT_CLK 18    // SCK
#define TFT_LED 0     // 0 if wired directly to 3.3V

// Initialize display
TFT_22_ILI9225 tft = TFT_22_ILI9225(TFT_RST, TFT_RS, TFT_CS, TFT_LED);

// ===================== TELEMETRY STATE =====================
int current_rpm = 0;
int max_rpm = 9000;
String current_gear_str = "0";
int current_speed = 0;
float current_brake = 0.0;
float t_FL = 0, t_FR = 0, t_RL = 0, t_RR = 0;
String current_laptime = "0:00.000";

// Previous values for flicker-free updates
int prev_speed = -1;
int prev_rpm = -1;
String prev_gear_str = "";

// Demo mode: animate gauges when no serial data
unsigned long lastDataTime = 0;
bool demoMode = true;
int demoStep = 0;
const int DEMO_TIMEOUT_MS = 3000; // enter demo after 3s of no data

// ===================== HELPERS =====================
String padLeft(String str, int len, char padChar = ' ') {
  while (str.length() < len) str = String(padChar) + str;
  return str;
}

// Draw an arc (sweep) from startAngle to endAngle at (cx,cy) with radius r
// Angles in degrees, 0 = top (12 o'clock), clockwise
void drawArc(int cx, int cy, int r, float startAngle, float endAngle, uint16_t color) {
  // Convert to radians, offset so 0° = top
  float step = 2.0; // degree step — smaller = smoother but slower
  for (float a = startAngle; a <= endAngle; a += step) {
    float rad = (a - 90.0) * PI / 180.0;
    int x = cx + (int)(r * cos(rad));
    int y = cy + (int)(r * sin(rad));
    tft.drawPixel(x, y, color);
  }
}

// Draw a thick arc (multiple radii)
void drawThickArc(int cx, int cy, int r, int thickness, float startAngle, float endAngle, uint16_t color) {
  for (int t = 0; t < thickness; t++) {
    drawArc(cx, cy, r - t, startAngle, endAngle, color);
  }
}

// Draw tick marks around the arc
void drawTick(int cx, int cy, int rOuter, int rInner, float angle, uint16_t color) {
  float rad = (angle - 90.0) * PI / 180.0;
  int x1 = cx + (int)(rOuter * cos(rad));
  int y1 = cy + (int)(rOuter * sin(rad));
  int x2 = cx + (int)(rInner * cos(rad));
  int y2 = cy + (int)(rInner * sin(rad));
  tft.drawLine(x1, y1, x2, y2, color);
}

// Draw a needle from center to edge of gauge
void drawNeedle(int cx, int cy, int r, float angle, uint16_t color) {
  float rad = (angle - 90.0) * PI / 180.0;
  int x = cx + (int)(r * cos(rad));
  int y = cy + (int)(r * sin(rad));
  tft.drawLine(cx, cy, x, y, color);
}

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10); // Fast timeout for responsiveness

  tft.begin();
  tft.setOrientation(1); // 1 = Landscape (Horizontal) 220x176
  tft.clear();

  tft.setFont(Terminal12x16);
  tft.drawText(10, 100, "WAITING DATA", COLOR_WHITE);

  // Draw static UI elements once
  drawStaticUI();
}

// ===================== LOOP =====================
void loop() {
  // Check if Python script sent data over USB
  // Format: R<rpm>,M<max_rpm>,G<gear_str>,S<speed>,L<laptime>,B<brake>,T<fl,fr,rl,rr>\n
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); 
    
    if (data.startsWith("R")) {
      parseData(data);
      updateDynamicUI();
      lastDataTime = millis();
      demoMode = false;
    }
  }

  // Demo mode: animate gauges when no serial data arrives
  if (!demoMode && (millis() - lastDataTime > DEMO_TIMEOUT_MS)) {
    demoMode = true;
    demoStep = 0;
  }

  if (demoMode) {
    runDemoMode();
    delay(40); // ~25 FPS demo
  }
}

// ===================== DATA PARSER =====================
void parseData(String data) {
  int i_M = data.indexOf(",M");
  int i_G = data.indexOf(",G");
  int i_S = data.indexOf(",S");
  int i_L = data.indexOf(",L");
  int i_B = data.indexOf(",B");
  int i_T = data.indexOf(",T");
  int i_F = data.indexOf(",F");
    
  if(i_M > 0 && i_G > 0 && i_S > 0 && i_L > 0 && i_B > 0 && i_T > 0) {
    current_rpm = data.substring(1, i_M).toInt();
    max_rpm = data.substring(i_M + 2, i_G).toInt();
    if(max_rpm == 0) max_rpm = 9000;
      
    // Parse gear and TRIM to remove any garbage/whitespace/null bytes
    current_gear_str = data.substring(i_G + 2, i_S);
    current_gear_str.trim();  // Remove leading/trailing whitespace & control chars
    // Map letters to numbers (font may not support letters)
    if (current_gear_str == "N") current_gear_str = "0";
    else if (current_gear_str == "R") current_gear_str = "-1";
    // Extra safety: only keep first printable character(s)
    if (current_gear_str.length() > 2) {
      current_gear_str = current_gear_str.substring(0, 2);
    }

    current_speed = data.substring(i_S + 2, i_L).toInt();
    current_laptime = data.substring(i_L + 2, i_B);
    current_brake = data.substring(i_B + 2, i_T).toFloat();
      
    // Parse Tyres (FL,FR,RL,RR) e.g., "T85.5,86.2,90.1,91.0"
    String tyreStr = data.substring(i_T + 2, (i_F > 0) ? i_F : data.length());
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

// ===================== DEMO MODE =====================
void runDemoMode() {
  demoStep++;
  
  // Sweep RPM: 0 → max → 0 over ~200 steps (8 seconds at 25fps)
  int rpmCycle = demoStep % 200;
  if (rpmCycle < 100) {
    current_rpm = (rpmCycle * max_rpm) / 100;
  } else {
    current_rpm = ((200 - rpmCycle) * max_rpm) / 100;
  }

  // Sweep Speed: 0 → 300 → 0 over ~200 steps
  int speedCycle = (demoStep + 50) % 200; // Offset so it doesn't sync exactly with RPM
  if (speedCycle < 100) {
    current_speed = (speedCycle * 300) / 100;
  } else {
    current_speed = ((200 - speedCycle) * 300) / 100;
  }

  // Cycle through gears based on RPM
  if (current_rpm < max_rpm * 0.15)      current_gear_str = "0";  // Neutral
  else if (current_rpm < max_rpm * 0.30) current_gear_str = "1";
  else if (current_rpm < max_rpm * 0.45) current_gear_str = "2";
  else if (current_rpm < max_rpm * 0.60) current_gear_str = "3";
  else if (current_rpm < max_rpm * 0.75) current_gear_str = "4";
  else if (current_rpm < max_rpm * 0.90) current_gear_str = "5";
  else                                   current_gear_str = "6";

  current_laptime = "DEMO";
  
  updateDynamicUI();
}

// =========================================================
//  SPEEDO UI
// =========================================================
// Gauge arc parameters
#define SPEED_CX 55
#define SPEED_CY 65
#define SPEED_R  42

#define RPM_CX   165
#define RPM_CY   65
#define RPM_R    42

// Arc sweep range: 225° total sweep from 135° to 360° (+ 45° past 0°)
// In our coordinate system: 0° = top, clockwise
// Start = 225° (7.5 o'clock), End = 315+90 = 135° (4.5 o'clock going CW through bottom)
// We'll use 135° to 405° (i.e. 135 → 360 → 45 wrapped)
#define GAUGE_START 135.0
#define GAUGE_END   405.0
#define GAUGE_SWEEP (GAUGE_END - GAUGE_START) // 270°

// Stored previous needle angles to erase only the needle
float prev_speed_angle = GAUGE_START;
float prev_rpm_angle = GAUGE_START;

void drawGaugeFace(int cx, int cy, int r, const char* label, int maxVal, int step) {
  // Draw background arc (dark track)
  drawThickArc(cx, cy, r, 4, GAUGE_START, GAUGE_END, COLOR_DIM_GRAY);

  // Draw tick marks
  int numTicks = maxVal / step;
  for (int i = 0; i <= numTicks; i++) {
    float angle = GAUGE_START + ((float)i / numTicks) * GAUGE_SWEEP;
    drawTick(cx, cy, r + 2, r - 6, angle, COLOR_WHITE);
  }

  // Draw minor ticks (half-way between major ticks, shorter)
  for (int i = 0; i < numTicks; i++) {
    float angle = GAUGE_START + ((float)i + 0.5) / numTicks * GAUGE_SWEEP;
    drawTick(cx, cy, r + 1, r - 3, angle, COLOR_MID_GRAY);
  }

  // Label below gauge
  tft.setFont(Terminal6x8);
  int labelX = cx - (strlen(label) * 3); // Approx center
  tft.drawText(labelX, cy + r - 15, label, COLOR_LIGHTGRAY);

  // Center dot
  tft.fillCircle(cx, cy, 3, COLOR_WHITE);
}

void drawStaticUI() {
  tft.clear();
  
  // — Header bar —
  tft.setFont(Terminal6x8);
  tft.drawText(80, 2, "TELEMETRY", COLOR_MID_GRAY);
  tft.drawLine(0, 12, 219, 12, COLOR_DARK_LINE);

  // — Speed Gauge Face (left) —
  drawGaugeFace(SPEED_CX, SPEED_CY, SPEED_R, "KM/H", 300, 50);

  // — RPM Gauge Face (right) —
  drawGaugeFace(RPM_CX, RPM_CY, RPM_R, "RPM", max_rpm, max_rpm / 6);

  // — Red zone arc on RPM (last 15%) —
  float redStart = GAUGE_START + GAUGE_SWEEP * 0.85;
  drawThickArc(RPM_CX, RPM_CY, RPM_R, 4, redStart, GAUGE_END, COLOR_RED);

  // — Gear box (centre, between gauges) —
  int gearBoxX = 90;
  int gearBoxY = 40;
  int gearBoxW = 40;
  int gearBoxH = 40;
  tft.drawRectangle(gearBoxX, gearBoxY, gearBoxX + gearBoxW, gearBoxY + gearBoxH, COLOR_BORDER_GRAY);
  tft.setFont(Terminal6x8);
  tft.drawText(100, 42, "GEAR", COLOR_MID_GRAY);

  // — Divider line —
  tft.drawLine(0, 120, 219, 120, COLOR_DARK_LINE);

  // — Bottom labels —
  tft.setFont(Terminal6x8);
  tft.drawText(5, 128, "SPD", COLOR_MID_GRAY);
  tft.drawText(5, 142, "RPM", COLOR_MID_GRAY);
  tft.drawText(5, 156, "LAP", COLOR_MID_GRAY);

  // Reset needle tracking
  prev_speed_angle = GAUGE_START;
  prev_rpm_angle = GAUGE_START;
  prev_speed = -1;
  prev_rpm = -1;
  prev_gear_str = "";
}

void updateDynamicUI() {
  // ========== SPEED GAUGE ==========
  float speed_ratio = (float)current_speed / 300.0;
  if (speed_ratio > 1.0) speed_ratio = 1.0;
  float speed_angle = GAUGE_START + speed_ratio * GAUGE_SWEEP;

  if (current_speed != prev_speed) {
    // Erase old needle
    drawNeedle(SPEED_CX, SPEED_CY, SPEED_R - 8, prev_speed_angle, COLOR_BLACK);
    // Redraw center dot
    tft.fillCircle(SPEED_CX, SPEED_CY, 3, COLOR_WHITE);
    // Draw new needle
    uint16_t needleColor = COLOR_GREEN;
    if (speed_ratio > 0.8) needleColor = COLOR_YELLOW;
    drawNeedle(SPEED_CX, SPEED_CY, SPEED_R - 8, speed_angle, needleColor);
    prev_speed_angle = speed_angle;

    // Update speed number at bottom
    tft.fillRectangle(30, 128, 100, 138, COLOR_BLACK);
    tft.setFont(Terminal6x8);
    tft.drawText(30, 128, padLeft(String(current_speed), 3) + " KM/H", COLOR_WHITE);

    prev_speed = current_speed;
  }

  // ========== RPM GAUGE ==========
  float rpm_ratio = (float)current_rpm / max_rpm;
  if (rpm_ratio > 1.0) rpm_ratio = 1.0;
  float rpm_angle = GAUGE_START + rpm_ratio * GAUGE_SWEEP;

  if (current_rpm != prev_rpm) {
    // Erase old needle
    drawNeedle(RPM_CX, RPM_CY, RPM_R - 8, prev_rpm_angle, COLOR_BLACK);
    // Redraw center dot
    tft.fillCircle(RPM_CX, RPM_CY, 3, COLOR_WHITE);
    // Draw new needle with color zones
    uint16_t needleColor = COLOR_GREEN;
    if (rpm_ratio > 0.7) needleColor = COLOR_YELLOW;
    if (rpm_ratio > 0.9) needleColor = COLOR_RED;
    drawNeedle(RPM_CX, RPM_CY, RPM_R - 8, rpm_angle, needleColor);
    prev_rpm_angle = rpm_angle;

    // Update RPM number at bottom
    tft.fillRectangle(30, 142, 110, 152, COLOR_BLACK);
    tft.setFont(Terminal6x8);
    tft.drawText(30, 142, padLeft(String(current_rpm), 5) + " RPM", COLOR_WHITE);

    prev_rpm = current_rpm;
  }

  // ========== GEAR (centre) ==========
  if (current_gear_str != prev_gear_str) {
    // Clear ENTIRE gear box interior to kill any leftover green pixels
    tft.fillRectangle(91, 41, 129, 79, COLOR_BLACK);
    // Redraw the border and label since we cleared the whole box
    tft.drawRectangle(90, 40, 130, 80, COLOR_BORDER_GRAY);
    tft.setFont(Terminal6x8);
    tft.drawText(100, 42, "GEAR", COLOR_MID_GRAY);

    // Draw gear character — big font
    tft.setFont(Trebuchet_MS16x21);
    
    // Color based on gear — COMMENTED OUT FOR TESTING
    uint16_t gearColor = COLOR_WHITE;
    // if (current_gear_str == "N") gearColor = COLOR_GREEN;
    // else if (current_gear_str == "R") gearColor = COLOR_RED;
    
    // Center the text in the box — use c_str() to avoid garbage from String object
    int gearX = 102;
    int gearY = 55;
    tft.drawText(gearX, gearY, current_gear_str, gearColor);

    prev_gear_str = current_gear_str;
  }

  // ========== LAP TIME (bottom) ==========
  tft.fillRectangle(30, 156, 170, 166, COLOR_BLACK);
  tft.setFont(Terminal6x8);
  tft.drawText(30, 156, current_laptime, COLOR_YELLOW);
}
