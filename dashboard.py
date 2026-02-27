import tkinter as tk
import ac_reader
import math

# ─── Window setup ─────────────────────────────────────────────────────────────
BASE_W, BASE_H = 500, 300
root = tk.Tk()
root.title("AC Telemetry — F1 Wheel")
root.geometry(f"{BASE_W}x{BASE_H}")
root.minsize(400, 240)
root.configure(bg="#0a0a0a")

canvas = tk.Canvas(root, bg="#0a0a0a", highlightthickness=0, bd=0)
canvas.pack(fill="both", expand=True)

# ─── Color palette ────────────────────────────────────────────────────────────
BG           = "#0a0a0a"
PANEL_BG     = "#111111"
PANEL_BG2    = "#141414"
BORDER       = "#222222"
ACCENT_RED   = "#e10600"
ACCENT_GREEN = "#00d43a"
ACCENT_BLUE  = "#0090ff"
ACCENT_YELLOW= "#ffcc00"
TEXT_DIM     = "#f0f0f0"
TEXT_MID     = "#f0f0f0"
TEXT_BRIGHT  = "#f0f0f0"
TEXT_WHITE   = "#f0f0f0"

# ─── RPM config ──────────────────────────────────────────────────────────────
RPM_DOTS = 30


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def rpm_dot_color(i, total):
    ratio = i / total
    if ratio < 0.5:
        r = int(ratio * 2 * 255); g = 220
    elif ratio < 0.8:
        r = 255; g = int(220 - (ratio - 0.5) / 0.3 * 170)
    else:
        r = 255; g = int(50 - (ratio - 0.8) / 0.2 * 50)
    return f"#{r:02x}{max(0, g):02x}00"


def tyre_color(temp):
    if temp < 60:   return ACCENT_BLUE
    if temp < 80:   return ACCENT_GREEN
    if temp < 100:  return ACCENT_YELLOW
    return ACCENT_RED


def brake_color(temp):
    if temp < 400:  return ACCENT_GREEN
    if temp < 600:  return ACCENT_YELLOW
    return ACCENT_RED


def draw_rounded_rect(x1, y1, x2, y2, r, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
           x2,y2-r, x2,y2, x2-r,y2,
           x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def panel(x, y, w, h, bg=PANEL_BG):
    draw_rounded_rect(x, y, x+w, y+h, 4, fill=bg, outline=BORDER, width=1)


def font(base, W, bold=False):
    return ("Consolas", max(6, int(base * W / BASE_W)), "bold" if bold else "")


# ═══════════════════════════════════════════════════════════════════════════════
#  LAYOUT COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════════

def layout(W, H):
    M = max(4, int(W * 0.012))          # outer margin
    G = max(3, int(W * 0.007))          # gap between panels

    # RPM row
    dot_r  = max(3, int(W * 0.009))
    rpm_y  = dot_r + 5
    sep_y  = rpm_y + dot_r + 5          # separator line under dots

    # Bottom bar
    bar_h  = max(24, int(H * 0.085))
    bot_y  = H - bar_h - 3             # 3 px for red accent

    # Usable vertical space between separator and bottom bar
    body_h = bot_y - sep_y - G * 3     # subtract gaps
    r1_h   = int(body_h * 0.58)
    r2_h   = body_h - r1_h

    r1_y = sep_y + G
    r2_y = r1_y + r1_h + G

    # Three columns
    c1_w = int(W * 0.20)               # speed / pedals
    c3_w = int(W * 0.36)               # g-force / fuel
    c2_w = W - 2*M - c1_w - c3_w - 2*G # gear / tyres

    c1_x = M
    c2_x = M + c1_w + G
    c3_x = W - M - c3_w

    return dict(
        W=W, H=H, M=M, G=G,
        dot_r=dot_r, rpm_y=rpm_y, sep_y=sep_y,
        r1_y=r1_y, r1_h=r1_h, r2_y=r2_y, r2_h=r2_h, bot_y=bot_y, bar_h=bar_h,
        c1_x=c1_x, c1_w=c1_w,
        c2_x=c2_x, c2_w=c2_w,
        c3_x=c3_x, c3_w=c3_w,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  DRAWING
# ═══════════════════════════════════════════════════════════════════════════════

def draw_frame(L):
    W = L["W"]
    canvas.create_rectangle(0, 0, 4, 22, fill=ACCENT_RED, outline="")
    canvas.create_rectangle(W-4, 0, W, 22, fill=ACCENT_RED, outline="")
    canvas.create_line(L["M"], L["sep_y"], W - L["M"], L["sep_y"],
                       fill=BORDER, width=1)


def draw_rpm(rpm, max_rpm, L):
    W = L["W"]
    if max_rpm <= 0: max_rpm = 9000
    ratio = min(rpm / max_rpm, 1.0)
    lit = int(ratio * RPM_DOTS)
    r = L["dot_r"]
    cy = L["rpm_y"]
    pad_r = max(36, int(W * 0.08))
    span = W - L["M"] - 6 - pad_r
    step = span / max(RPM_DOTS - 1, 1)

    for i in range(RPM_DOTS):
        cx = L["M"] + 6 + i * step
        c = rpm_dot_color(i, RPM_DOTS) if i < lit else "#1a1a1a"
        if ratio > 0.85 and i < lit and i >= lit - 3:
            canvas.create_oval(cx-r-2, cy-r-2, cx+r+2, cy+r+2,
                               fill="", outline=c, width=1)
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill=c, outline="")

    canvas.create_text(W - 6, cy, text=str(rpm), fill=TEXT_MID,
                       font=font(8, W), anchor="e")


# ── Row 1 ─────────────────────────────────────────────────────────────────────

def draw_speed(speed, L):
    x, y, w, h = L["c1_x"], L["r1_y"], L["c1_w"], L["r1_h"]
    panel(x, y, w, h)
    cx = x + w//2
    canvas.create_text(cx, y + 8, text="KM/H", fill=TEXT_DIM,
                       font=font(7, L["W"]), anchor="center")
    canvas.create_text(cx, y + h//2 + 6, text=f"{speed:.0f}",
                       fill=ACCENT_GREEN, font=font(26, L["W"], True), anchor="center")


def draw_gear(gear, L):
    x, y, w, h = L["c2_x"], L["r1_y"], L["c2_w"], L["r1_h"]
    panel(x, y, w, h, PANEL_BG2)
    cx = x + w//2
    g = "R" if gear == 0 else ("N" if gear == 1 else str(gear - 1))
    canvas.create_text(cx, y + 8, text="GEAR", fill=TEXT_DIM,
                       font=font(7, L["W"]), anchor="center")
    canvas.create_text(cx, y + h//2 + 8, text=g, fill=TEXT_WHITE,
                       font=font(44, L["W"], True), anchor="center")


def draw_gforce(acc_g, air_t, road_t, brk_t, turbo, L):
    x, y, w, h = L["c3_x"], L["r1_y"], L["c3_w"], L["r1_h"]
    W = L["W"]
    panel(x, y, w, h)

    ft = font(7, W)
    fv = font(9, W, True)
    pad = 8

    # ── G-force crosshair (left portion) ──
    # Use roughly 45% of panel width for the g-force circle
    gf_diam = min(int(w * 0.42), h - 28)
    gf_r = gf_diam // 2
    gf_cx = x + pad + gf_r + 2
    gf_cy = y + 14 + gf_r

    canvas.create_text(gf_cx, y + 5, text="G-FORCE", fill=TEXT_DIM,
                       font=ft, anchor="center")

    # Outer ring
    canvas.create_oval(gf_cx-gf_r, gf_cy-gf_r, gf_cx+gf_r, gf_cy+gf_r,
                       fill="#0e0e0e", outline=BORDER, width=1)
    # Crosshairs
    canvas.create_line(gf_cx-gf_r, gf_cy, gf_cx+gf_r, gf_cy, fill="#1a1a1a")
    canvas.create_line(gf_cx, gf_cy-gf_r, gf_cx, gf_cy+gf_r, fill="#1a1a1a")
    # 1G ring
    ir = gf_r // 2
    canvas.create_oval(gf_cx-ir, gf_cy-ir, gf_cx+ir, gf_cy+ir,
                       fill="", outline="#1a1a1a", width=1)

    # Dot
    lat = acc_g[0] if len(acc_g) > 0 else 0.0
    lon = acc_g[2] if len(acc_g) > 2 else 0.0
    clamp = lambda v: max(-1, min(1, v / 3.0))
    dx = gf_cx + int(clamp(lat) * gf_r * 0.85)
    dy = gf_cy - int(clamp(lon) * gf_r * 0.85)
    dr = max(3, gf_r // 8)
    canvas.create_oval(dx-dr-2, dy-dr-2, dx+dr+2, dy+dr+2,
                       fill="", outline=ACCENT_RED, width=1)
    canvas.create_oval(dx-dr, dy-dr, dx+dr, dy+dr, fill=ACCENT_RED, outline="")

    # G values under circle
    gy = gf_cy + gf_r + 5
    canvas.create_text(gf_cx, gy, text=f"{lat:+.1f}  {lon:+.1f}",
                       fill=TEXT_MID, font=ft, anchor="center")

    # ── Right side: telemetry readouts ──
    rx = x + pad + gf_diam + 14       # right column start
    rw = x + w - pad - rx             # available width
    ry = y + 6
    spacing = max(14, int(h / 8.5))

    def row(label, value, color):
        nonlocal ry
        canvas.create_text(rx, ry, text=label, fill=TEXT_DIM, font=ft, anchor="nw")
        canvas.create_text(rx + rw, ry, text=value, fill=color, font=fv, anchor="ne")
        ry += spacing

    row("AIR",    f"{air_t:.0f}°",   TEXT_BRIGHT)
    row("ROAD",   f"{road_t:.0f}°",  TEXT_BRIGHT)
    row("TURBO",  f"{turbo:.2f}",    ACCENT_BLUE if turbo < 0.5 else ACCENT_YELLOW)

    ry += 2
    canvas.create_text(rx, ry, text="BRK TEMP", fill=TEXT_DIM, font=ft, anchor="nw")
    ry += spacing
    for i, lbl in enumerate(["FL", "FR", "RL", "RR"]):
        bt = brk_t[i]
        canvas.create_text(rx, ry, text=lbl, fill=TEXT_DIM, font=ft, anchor="nw")
        canvas.create_text(rx + rw, ry, text=f"{bt:.0f}°",
                           fill=brake_color(bt), font=fv, anchor="ne")
        ry += spacing - 2


# ── Row 2 ─────────────────────────────────────────────────────────────────────

def draw_pedals(gas, brake, L):
    x, y, w, h = L["c1_x"], L["r2_y"], L["c1_w"], L["r2_h"]
    W = L["W"]
    panel(x, y, w, h)
    ft = font(7, W)

    bar_w = max(14, int(w * 0.22))
    bar_h = h - 34
    by = y + 20

    def bar(bx, label, val, color):
        canvas.create_text(bx + bar_w//2, y + 6, text=label, fill=TEXT_DIM,
                           font=ft, anchor="center")
        canvas.create_rectangle(bx, by, bx+bar_w, by+bar_h,
                                fill="#1a1a1a", outline=BORDER, width=1)
        fh = int(val * bar_h)
        if fh > 0:
            canvas.create_rectangle(bx+1, by+bar_h-fh, bx+bar_w-1, by+bar_h-1,
                                    fill=color, outline="")
        canvas.create_text(bx + bar_w//2, by + bar_h + 5,
                           text=f"{val*100:.0f}%", fill=TEXT_MID, font=ft, anchor="center")

    bar(x + int(w*0.14), "THR", gas, ACCENT_GREEN)
    bar(x + int(w*0.58), "BRK", brake, ACCENT_RED)


def draw_tyres(temps, L):
    x, y, w, h = L["c2_x"], L["r2_y"], L["c2_w"], L["r2_h"]
    W = L["W"]
    panel(x, y, w, h)
    ft = font(7, W)
    fb = font(9, W, True)
    cx = x + w//2

    canvas.create_text(cx, y + 6, text="TYRE °C", fill=TEXT_DIM, font=ft, anchor="center")

    # Car body
    bh = int(h * 0.52)
    bt = y + int(h * 0.26)
    canvas.create_rectangle(cx-5, bt, cx+5, bt+bh, fill="", outline=BORDER, width=1)

    qw = max(20, w // 4)
    spots = [
        (cx - qw, y + int(h*0.36)),   # FL
        (cx + qw, y + int(h*0.36)),   # FR
        (cx - qw, y + int(h*0.74)),   # RL
        (cx + qw, y + int(h*0.74)),   # RR
    ]
    for i, (tx, ty) in enumerate(spots):
        t = temps[i]
        canvas.create_text(tx, ty - 7, text=["FL","FR","RL","RR"][i],
                           fill=TEXT_DIM, font=ft, anchor="center")
        canvas.create_text(tx, ty + 5, text=f"{t:.0f}", fill=tyre_color(t),
                           font=fb, anchor="center")


def draw_fuel(fuel, max_fuel, bb, drs, drs_avail, L):
    x, y, w, h = L["c3_x"], L["r2_y"], L["c3_w"], L["r2_h"]
    W = L["W"]
    panel(x, y, w, h)
    ft = font(7, W)
    fv = font(9, W, True)

    pad = 10
    iy = y + 8
    rh = max(15, int(h / 4.5))

    # ── Fuel ──
    lbl_w = 32
    canvas.create_text(x + pad, iy + 1, text="FUEL", fill=TEXT_DIM, font=ft, anchor="nw")
    fb_x = x + pad + lbl_w + 4
    fb_w = w - 2*pad - lbl_w - 36
    fb_h = 7
    canvas.create_rectangle(fb_x, iy + 2, fb_x + fb_w, iy + 2 + fb_h,
                            fill="#1a1a1a", outline=BORDER, width=1)
    if max_fuel > 0:
        fw = int(min(fuel/max_fuel, 1.0) * (fb_w - 2))
        fc = ACCENT_GREEN if fuel/max_fuel > 0.25 else ACCENT_RED
        if fw > 0:
            canvas.create_rectangle(fb_x+1, iy+3, fb_x+1+fw, iy+1+fb_h, fill=fc, outline="")
    canvas.create_text(x + w - pad, iy + 3, text=f"{fuel:.0f}L",
                       fill=TEXT_BRIGHT, font=ft, anchor="ne")

    iy += rh

    # ── Brake bias ──
    canvas.create_text(x + pad, iy, text="BB", fill=TEXT_DIM, font=ft, anchor="nw")
    canvas.create_text(x + pad + lbl_w, iy, text=f"{bb:.1f}%",
                       fill=TEXT_BRIGHT, font=fv, anchor="nw")

    iy += rh

    # ── DRS ──
    canvas.create_text(x + pad, iy, text="DRS", fill=TEXT_DIM, font=ft, anchor="nw")
    dc = ACCENT_GREEN if drs > 0 else (ACCENT_YELLOW if drs_avail else "#1a1a1a")
    ox = x + pad + lbl_w
    canvas.create_oval(ox, iy + 1, ox + 10, iy + 11, fill=dc, outline=BORDER, width=1)
    dt = "ON" if drs > 0 else ("RDY" if drs_avail else "OFF")
    canvas.create_text(ox + 15, iy + 1, text=dt, fill=TEXT_MID, font=ft, anchor="nw")


# ── Bottom bar ────────────────────────────────────────────────────────────────

def draw_bar(car, track, tyre, L):
    W, H = L["W"], L["H"]
    M = L["M"]
    by = L["bot_y"]
    ft = font(7, W)
    fi = font(8, W)

    canvas.create_line(M, by, W-M, by, fill=BORDER, width=1)

    canvas.create_text(M+4, by+3, text="CAR", fill=TEXT_DIM, font=ft, anchor="nw")
    canvas.create_text(M+4, by+13, text=str(car).upper()[:22],
                       fill=TEXT_MID, font=fi, anchor="nw")

    canvas.create_text(W//2, by+3, text="TRACK", fill=TEXT_DIM, font=ft, anchor="n")
    canvas.create_text(W//2, by+13, text=str(track).upper()[:22],
                       fill=TEXT_MID, font=fi, anchor="n")

    canvas.create_text(W-M-4, by+3, text="TYRE", fill=TEXT_DIM, font=ft, anchor="ne")
    canvas.create_text(W-M-4, by+13, text=str(tyre).strip('\x00')[:14],
                       fill=TEXT_MID, font=fi, anchor="ne")

    canvas.create_rectangle(0, H-3, W, H, fill=ACCENT_RED, outline="")


# ── Waiting screen ────────────────────────────────────────────────────────────

def draw_waiting(L):
    W, H = L["W"], L["H"]
    canvas.create_rectangle(0, 0, W, 3, fill=ACCENT_RED, outline="")
    canvas.create_rectangle(0, H-3, W, H, fill=ACCENT_RED, outline="")
    canvas.create_text(W//2, H//2 - 18, text="ASSETTO CORSA",
                       fill=TEXT_WHITE, font=font(20, W, True), anchor="center")
    canvas.create_text(W//2, H//2 + 14, text="WAITING FOR CONNECTION…",
                       fill=TEXT_DIM, font=font(12, W), anchor="center")


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

_max_rpm  = [9000]
_max_fuel = [50.0]


def update():
    static  = ac_reader.read_static_info()
    physics = ac_reader.read_physics()
    gfx     = ac_reader.read_graphics()

    canvas.delete("all")

    W = canvas.winfo_width()
    H = canvas.winfo_height()
    if W < 10 or H < 10:
        W, H = BASE_W, BASE_H
    L = layout(W, H)

    if static and physics and gfx:
        if static.MaxRpm  > 0: _max_rpm[0]  = static.MaxRpm
        if static.MaxFuel > 0: _max_fuel[0] = static.MaxFuel

        draw_frame(L)
        draw_rpm(physics.Rpms, _max_rpm[0], L)

        # Row 1
        draw_speed(physics.SpeedKmh, L)
        draw_gear(physics.Gear, L)
        draw_gforce(physics.AccG, physics.AirTemp, physics.RoadTemp,
                    physics.BrakeTemp, physics.TurboBoost, L)

        # Row 2
        draw_pedals(physics.Gas, physics.Brake, L)
        draw_tyres(physics.TyreCoreTemperature, L)
        draw_fuel(physics.Fuel, _max_fuel[0],
                  physics.BrakeBias, physics.Drs, physics.DrsAvailable, L)

        draw_bar(static.CarModel, static.Track, gfx.TyreCompound, L)
    else:
        draw_waiting(L)

    root.after(100, update)


update()
root.mainloop()