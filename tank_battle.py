# ============================================================
#  CSE423 - Tank Battle (3D)
#  Shudhu Lab 1/2/3 template er gl/glut function diye banano.
#  glutTimerFunc use kora hoy nai (banned) - shob animation
#  idle() er moddhe time.time() delta diye kora hoise.
#
#  Feature list (task onujayi):
#   1. Player tank - box (body) + cylinder (barrel)
#   2. Turret body er shathe move kore (nijei ghore na)
#   3. Enemy tank player er base er dike ashe
#   4. Round/wave - ekta wave shesh hole notun harder wave
#   5. Shell arc kore jay (upore uthe niche pore, gravity)
#   6. Obstacle - wall/rock, view r movement block kore
#   7. Base er health - base destroy hole game over
#   8. Tank er health - destroy hole flash + shrink kore
#   9. Duita camera - orbit (upor theke) r follow (tank er pichon)
#  10. Power-up - mati te pore thake, gele boost dey
#  11. Minimap - corner e choto map
#  12. Score + bonus point
#  13. Pause button - game freeze
#  14. Game over screen + restart
# ============================================================

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

WIN_W, WIN_H = 1000, 800
fovY = 90
ARENA = 800          # arena radius (gol battlefield)
# arena ekhon OVAL shape - X r Y te alada radius (RX chere-lomba, RY choto)
RX = 620             # oval er X-radius (bhutorer dike prosto)
RY = 500             # oval er Y-radius (bhutorer dike lomba na, ektu choto)
WALL_H = 60


def in_arena(x, y, margin=0):
    # point ta oval er bhitore kina - oval equation (x/rx)^2 + (y/ry)^2 <= 1
    rx = RX - margin
    ry = RY - margin
    return (x * x) / (rx * rx) + (y * y) / (ry * ry) <= 1.0

# ------------------------------------------------------------
# player tank state
# ------------------------------------------------------------
tank_x, tank_y = 0.0, -450.0
tank_ang = 0.0        # body kon dike (degree)
turret_ang = 0.0      # turret/barrel kon dike - ekhon body er shathe e thake
move_spd = 180.0
turn_spd = 90.0

tank_hp = 100
tank_max_hp = 100
tank_hit_flash = 0.0  # hit khele ei timer > 0 hoy, tokhon flash kore

# ------------------------------------------------------------
# base state (alada health)
# ------------------------------------------------------------
base_x, base_y = 0.0, -650.0
base_hp = 100
base_max_hp = 100

# ------------------------------------------------------------
# shooting - shell gula arc kore, tai z r vz (vertical speed) ache
# ------------------------------------------------------------
shells = []           # [x, y, z, vx, vy, vz]  (enemy shell na, player er)
enemy_shells = []     # enemy der chhora shell
shell_spd = 420.0
GRAV = 500.0          # gravity, shell ke niche tane
fire_cd = 0.0
FIRE_GAP = 0.45       # duita fire er majhe minimum gap (sec)

# ------------------------------------------------------------
# enemies - [x, y, ang, hp, fire_cd]
# ------------------------------------------------------------
enemies = []
enemy_spd = 55.0
enemy_r = 30.0
round_no = 1
round_clear_msg = 0.0

# ------------------------------------------------------------
# obstacles - [x, y, size]  (box, view+movement block kore)
# ------------------------------------------------------------
obstacles = []

# ------------------------------------------------------------
# power-ups - [x, y, kind, phase]  kind: 'rapid' ba 'speed'
# phase eta ghurano/bhashano animation er jonno
# ------------------------------------------------------------
powerups = []
boost_rapid = 0.0     # >0 thakle fire gap kome (rapid fire)
boost_speed = 0.0     # >0 thakle tank fast chole

# ------------------------------------------------------------
# game flow
# ------------------------------------------------------------
score = 0
paused = False
game_over = False
cam_mode = 0          # 0 = orbit, 1 = follow
cam_orbit = 0.0       # orbit camera angle - shudhu arrow key chaple bodlay

# game over hole restart, P e pause, V te camera toggle
last_time = time.time()


# ============================================================
# HELPERS
# ============================================================

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def cuboid(sx, sy, sz):
    # ekta unit cube ke scale kore box banai
    glPushMatrix()
    glScalef(sx, sy, sz)
    glutSolidCube(1)
    glPopMatrix()


def heading(a):
    # angle theke (dx, dy) direction ber kore
    r = math.radians(a)
    return -math.sin(r), math.cos(r)


def dist(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)


def blocked(x, y):
    # ei point ta kono obstacle er bhitore kina (movement block)
    for ox, oy, osz in obstacles:
        if abs(x - ox) < osz / 2 + 20 and abs(y - oy) < osz / 2 + 20:
            return True
    return False


# ============================================================
# WORLD SETUP
# ============================================================

def make_obstacles():
    obstacles.clear()
    spots = [(-250, 100), (250, 150), (0, 250), (-300, -100), (320, -120)]
    for sx, sy in spots:
        obstacles.append([sx, sy, random.choice([70, 90, 110])])


def rand_in_circle(rmax, y_min=None, y_max=None):
    # gol arena er bhitore ekta random point ber kore
    for _ in range(20):
        x = random.uniform(-rmax, rmax)
        y = random.uniform(-rmax, rmax)
        if math.hypot(x, y) <= rmax:
            if y_min is not None and y < y_min:
                continue
            if y_max is not None and y > y_max:
                continue
            return x, y
    return 0.0, 0.0


def spawn_wave(n):
    enemies.clear()
    for _ in range(n):
        # arena er upor er dik theke enemy name (gol boundary er bhitore)
        x, y = rand_in_circle(ARENA - 60, y_min=200)
        enemies.append([x, y, 0.0, 30, random.uniform(1.0, 3.0)])


def spawn_powerup():
    kind = random.choice(['rapid', 'speed'])
    x, y = rand_in_circle(ARENA - 80, y_min=-200, y_max=300)
    powerups.append([x, y, kind, 0.0])


def reset_game():
    global tank_x, tank_y, tank_ang, turret_ang, tank_hp, base_hp
    global shells, enemy_shells, score, round_no, paused, game_over
    global boost_rapid, boost_speed, fire_cd, tank_hit_flash, round_clear_msg
    tank_x, tank_y = 0.0, -450.0
    tank_ang = 0.0
    turret_ang = 0.0
    tank_hp = tank_max_hp
    base_hp = base_max_hp
    shells = []
    enemy_shells = []
    powerups.clear()
    score = 0
    round_no = 1
    paused = False
    game_over = False
    boost_rapid = 0.0
    boost_speed = 0.0
    fire_cd = 0.0
    tank_hit_flash = 0.0
    round_clear_msg = 0.0
    make_obstacles()
    spawn_wave(3)
    powerups.clear()
    spawn_powerup()
    spawn_powerup()


# ============================================================
# DRAWING
# ============================================================

def draw_sky():
    # rangin sky - arena er charpashe ekta boro gol "deyal" (cylinder er
    # moto) quad diye banano, niche theke upore color gradient (dusk feel:
    # niche komla/gulapi, upore neel-beguni). Kono texture na, shudhu
    # glVertex3f + glColor3f diye.
    R = ARENA * 2.4          # sky arena theke onk baire
    seg = 48
    bands = [
        (0,    380,  (0.98, 0.55, 0.32)),   # horizon - komla
        (380,  760,  (0.78, 0.42, 0.55)),   # gulapi
        (760,  1150, (0.42, 0.32, 0.62)),   # beguni
        (1150, 1600, (0.16, 0.18, 0.45)),   # gaaro neel (upor)
    ]
    for z0, z1, col in bands:
        glColor3f(*col)
        glBegin(GL_QUADS)
        for si in range(seg):
            a0 = 2 * math.pi * si / seg
            a1 = 2 * math.pi * (si + 1) / seg
            x0, y0 = R * math.cos(a0), R * math.sin(a0)
            x1, y1 = R * math.cos(a1), R * math.sin(a1)
            glVertex3f(x0, y0, z0)
            glVertex3f(x1, y1, z0)
            glVertex3f(x1, y1, z1)
            glVertex3f(x0, y0, z1)
        glEnd()

    # ekta boro sun/moon disk (horizon er upore, halka jhulchhe)
    sun_a = math.radians(60)
    sx = (R - 30) * math.cos(sun_a)
    sy = (R - 30) * math.sin(sun_a)
    sz = 520 + 20 * math.sin(time.time() * 0.6)
    glColor3f(1.0, 0.92, 0.6)
    glBegin(GL_QUADS)
    steps = 20
    rr = 220
    for k in range(steps):
        b0 = 2 * math.pi * k / steps
        b1 = 2 * math.pi * (k + 1) / steps
        # disk ta sky er gaaye, tai oi angle er tangent plane e naki -
        # simple rakhte just x fixed kore z-y plane e disk আঁki
        glVertex3f(sx, sy, sz)
        glVertex3f(sx, sy + rr * math.cos(b0), sz + rr * math.sin(b0))
        glVertex3f(sx, sy + rr * math.cos(b1), sz + rr * math.sin(b1))
        glVertex3f(sx, sy, sz)
    glEnd()

    # distant hill silhouette - horizon er kace koyekta gaaro trikon-ish
    # dhap (quad diye), scene ke bhora r depth dey
    glColor3f(0.20, 0.24, 0.30)
    hills = 20
    Rh = ARENA * 1.9
    glBegin(GL_QUADS)
    for si in range(hills):
        a0 = 2 * math.pi * si / hills
        a1 = 2 * math.pi * (si + 1) / hills
        x0, y0 = Rh * math.cos(a0), Rh * math.sin(a0)
        x1, y1 = Rh * math.cos(a1), Rh * math.sin(a1)
        # ekek hill er ekek height (deterministic variation)
        hgt = 120 + 90 * ((si * 5) % 4)
        glVertex3f(x0, y0, 0)
        glVertex3f(x1, y1, 0)
        glVertex3f(x1, y1, hgt)
        glVertex3f(x0, y0, hgt)
    glEnd()


def draw_ground():
    # battlefield mati - GOL (circular) arena. Concentric ring r wedge
    # diye tile kora. Ekhon aro rangin - সবুজ ghas er tone er upor halka
    # animated shimmer, r kichu ring e alada accent color.
    rings = 12
    seg = 48
    rad = ARENA
    tsec = time.time()
    for ri in range(rings):
        r0 = rad * ri / rings
        r1 = rad * (ri + 1) / rings
        glBegin(GL_QUADS)
        for si in range(seg):
            a0 = 2 * math.pi * si / seg
            a1 = 2 * math.pi * (si + 1) / seg
            t = ((ri * 7 + si * 13) % 5) / 5.0
            # halka animated shimmer - color ektu dole (khub subtle)
            sh = 0.04 * math.sin(tsec * 1.5 + ri + si)
            # sobuj ghas-tone base
            r = 0.20 + 0.14 * t + sh
            gg = 0.45 + 0.18 * t + sh
            b = 0.22 + 0.10 * t
            # majhe majhe ekta ring e alada accent (teal/olive) jate
            # arena flat na lage
            if ri % 4 == 0:
                r, gg, b = 0.16 + 0.10 * t, 0.40 + 0.14 * t, 0.34 + 0.10 * t
            glColor3f(r, gg, b)
            glVertex3f(r0 * math.cos(a0), r0 * math.sin(a0), 0)
            glVertex3f(r1 * math.cos(a0), r1 * math.sin(a0), 0)
            glVertex3f(r1 * math.cos(a1), r1 * math.sin(a1), 0)
            glVertex3f(r0 * math.cos(a1), r0 * math.sin(a1), 0)
        glEnd()

    # kichu darker scorch/crater patch (gol), battlefield feel er jonno
    glColor3f(0.20, 0.16, 0.12)
    for (cx, cy, cs) in [(-260, 200, 70), (240, -160, 90), (330, 260, 60),
                         (-360, -210, 78), (80, 400, 66)]:
        glBegin(GL_QUADS)
        steps = 16
        for k in range(steps):
            b0 = 2 * math.pi * k / steps
            b1 = 2 * math.pi * (k + 1) / steps
            glVertex3f(cx, cy, 1)
            glVertex3f(cx + cs * math.cos(b0), cy + cs * math.sin(b0), 1)
            glVertex3f(cx + cs * math.cos(b1), cy + cs * math.sin(b1), 1)
            glVertex3f(cx, cy, 1)
        glEnd()

    # ekta rangin center marker - arena er majhe ekta choto gol pad
    # (bright teal), jate scene e ekta focal color point thake
    glColor3f(0.1, 0.7, 0.7)
    glBegin(GL_QUADS)
    steps = 20
    cs = 55
    for k in range(steps):
        b0 = 2 * math.pi * k / steps
        b1 = 2 * math.pi * (k + 1) / steps
        glVertex3f(0, 0, 2)
        glVertex3f(cs * math.cos(b0), cs * math.sin(b0), 2)
        glVertex3f(cs * math.cos(b1), cs * math.sin(b1), 2)
        glVertex3f(0, 0, 2)
    glEnd()


def draw_boundary():
    # circular wall - gol deyal, ekhon rangin: protita segment ektu alada
    # shade (rainbow-ish subtle) jate wall flat na lage
    rad = ARENA
    seg = 60
    glBegin(GL_QUADS)
    for si in range(seg):
        a0 = 2 * math.pi * si / seg
        a1 = 2 * math.pi * (si + 1) / seg
        x0, y0 = rad * math.cos(a0), rad * math.sin(a0)
        x1, y1 = rad * math.cos(a1), rad * math.sin(a1)
        # segment onujayi color cycle (hue er moto ghore)
        hue = si / seg
        r = 0.5 + 0.4 * math.sin(2 * math.pi * hue)
        g = 0.5 + 0.4 * math.sin(2 * math.pi * hue + 2.1)
        b = 0.5 + 0.4 * math.sin(2 * math.pi * hue + 4.2)
        glColor3f(r, g, b)
        glVertex3f(x0, y0, 0)
        glVertex3f(x1, y1, 0)
        glVertex3f(x1, y1, WALL_H)
        glVertex3f(x0, y0, WALL_H)
    glEnd()


def draw_obstacles():
    # rangin crate/rock - plain grey na. Protita obstacle er ekta base
    # cube + upore ekta bright accent cap + upore ekta choto ghurte-thaka
    # rangin gem (sphere), jate battlefield e rangin element thake.
    palette = [(0.75, 0.35, 0.25), (0.3, 0.5, 0.7), (0.55, 0.45, 0.2),
               (0.4, 0.6, 0.35), (0.6, 0.35, 0.55)]
    for idx, (ox, oy, osz) in enumerate(obstacles):
        col = palette[idx % len(palette)]
        glPushMatrix()
        glTranslatef(ox, oy, osz / 2)
        glColor3f(*col)
        cuboid(osz, osz, osz)
        glPopMatrix()

        # upore bright cap
        glPushMatrix()
        glTranslatef(ox, oy, osz + 4)
        glColor3f(min(1, col[0] + 0.3), min(1, col[1] + 0.3), min(1, col[2] + 0.3))
        cuboid(osz * 0.7, osz * 0.7, 8)
        glPopMatrix()

        # upore ghurte-thaka gem
        glPushMatrix()
        glTranslatef(ox, oy, osz + 22 + 4 * math.sin(time.time() * 2 + idx))
        glRotatef((time.time() * 60 + idx * 40) % 360, 0, 0, 1)
        glColor3f(0.2, 0.9, 0.9)
        gluSphere(gluNewQuadric(), 9, 8, 8)
        glPopMatrix()


def draw_tank(x, y, body_ang, tur_ang, color, scale=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(scale, scale, scale)

    # body
    glPushMatrix()
    glRotatef(body_ang, 0, 0, 1)
    glColor3f(*color)
    glPushMatrix()
    glTranslatef(0, 0, 18)
    cuboid(50, 70, 24)
    glPopMatrix()
    # bright accent stripe body er upore (rangin detail)
    glColor3f(min(1, color[0] + 0.4), min(1, color[1] + 0.4), min(1, color[2] + 0.2))
    glPushMatrix()
    glTranslatef(0, 0, 31)
    cuboid(52, 22, 4)
    glPopMatrix()
    # track duita (pashe duita box)
    glColor3f(0.15, 0.15, 0.15)
    for sx in (-30, 30):
        glPushMatrix()
        glTranslatef(sx, 0, 12)
        cuboid(14, 76, 20)
        glPopMatrix()
    glPopMatrix()

    # turret + barrel, eta body theke alada angle e ghore
    glPushMatrix()
    glRotatef(tur_ang, 0, 0, 1)
    glColor3f(color[0] * 0.7, color[1] * 0.7, color[2] * 0.7)
    glPushMatrix()
    glTranslatef(0, 0, 40)
    gluSphere(gluNewQuadric(), 18, 10, 10)
    glPopMatrix()
    # barrel, cylinder shamne bariye
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 6, 5, 55, 8, 8)
    glPopMatrix()
    # barrel er matha e bright tip (rangin)
    glColor3f(1.0, 0.8, 0.1)
    dxb, dyb = -math.sin(math.radians(tur_ang)), math.cos(math.radians(tur_ang))
    glPushMatrix()
    glTranslatef(dxb * 55, dyb * 55, 40)
    gluSphere(gluNewQuadric(), 5, 6, 6)
    glPopMatrix()
    glPopMatrix()

    glPopMatrix()


def hp_color(frac):
    # 100-70% -> green, 70-40% -> yellow, niche 40% -> red
    if frac >= 0.7:
        return (0.1, 0.85, 0.1)
    elif frac >= 0.4:
        return (0.95, 0.85, 0.1)
    else:
        return (0.9, 0.15, 0.1)


def fill_circle_2d(cx, cy, r):
    # ekta bhora circle/disk GL_POINTS diye (capsule er gol matha banate)
    glPointSize(2)
    glBegin(GL_POINTS)
    ry = -r
    while ry <= r:
        half = math.sqrt(max(0.0, r * r - ry * ry))
        x = -half
        while x <= half:
            glVertex3f(cx + x, cy + ry, 0)
            x += 2
        ry += 2
    glEnd()


def fill_rect_2d(x, y, w, h):
    glBegin(GL_QUADS)
    glVertex3f(x, y, 0)
    glVertex3f(x + w, y, 0)
    glVertex3f(x + w, y + h, 0)
    glVertex3f(x, y + h, 0)
    glEnd()


def capsule_2d(x, y, w, h):
    # oval/pill shape - majhe rectangle, dui pashe half-circle. Ekta
    # rounded capsule er moto dekhay (assignment 3 er box er moto na)
    r = h / 2
    fill_rect_2d(x + r, y, w - 2 * r, h)      # majher rectangle
    fill_circle_2d(x + r, y + r, r)           # baa matha (gol)
    fill_circle_2d(x + w - r, y + r, r)       # dan matha (gol)


def draw_hp_capsule(x, y, label, hp, max_hp):
    # image er moto ekta segmented capsule health bar (heart chara).
    # baire ekta gaaro outline capsule, bhitore hp onujayi rongin fill,
    # r fill er upore choto choto gap diye "segment" er look.
    frac = max(0.0, min(1.0, hp / max_hp))
    w, h = 200, 26
    # halka pulse animation jokhon hp kom (<40%) - warning er moto blink
    col = hp_color(frac)
    if frac < 0.4 and int(time.time() * 4) % 2 == 0:
        col = (1, 0.4, 0.3)

    # outline/background capsule (gaaro)
    glColor3f(0.12, 0.12, 0.12)
    capsule_2d(x - 3, y - 3, w + 6, h + 6)
    # khali (empty) capsule - halka sada
    glColor3f(0.85, 0.85, 0.85)
    capsule_2d(x, y, w, h)
    # bhora (filled) capsule - hp color
    if frac > 0.02:
        glColor3f(*col)
        capsule_2d(x, y, max(h, w * frac), h)

    # segment gap - filled ongsher upore choto choto khara kalo daag,
    # jate image er moto "block block" segmented look ashe
    glColor3f(0.12, 0.12, 0.12)
    seg = 10
    gx = x + h
    while gx < x + w * frac - 2:
        fill_rect_2d(gx, y + 3, 2, h - 6)
        gx += seg

    # label (TANK / BASE) capsule er baa pashe
    draw_text(int(x - 62), int(y + 5), label)


def draw_player_tank():
    # hit flash - flash timer thakle color blink kore, r shrink kore
    color = (0.2, 0.6, 0.9)
    scale = 1.0
    if tank_hit_flash > 0:
        if int(tank_hit_flash * 20) % 2 == 0:
            color = (1, 1, 1)
        scale = 0.85 + 0.15 * (1 - tank_hit_flash)
    draw_tank(tank_x, tank_y, tank_ang, turret_ang, color, scale)


def draw_base():
    glPushMatrix()
    glTranslatef(base_x, base_y, 0)

    # main structure - duita layer, rangin (neel-beguni), health bar e
    # alada kore dekhay tai eta neutral rakha hoyni, rangin kora hoise
    glColor3f(0.25, 0.35, 0.65)
    glPushMatrix()
    glTranslatef(0, 0, 30)
    cuboid(130, 90, 60)
    glPopMatrix()

    glColor3f(0.35, 0.5, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, 78)
    cuboid(90, 60, 40)
    glPopMatrix()

    # 4 kone choto tower (rangin)
    glColor3f(0.7, 0.4, 0.6)
    for sx in (-55, 55):
        for sy in (-38, 38):
            glPushMatrix()
            glTranslatef(sx, sy, 45)
            cuboid(16, 16, 90)
            glPopMatrix()

    # upore ekta pulsing glow beacon (color time onujayi bodlay, jate
    # "shine" korche mone hoy)
    t = time.time()
    glow = 0.6 + 0.4 * math.sin(t * 4)
    glColor3f(glow, 1.0 * glow, 0.3)
    glPushMatrix()
    glTranslatef(0, 0, 120 + 6 * math.sin(t * 3))
    gluSphere(gluNewQuadric(), 16, 10, 10)
    glPopMatrix()

    # beacon er charpashe ekta ghurte-thaka ring (choto sphere diye)
    glColor3f(0.3, 0.9, 1.0)
    for k in range(8):
        a = t * 2 + k * (math.pi / 4)
        glPushMatrix()
        glTranslatef(35 * math.cos(a), 35 * math.sin(a), 120)
        gluSphere(gluNewQuadric(), 5, 6, 6)
        glPopMatrix()

    glPopMatrix()


def draw_enemies():
    for e in enemies:
        ex, ey, ea, ehp, _ = e
        draw_tank(ex, ey, ea, ea, (0.85, 0.25, 0.2), 0.9)


def draw_shells():
    glColor3f(1, 0.9, 0.2)
    for s in shells:
        glPushMatrix()
        glTranslatef(s[0], s[1], s[2])
        gluSphere(gluNewQuadric(), 6, 6, 6)
        glPopMatrix()
    glColor3f(1, 0.4, 0.1)
    for s in enemy_shells:
        glPushMatrix()
        glTranslatef(s[0], s[1], s[2])
        gluSphere(gluNewQuadric(), 6, 6, 6)
        glPopMatrix()


def draw_powerups():
    for p in powerups:
        px_, py_, kind, phase = p
        z = 20 + 6 * math.sin(phase * 2)   # upor-niche bhashe
        glPushMatrix()
        glTranslatef(px_, py_, z)
        glRotatef(math.degrees(phase), 0, 0, 1)  # nijei ghore
        if kind == 'rapid':
            glColor3f(1, 0.8, 0)
        else:
            glColor3f(0, 0.8, 1)
        cuboid(20, 20, 20)
        glPopMatrix()


def draw_minimap():
    # corner e choto 2D map - orthographic projection e switch kore
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # map er background (choto quad, screen er upor-dan kone)
    mx, my, ms = WIN_W - 170, WIN_H - 170, 150

    def to_map(wx, wy):
        u = mx + (wx + ARENA) / (2 * ARENA) * ms
        v = my + (wy + ARENA) / (2 * ARENA) * ms
        return u, v

    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(mx, my, 0)
    glVertex3f(mx + ms, my, 0)
    glVertex3f(mx + ms, my + ms, 0)
    glVertex3f(mx, my + ms, 0)
    glEnd()

    glPointSize(6)
    glBegin(GL_POINTS)
    # base - yellow
    glColor3f(1, 1, 0)
    u, v = to_map(base_x, base_y)
    glVertex3f(u, v, 0)
    # player - cyan
    glColor3f(0.2, 0.7, 1)
    u, v = to_map(tank_x, tank_y)
    glVertex3f(u, v, 0)
    # enemies - red
    glColor3f(1, 0.2, 0.2)
    for e in enemies:
        u, v = to_map(e[0], e[1])
        glVertex3f(u, v, 0)
    # powerups - green
    glColor3f(0.2, 1, 0.4)
    for p in powerups:
        u, v = to_map(p[0], p[1])
        glVertex3f(u, v, 0)
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_2d_quad(x, y, w, h):
    glBegin(GL_QUADS)
    glVertex3f(x, y, 0)
    glVertex3f(x + w, y, 0)
    glVertex3f(x + w, y + h, 0)
    glVertex3f(x, y + h, 0)
    glEnd()


def draw_powerup_icons():
    # screen er upore active power-up gula choto icon hisebe dekhay.
    # ortho projection e switch kore 2D te draw kora hoy.
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # kon kon boost active, ekta list e rakhi
    active = []
    if boost_rapid > 0:
        active.append(('rapid', boost_rapid))
    if boost_speed > 0:
        active.append(('speed', boost_speed))

    # upore-majhe theke shuru kore ekta kore icon boshai
    icon = 34
    gap = 12
    total = len(active) * icon + max(0, len(active) - 1) * gap
    start_x = WIN_W / 2 - total / 2
    y = WIN_H - 50

    for idx, (kind, t) in enumerate(active):
        ix = start_x + idx * (icon + gap)
        # halka pulse animation - time onujayi choto-boro hoy
        pulse = 2 * math.sin(time.time() * 5 + idx)

        # icon er border/background
        glColor3f(0.15, 0.15, 0.15)
        draw_2d_quad(ix - 2, y - 2, icon + 4, icon + 4)

        if kind == 'rapid':
            glColor3f(1, 0.8, 0)      # rapid = holud
        else:
            glColor3f(0, 0.8, 1)      # speed = neel
        draw_2d_quad(ix - pulse, y - pulse, icon + 2 * pulse, icon + 2 * pulse)

        # koto second baki, choto kore niche
        draw_text(int(ix), int(y - 18), f"{t:.0f}s")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_coin(cx, cy, r, phase):
    # ekta coin - GL_POINTS diye ekta chakti (disk) er moto boshai.
    # phase diye "spin" er moto width change kore, tai coin ghurche mone hoy.
    squash = abs(math.cos(phase))          # 0..1, coin ghurle sorু-mota hoy
    wx = max(0.15, squash) * r
    glPointSize(3)
    glBegin(GL_POINTS)
    # bahirer holud ring
    glColor3f(1, 0.85, 0.1)
    steps = 22
    for k in range(steps):
        a = 2 * math.pi * k / steps
        glVertex3f(cx + wx * math.cos(a), cy + r * math.sin(a), 0)
    # bhitorer bhora ongsho
    glColor3f(1, 0.7, 0.0)
    for ry in range(int(-r), int(r), 3):
        half = wx * math.sqrt(max(0.0, 1 - (ry / r) ** 2))
        xr = int(-half)
        while xr < half:
            glVertex3f(cx + xr, cy + ry, 0)
            xr += 3
    glEnd()


def draw_score_coins():
    # score ta text na, coin diye dekhano hoy. Ekta boro coin (ghurche)
    # er pashe score number. Kotoshundor coin taw aste aste ghore.
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    t = time.time()
    # ekta boro coin, upor-niche olpo bhashe + ghore
    cx = 40
    cy = WIN_H - 40 + 3 * math.sin(t * 3)
    draw_coin(cx, cy, 16, t * 4)

    # coin er pashe score number
    draw_text(65, WIN_H - 48, f"x {score}")

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hp_overlay():
    # tank r base duitar HP capsule bar screen er upore-baa dike dekhay.
    # 2D overlay - tai shob camera angle theke shobshomoy clear dekha jay.
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    draw_hp_capsule(90, WIN_H - 118, "TANK", tank_hp, tank_max_hp)
    draw_hp_capsule(90, WIN_H - 158, "BASE", base_hp, base_max_hp)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud():
    draw_text(10, WIN_H - 72, f"Round: {round_no}")
    draw_text(10, WIN_H - 190, f"Camera: {'Orbit' if cam_mode == 0 else 'Follow'} (press V)")
    if paused:
        draw_text(WIN_W // 2 - 40, WIN_H // 2, "PAUSED (P)")
    if round_clear_msg > 0 and not game_over:
        draw_text(WIN_W // 2 - 90, WIN_H // 2 + 40, f"ROUND {round_no} - GET READY!")
    if game_over:
        draw_text(WIN_W // 2 - 80, WIN_H // 2 + 20, "GAME OVER")
        draw_text(WIN_W // 2 - 110, WIN_H // 2 - 10, f"Final Score: {score}")
        draw_text(WIN_W // 2 - 120, WIN_H // 2 - 40, "Press R to restart")


# ============================================================
# CAMERA
# ============================================================

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W / WIN_H, 0.1, 4500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if cam_mode == 0:
        # orbit camera - boro arena dekhar jonno aro pichone r upore
        r = math.radians(cam_orbit)
        cx = 1250 * math.sin(r)
        cy = 1250 * math.cos(r) - 120
        gluLookAt(cx, cy, 950, 0, 0, 0, 0, 0, 1)
    else:
        # follow camera - tank er thik pichone theke
        dx, dy = heading(tank_ang)
        cx = tank_x - dx * 240
        cy = tank_y - dy * 240
        gluLookAt(cx, cy, 175, tank_x + dx * 90, tank_y + dy * 90, 40, 0, 0, 1)


# ============================================================
# GAME LOGIC (update)
# ============================================================

def fire_player_shell():
    global fire_cd
    if fire_cd > 0:
        return
    dx, dy = heading(turret_ang)
    bx = tank_x + dx * 40
    by = tank_y + dy * 40
    # shell upore-shamne chhora hoy (arc), tai vz positive diye shuru
    shells.append([bx, by, 45, dx * shell_spd, dy * shell_spd, 190])
    gap = FIRE_GAP * (0.4 if boost_rapid > 0 else 1.0)
    fire_cd = gap


def enemy_fire(e, tx, ty):
    # target (tx,ty) er dike shell chhore
    dx = tx - e[0]
    dy = ty - e[1]
    d = math.hypot(dx, dy)
    if d < 1:
        return
    dx, dy = dx / d, dy / d
    # arc er jonno vz ektu distance onujayi dei, jate dur e thakle o pouchay
    vz = 120 + d * 0.25
    enemy_shells.append([e[0] + dx * 30, e[1] + dy * 30, 40,
                         dx * 320, dy * 320, vz])


def update_shells(dt):
    global score, base_hp
    # player shells
    alive = []
    for s in shells:
        s[0] += s[3] * dt
        s[1] += s[4] * dt
        s[2] += s[5] * dt
        s[5] -= GRAV * dt          # gravity - arc effect
        hit = False
        for e in enemies:
            # height window ta boro kora hoise (s[2] < 90) jate arc kora
            # shell o enemy te thik moto lage
            if dist(s[0], s[1], e[0], e[1]) < enemy_r + 12 and s[2] < 90:
                e[3] -= 25
                hit = True
                if e[3] <= 0:
                    score += 10
                break
        if hit:
            continue
        # shell mati te porle (z<=0) ba gol arena er baire gele shesh
        if s[2] > 0 and math.hypot(s[0], s[1]) < ARENA:
            alive.append(s)
    shells[:] = alive
    # dead enemy remove
    enemies[:] = [e for e in enemies if e[3] > 0]

    # enemy shells
    ea = []
    for s in enemy_shells:
        s[0] += s[3] * dt
        s[1] += s[4] * dt
        s[2] += s[5] * dt
        s[5] -= GRAV * dt
        # tank hit?
        if dist(s[0], s[1], tank_x, tank_y) < 45 and s[2] < 85:
            hurt_tank(12)
            continue
        # base hit?
        if dist(s[0], s[1], base_x, base_y) < 80 and s[2] < 90:
            base_hp -= 8
            continue
        if s[2] > 0 and math.hypot(s[0], s[1]) < ARENA:
            ea.append(s)
    enemy_shells[:] = ea


def hurt_tank(amount):
    global tank_hp, tank_hit_flash
    tank_hp -= amount
    tank_hit_flash = 0.5


def update_enemies(dt):
    for e in enemies:
        # player r base - jei ta kache, oitar dike e target kore
        d_player = dist(e[0], e[1], tank_x, tank_y)
        d_base = dist(e[0], e[1], base_x, base_y)
        if d_player < d_base:
            tx, ty = tank_x, tank_y
            d = d_player
        else:
            tx, ty = base_x, base_y
            d = d_base

        dx, dy = tx - e[0], ty - e[1]
        e[2] = math.degrees(math.atan2(dx, dy))  # target er dike mukh

        # target theke ektu dur e theme jay, tar por goli chhore
        if d > 160:
            nx = e[0] + dx / d * enemy_spd * dt
            ny = e[1] + dy / d * enemy_spd * dt
            if not blocked(nx, ny):
                e[0], e[1] = nx, ny

        # fire cooldown - target range er moddhe thakle fire kore
        e[4] -= dt
        if e[4] <= 0 and d < 500:
            enemy_fire(e, tx, ty)
            e[4] = random.uniform(1.5, 2.8)


def update_powerups(dt):
    global boost_rapid, boost_speed
    for p in powerups:
        p[3] += dt
    got = []
    for i, p in enumerate(powerups):
        if dist(p[0], p[1], tank_x, tank_y) < 40:
            if p[2] == 'rapid':
                boost_rapid = 8.0
            else:
                boost_speed = 8.0
            got.append(i)
    for i in reversed(got):
        powerups.pop(i)


def next_round_if_clear():
    global round_no, score, round_clear_msg
    if not enemies and not game_over:
        # wave clear - base ekhono thik thakle bonus
        if base_hp == base_max_hp:
            score += 25
        round_no += 1
        round_clear_msg = 2.0
        spawn_wave(2 + round_no)   # protita round e beshi enemy (harder)


def update(dt):
    global tank_x, tank_y, tank_ang, turret_ang, fire_cd
    global boost_rapid, boost_speed, tank_hit_flash, round_clear_msg
    global game_over

    # orbit camera ekhon nijei nore na - shudhu arrow key chaple ghore
    # (age nijei ghurchilo, seta off kora hoise)

    if game_over:
        return

    # timers
    if fire_cd > 0:
        fire_cd -= dt
    if boost_rapid > 0:
        boost_rapid = max(0, boost_rapid - dt)
    if boost_speed > 0:
        boost_speed = max(0, boost_speed - dt)
    if tank_hit_flash > 0:
        tank_hit_flash = max(0, tank_hit_flash - dt)
    if round_clear_msg > 0:
        round_clear_msg = max(0, round_clear_msg - dt)

    # turret ekhon nijei ghore na - tank body ja dike, turret o oi dike
    # thake (body er shathe move kore)
    turret_ang = tank_ang

    update_shells(dt)
    update_enemies(dt)
    update_powerups(dt)
    next_round_if_clear()

    # random e majhe majhe powerup spawn
    if random.random() < 0.012 and len(powerups) < 4:
        spawn_powerup()

    # lose condition
    if tank_hp <= 0 or base_hp <= 0:
        game_over = True


def idle():
    global last_time
    now = time.time()
    dt = now - last_time
    last_time = now
    dt = min(dt, 0.05)
    if not paused:
        update(dt)
    glutPostRedisplay()


# ============================================================
# INPUT
# ============================================================

def keyboard_down(key, x, y):
    global paused, cam_mode, tank_x, tank_y, tank_ang
    k = key.lower()
    if k == b'r':
        reset_game()
        return
    if k == b'p':
        paused = not paused
        return
    if k == b'v':
        cam_mode = 1 - cam_mode
        return
    if game_over or paused:
        return

    # per-press movement (KeyboardUpFunc allowed na, tai held-key na kore
    # protita press e ek dhap move kore - jotobar chapbe totobar agabe)
    step = 22.0 * (1.6 if boost_speed > 0 else 1.0)
    turn = 8.0
    dx, dy = heading(tank_ang)
    if k == b'w':
        nx, ny = tank_x + dx * step, tank_y + dy * step
        if math.hypot(nx, ny) < ARENA - 40 and not blocked(nx, ny):
            tank_x, tank_y = nx, ny
    elif k == b's':
        nx, ny = tank_x - dx * step, tank_y - dy * step
        if math.hypot(nx, ny) < ARENA - 40 and not blocked(nx, ny):
            tank_x, tank_y = nx, ny
    elif k == b'a':
        tank_ang += turn
    elif k == b'd':
        tank_ang -= turn
    elif k == b' ':
        fire_player_shell()


def special_keys(key, x, y):
    # arrow key diye orbit camera manually o ghurano jay
    global cam_orbit
    if key == GLUT_KEY_LEFT:
        cam_orbit = (cam_orbit - 6) % 360
    elif key == GLUT_KEY_RIGHT:
        cam_orbit = (cam_orbit + 6) % 360


def mouse(button, state, x, y):
    if game_over or paused:
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_player_shell()


# ============================================================
# DISPLAY
# ============================================================

def show_screen():
    glClearColor(0.16, 0.18, 0.45, 1)   # sky er upor er neel er shathe match
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)

    setup_camera()

    draw_sky()
    draw_ground()
    draw_boundary()
    draw_obstacles()
    draw_base()
    draw_player_tank()
    draw_enemies()
    draw_shells()
    draw_powerups()

    draw_minimap()
    draw_score_coins()
    draw_powerup_icons()
    draw_hp_overlay()
    draw_hud()

    glutSwapBuffers()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Tank Battle")

    reset_game()

    glutDisplayFunc(show_screen)
    glutKeyboardFunc(keyboard_down)
    glutSpecialFunc(special_keys)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
