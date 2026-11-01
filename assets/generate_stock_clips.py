"""
Procedural Moving Cricket Footage Generator
Generates high-definition 1080x1920 30FPS moving cricket video clips:
1. stadium_floodlights.mp4: Volumetric moving beams, sweeping stadium lights, haze
2. bowler_runup.mp4: 3D perspective moving rapidly down cricket pitch towards stumps
3. cricket_ball_spin.mp4: Realistic 3D rotating red leather cricket ball with white seam & lens flare
4. batsman_crease.mp4: Dynamic stadium lighting, crease perspective, tracking shot
5. wicket_crash.mp4: Ball impact, flying bails animation, motion trail
6. stadium_crowd.mp4: Cheering crowd silhouettes with flashing lights and celebratory aura
7. umpire_decision.mp4: Official MCC DRS tracking ray traveling down pitch with laser grid
8. historic_vault.mp4: Golden archive sweep with cinematic lighting for legendary records
"""

import os
import math
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS = 1080, 1920, 30


def render_clip(name: str, duration_sec: int, render_frame_fn):
    out_dir = "assets/stock_footage"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, name)

    if os.path.exists(out_path) and os.path.getsize(out_path) > 100000:
        print(f"Clip {name} already exists. Skipping.")
        return out_path

    total_frames = int(duration_sec * FPS)
    cmd = [
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{W}x{H}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-pix_fmt", "yuv420p", out_path
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for f in range(total_frames):
        t = f / FPS
        img = render_frame_fn(t, f, total_frames)
        proc.stdin.write(img.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Generated moving video: {out_path} ({duration_sec}s @ 30FPS)")
    return out_path


# --- 1. Stadium Floodlights Night ---
def frame_stadium(t, f, total):
    img = Image.new("RGB", (W, H), (9, 13, 22))
    draw = ImageDraw.Draw(img)

    # Moving floodlight beams sweeping
    beam1_x = int(W * 0.2 + math.sin(t * 1.2) * 200)
    beam2_x = int(W * 0.8 - math.cos(t * 1.5) * 220)

    # Draw volumetric light cones
    draw.polygon([(0, 0), (beam1_x - 120, H), (beam1_x + 120, H)], fill=(20, 42, 65))
    draw.polygon([(W, 0), (beam2_x - 140, H), (beam2_x + 100, H)], fill=(22, 45, 70))

    # Center stadium turf glow
    glow_y = int(H * 0.75 + math.sin(t * 2.0) * 25)
    draw.ellipse([100, glow_y - 200, W - 100, glow_y + 400], fill=(16, 50, 30))

    # Crowd silhouette at bottom with moving camera pan
    pan = int(math.sin(t * 0.8) * 40)
    for cx in range(-50, W + 50, 45):
        h_offset = int(math.sin(cx + t * 4) * 15)
        draw.ellipse([cx + pan, H - 280 + h_offset, cx + 40 + pan, H - 180 + h_offset], fill=(6, 9, 15))
    draw.rectangle([0, H - 220, W, H], fill=(5, 8, 14))
    return img


# --- 2. Bowler Runup down the Pitch ---
def frame_bowler(t, f, total):
    img = Image.new("RGB", (W, H), (12, 16, 26))
    draw = ImageDraw.Draw(img)

    # Dynamic camera flying down the pitch
    speed = t * 180
    vanish_y = int(H * 0.38)
    vanish_x = W // 2

    # Perspective pitch trapezoid expanding downwards
    pitch_top_w = 140
    pitch_bot_w = 680
    draw.polygon([
        (vanish_x - pitch_top_w // 2, vanish_y),
        (vanish_x + pitch_top_w // 2, vanish_y),
        (vanish_x + pitch_bot_w // 2, H),
        (vanish_x - pitch_bot_w // 2, H)
    ], fill=(190, 160, 115), outline=(22, 68, 36), width=8)

    # Moving bowling crease lines zooming toward camera
    for i in range(5):
        line_progress = ((t * 1.2 + i * 0.25) % 1.0)
        y = int(vanish_y + (H - vanish_y) * (line_progress ** 1.8))
        half_w = int(pitch_top_w // 2 + (pitch_bot_w // 2 - pitch_top_w // 2) * (line_progress ** 1.8))
        draw.line([(vanish_x - half_w, y), (vanish_x + half_w, y)], fill=(255, 255, 255), width=int(2 + line_progress * 8))

    # Batsman Stumps at the far end
    stump_x = vanish_x
    stump_y = vanish_y + 10
    draw.line([(stump_x - 18, stump_y - 45), (stump_x - 18, stump_y)], fill=(240, 230, 200), width=3)
    draw.line([(stump_x, stump_y - 48), (stump_x, stump_y)], fill=(240, 230, 200), width=3)
    draw.line([(stump_x + 18, stump_y - 45), (stump_x + 18, stump_y)], fill=(240, 230, 200), width=3)
    draw.line([(stump_x - 22, stump_y - 48), (stump_x + 22, stump_y - 48)], fill=(255, 255, 255), width=3) # Bails
    return img


# --- 3. Cricket Ball 3D Spin ---
def frame_ball(t, f, total):
    img = Image.new("RGB", (W, H), (10, 14, 22))
    draw = ImageDraw.Draw(img)

    # Moving atmospheric glow
    glow_x = int(W // 2 + math.sin(t * 1.8) * 120)
    glow_y = int(H // 2 - 80 + math.cos(t * 1.4) * 80)
    draw.ellipse([glow_x - 360, glow_y - 360, glow_x + 360, glow_y + 360], fill=(28, 48, 85))

    # 3D Red Leather Cricket Ball
    bx, by, r = W // 2, H // 2 - 80, 240
    draw.ellipse([bx - r, by - r, bx + r, by + r], fill=(190, 24, 24), outline=(130, 15, 15), width=5)

    # Shading gradient
    draw.ellipse([bx - r + 30, by - r + 20, bx - r + 130, by - r + 120], fill=(235, 75, 75))

    # Moving rotating white seam
    phase = t * 7.5
    pts = []
    for deg in range(-85, 86, 8):
        rad = math.radians(deg)
        x = bx + r * 0.92 * math.cos(rad) * math.cos(phase)
        y = by + r * 0.96 * math.sin(rad)
        pts.append((x, y))
    if len(pts) > 1:
        draw.line(pts, fill=(255, 255, 255), width=8)
    return img


# --- 4. Batsman Stance & Crease ---
def frame_batsman(t, f, total):
    img = Image.new("RGB", (W, H), (14, 18, 28))
    draw = ImageDraw.Draw(img)

    # Dynamic camera push-in
    scale = 1.0 + (t / total) * 0.15
    vanish_y = int(H * 0.42 * scale)

    # Pitch surface
    draw.polygon([(260, vanish_y), (820, vanish_y), (1040, H), (40, H)], fill=(200, 170, 125))

    # Crease line
    draw.line([(80, H - 420), (1000, H - 420)], fill=(255, 255, 255), width=10)

    # Batsman shadow & stance silhouette with subtle breathing motion
    sway = math.sin(t * 3.0) * 8
    # Bat silhouette angled down
    draw.line([(580 + sway, H - 650), (620 + sway, H - 380)], fill=(120, 80, 40), width=22)
    # Stumps in front of crease
    draw.rectangle([480, H - 540, 500, H - 420], fill=(225, 215, 185))
    draw.rectangle([515, H - 545, 535, H - 420], fill=(225, 215, 185))
    draw.rectangle([550, H - 540, 570, H - 420], fill=(225, 215, 185))
    return img


# --- 5. Flying Wickets Crash ---
def frame_wickets(t, f, total):
    img = Image.new("RGB", (W, H), (11, 15, 25))
    draw = ImageDraw.Draw(img)

    # Center explosion of light
    cx, cy = W // 2, H // 2 - 50
    draw.ellipse([cx - 280, cy - 280, cx + 280, cy + 280], fill=(45, 30, 20))

    # Stumps rattling & flying
    angle1 = math.sin(t * 5.0) * 35
    angle2 = -math.cos(t * 4.5) * 45
    # Off stump flying
    draw.line([(cx - 70, cy + 180), (cx - 70 + angle1 * 4, cy - 140 + angle1 * 2)], fill=(245, 230, 190), width=14)
    # Middle stump shattered
    draw.line([(cx, cy + 180), (cx + angle2 * 3, cy - 120 + angle2 * 2)], fill=(245, 230, 190), width=14)
    # Leg stump
    draw.line([(cx + 70, cy + 180), (cx + 70, cy - 100)], fill=(245, 230, 190), width=14)

    # Flying illuminated bails
    bail_y = int(cy - 200 - math.sin(t * 3.5) * 80)
    draw.line([(cx - 60, bail_y), (cx + 40, bail_y - 25)], fill=(255, 255, 255), width=10)
    return img


# --- 6. Stadium Celebration & Confetti ---
def frame_celebration(t, f, total):
    img = Image.new("RGB", (W, H), (12, 17, 30))
    draw = ImageDraw.Draw(img)

    # Dynamic pulsing stadium lights
    pulse = (math.sin(t * 4.0) + 1.0) / 2.0
    draw.ellipse([150, 200, 930, 850], fill=(int(20 + pulse * 25), int(45 + pulse * 40), int(75 + pulse * 45)))

    # Confetti particles falling
    np.random.seed(42)
    num_particles = 65
    for i in range(num_particles):
        x = (int(np.random.uniform(50, W - 50)) + int(math.sin(t * 2 + i) * 60)) % W
        y = (int(np.random.uniform(50, H - 50)) + int(t * 280 + i * 40)) % H
        color = [(255, 215, 0), (0, 212, 255), (255, 80, 80), (255, 255, 255)][i % 4]
        draw.ellipse([x, y, x + 10, y + 10], fill=color)

    # Crowd silhouette celebration hands
    for cx in range(0, W + 40, 55):
        hand_h = int(math.sin(cx + t * 6) * 35)
        draw.ellipse([cx, H - 250 + hand_h, cx + 35, H - 150 + hand_h], fill=(7, 10, 16))
    draw.rectangle([0, H - 180, W, H], fill=(5, 8, 14))
    return img


# --- 7. Umpire Decision Radar DRS ---
def frame_umpire(t, f, total):
    img = Image.new("RGB", (W, H), (8, 12, 20))
    draw = ImageDraw.Draw(img)

    # Radar grid lines sweeping down pitch
    for y in range(400, H - 300, 90):
        alpha = int(40 + math.sin(t * 4 + y * 0.01) * 30)
        draw.line([(100, y), (W - 100, y)], fill=(0, 180, 255), width=2)

    # 3D Ball tracking trajectory arc (neon cyan line)
    sweep_progress = (t * 0.7) % 1.0
    pts = []
    for step in range(30):
        progress = step / 30.0
        if progress > sweep_progress:
            break
        px = int(W // 2 + math.sin(progress * 3.14) * 120)
        py = int(500 + progress * 800)
        pts.append((px, py))
    if len(pts) > 1:
        draw.line(pts, fill=(0, 255, 255), width=8)
        # Glowing radar ball at the head
        hx, hy = pts[-1]
        draw.ellipse([hx - 22, hy - 22, hx + 22, hy + 22], fill=(255, 255, 255), outline=(0, 255, 255), width=4)

    # Top DRS Decision box
    draw.rounded_rectangle([320, 220, 760, 310], radius=16, fill=(16, 25, 42), outline=(0, 212, 255), width=3)
    return img


# --- 8. Historic Record Vault ---
def frame_historic(t, f, total):
    img = Image.new("RGB", (W, H), (14, 18, 28))
    draw = ImageDraw.Draw(img)

    # Moving golden documentary light sheen
    glow_x = int(W // 2 + math.sin(t * 1.5) * 180)
    draw.ellipse([glow_x - 300, 500, glow_x + 300, 1100], fill=(45, 38, 15))

    # Elegant golden frame lines
    margin = 80
    draw.rectangle([margin, margin + 120, W - margin, H - margin - 200], outline=(212, 175, 55), width=4)
    draw.rectangle([margin + 16, margin + 136, W - margin - 16, H - margin - 216], outline=(120, 95, 30), width=2)
    return img


def generate_all_stock():
    print("Generating High-Definition Moving Cricket Stock Library...")
    render_clip("stadium_floodlights.mp4", 8, frame_stadium)
    render_clip("bowler_runup.mp4", 8, frame_bowler)
    render_clip("cricket_ball_spin.mp4", 8, frame_ball)
    render_clip("batsman_crease.mp4", 8, frame_batsman)
    render_clip("wicket_crash.mp4", 8, frame_wickets)
    render_clip("stadium_celebration.mp4", 8, frame_celebration)
    render_clip("umpire_decision.mp4", 8, frame_umpire)
    render_clip("historic_vault.mp4", 8, frame_historic)
    print("All 8 stock video clips ready in assets/stock_footage/!")


if __name__ == "__main__":
    generate_all_stock()
