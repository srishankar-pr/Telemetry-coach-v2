#include "SPI.h"
#include "TFT_22_ILI9225.h"

// GFX font only for gear display (supports both letters and numbers cleanly)
#include <../fonts/FreeSansBold18pt7b.h>

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
String current_gear_str = "N";
int current_speed = 0;
float current_brake = 0.0;
float t_FL = 0, t_FR = 0, t_RL = 0, t_RR = 0;
String current_laptime = "0:00.000";
float g_lat = 0.0;   // lateral G-force (left/right)
float g_lon = 0.0;   // longitudinal G-force (accel/brake)

// Previous G-force dot position for flicker-free erase
int prev_gx = -1;
int prev_gy = -1;

// G-Force graph constants
#define GF_CX 133     // center X of G-force graph
#define GF_CY 178     // center Y
#define GF_R  30      // radius of the graph circle
#define GF_MAX_G 3.0  // max G-force shown on graph

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  
  tft.begin();
  tft.setOrientation(0); // Portrait 176x220
  tft.clear();
  
  tft.setFont(Terminal12x16);
  tft.drawText(10, 100, "WAITING DATA", COLOR_WHITE);

  drawStaticUI();
}

// ===================== LOOP =====================
void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n'); 
    
    if (data.startsWith("R")) {
      parseData(data);
      updateDynamicUI();
    }
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
  int i_A = data.indexOf(",A");
    
  if(i_M > 0 && i_G > 0 && i_S > 0 && i_L > 0 && i_B > 0 && i_T > 0) {
    current_rpm = data.substring(1, i_M).toInt();
    max_rpm = data.substring(i_M + 2, i_G).toInt();
    if(max_rpm == 0) max_rpm = 9000;
      
    current_gear_str = data.substring(i_G + 2, i_S);
    current_speed = data.substring(i_S + 2, i_L).toInt();
    current_laptime = data.substring(i_L + 2, i_B);
    current_brake = data.substring(i_B + 2, i_T).toFloat();
      
    // Parse Tyres (FL,FR,RL,RR)
    String tyreStr = data.substring(i_T + 2, (i_F > 0) ? i_F : ((i_A > 0) ? i_A : data.length()));
    int t1 = tyreStr.indexOf(',');
    int t2 = tyreStr.indexOf(',', t1+1);
    int t3 = tyreStr.indexOf(',', t2+1);
      
    if(t1>0 && t2>0 && t3>0) {
      t_FL = tyreStr.substring(0, t1).toFloat();
      t_FR = tyreStr.substring(t1+1, t2).toFloat();
      t_RL = tyreStr.substring(t2+1, t3).toFloat();
      t_RR = tyreStr.substring(t3+1).toFloat();
    }

    // Parse G-force: A<lateral>,<longitudinal>
    if(i_A > 0) {
      String gStr = data.substring(i_A + 2);
      int gComma = gStr.indexOf(',');
      if(gComma > 0) {
        g_lat = gStr.substring(0, gComma).toFloat();
        g_lon = gStr.substring(gComma + 1).toFloat();
      }
    }
  }
}

// =========================================================
//  RACE HUD UI
// =========================================================
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
  
  // --- Bottom Left: Tyres (compact 2x2 grid) ---
  tft.drawRectangle(5, 130, 95, 218, COLOR_DARKGRAY);
  tft.drawText(10, 135, "TYRES", COLOR_LIGHTGRAY);
  // Labels for the 2x2 grid
  tft.drawText(10, 150, "FL", COLOR_LIGHTGRAY);
  tft.drawText(52, 150, "FR", COLOR_LIGHTGRAY);
  tft.drawText(10, 190, "RL", COLOR_LIGHTGRAY);
  tft.drawText(52, 190, "RR", COLOR_LIGHTGRAY);

  // --- Bottom Right: G-Force graph ---
  tft.drawRectangle(100, 130, 170, 218, COLOR_DARKGRAY);
  tft.drawText(105, 135, "G-FORCE", COLOR_LIGHTGRAY);
  
  // Draw crosshair circle and lines
  drawGForceStatic();
}

void drawGForceStatic() {
  // Outer circle
  tft.drawCircle(GF_CX, GF_CY, GF_R, COLOR_DARKGRAY);
  // Inner circle (1G reference)
  tft.drawCircle(GF_CX, GF_CY, GF_R / 3, COLOR_DARKGRAY);
  // Crosshair lines
  tft.drawLine(GF_CX - GF_R, GF_CY, GF_CX + GF_R, GF_CY, COLOR_DARKGRAY);  // horizontal
  tft.drawLine(GF_CX, GF_CY - GF_R, GF_CX, GF_CY + GF_R, COLOR_DARKGRAY);  // vertical
}

void updateDynamicUI() {
  // --- 1. RPM BAR ---
  float rpm_ratio = (float)current_rpm / max_rpm;
  if(rpm_ratio > 1.0) rpm_ratio = 1.0;
  
  tft.fillRectangle(5, 15, 171, 26, COLOR_BLACK); 
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
      tft.fillCircle(cx, cy, r, COLOR_DARKGRAY);
    }
  }
  
  // --- 2. GEAR (GFX font) & SPEED ---
  tft.fillRectangle(15, 45, 65, 90, COLOR_BLACK); 
  tft.setGFXFont(&FreeSansBold18pt7b);
  tft.drawGFXText(25, 82, current_gear_str, COLOR_WHITE);
  
  tft.setFont(Terminal6x8); 
  tft.fillRectangle(10, 105, 70, 115, COLOR_BLACK); 
  tft.drawText(20, 105, String(current_speed), COLOR_WHITE);
  
  // --- 3. LAPTIME ---
  tft.setFont(Terminal6x8); 
  tft.fillRectangle(95, 45, 165, 65, COLOR_BLACK);
  tft.drawText(95, 50, current_laptime, COLOR_YELLOW);
  
  // --- 4. BRAKE PRESSURE BAR ---
  int max_brk_width = 70;
  int brk_width = (int)(current_brake * max_brk_width); 
  tft.fillRectangle(90, 100, 90 + brk_width, 110, COLOR_RED);
  tft.fillRectangle(90 + brk_width + 1, 100, 90 + max_brk_width, 110, COLOR_BLACK);
  
  // --- 5. TYRES (compact 2x2 in bottom-left) ---
  tft.setFont(Terminal6x8);

  auto getSimpleTempColor = [](float t) -> uint16_t {
    if(t < 75.0) return COLOR_BLUE; 
    return COLOR_GREEN;             
  };

  // FL
  tft.fillRectangle(10, 160, 45, 170, COLOR_BLACK);
  tft.fillRectangle(10, 172, 45, 177, getSimpleTempColor(t_FL));
  tft.drawText(10, 162, String((int)t_FL) + "c", getSimpleTempColor(t_FL));

  // FR
  tft.fillRectangle(52, 160, 88, 170, COLOR_BLACK);
  tft.fillRectangle(52, 172, 88, 177, getSimpleTempColor(t_FR));
  tft.drawText(52, 162, String((int)t_FR) + "c", getSimpleTempColor(t_FR));

  // RL
  tft.fillRectangle(10, 200, 45, 210, COLOR_BLACK);
  tft.fillRectangle(10, 212, 45, 216, getSimpleTempColor(t_RL));
  tft.drawText(10, 202, String((int)t_RL) + "c", getSimpleTempColor(t_RL));

  // RR
  tft.fillRectangle(52, 200, 88, 210, COLOR_BLACK);
  tft.fillRectangle(52, 212, 88, 216, getSimpleTempColor(t_RR));
  tft.drawText(52, 202, String((int)t_RR) + "c", getSimpleTempColor(t_RR));

  // --- 6. G-FORCE GRAPH (bottom-right) ---
  updateGForce();
}

void updateGForce() {
  // Erase previous dot
  if(prev_gx >= 0 && prev_gy >= 0) {
    tft.fillCircle(prev_gx, prev_gy, 3, COLOR_BLACK);
    
    // Redraw any crosshair lines/circles the dot may have overlapped
    // Only redraw the small area around the old dot
    // Horizontal crosshair segment near old dot
    if(abs(prev_gy - GF_CY) <= 3) {
      tft.drawLine(prev_gx - 4, GF_CY, prev_gx + 4, GF_CY, COLOR_DARKGRAY);
    }
    // Vertical crosshair segment near old dot
    if(abs(prev_gx - GF_CX) <= 3) {
      tft.drawLine(GF_CX, prev_gy - 4, GF_CX, prev_gy + 4, COLOR_DARKGRAY);
    }
  }

  // Calculate new dot position
  // Lateral G → X axis (positive = right turn = dot goes right)
  // Longitudinal G → Y axis (positive = braking = dot goes up)
  float scale = (float)GF_R / GF_MAX_G;
  int dot_x = GF_CX + (int)(g_lat * scale);
  int dot_y = GF_CY - (int)(g_lon * scale);  // inverted: braking (positive) goes up

  // Clamp to circle bounds
  float dist = sqrt((float)(dot_x - GF_CX) * (dot_x - GF_CX) + (float)(dot_y - GF_CY) * (dot_y - GF_CY));
  if(dist > GF_R - 3) {
    float ratio = (GF_R - 3) / dist;
    dot_x = GF_CX + (int)((dot_x - GF_CX) * ratio);
    dot_y = GF_CY + (int)((dot_y - GF_CY) * ratio);
  }

  // Color based on total G magnitude
  float g_total = sqrt(g_lat * g_lat + g_lon * g_lon);
  uint16_t dotColor = COLOR_GREEN;
  if(g_total > 1.5) dotColor = COLOR_YELLOW;
  if(g_total > 2.5) dotColor = COLOR_RED;

  // Draw new dot
  tft.fillCircle(dot_x, dot_y, 3, dotColor);

  // Store for next erase
  prev_gx = dot_x;
  prev_gy = dot_y;
}
