import sys
import math
import bacon
import random
from vectypes import *

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1200

MOON_DISTANCE = 500.0
MOUSE_SPEED = 60.0
MOUSE_SPAWN_COOLDOWN = 4.0
MOUSE_INITIAL_SPAWN_DELAY = 1.0
CAT_SPAWN_COOLDOWN = 0.3
CAT_ATTACK_RANGE = 50

EARTH_RADIUS = 75
MOON_SECONDS_PER_ROTATION = 15.0

MOON_HEALTHBAR_OFFSET = 0 
MOON_HEALTHBAR_HEIGHT = 2

MOUSE_DAMAGE = 0.1

GAME_OVER_FADE = 2.0
GAME_OVER_FADETEXT = 1.0
GAME_OVER_GRAVITY = 3.5
GAME_OVER_AFTERFADE_WAIT = 0.3

CATAPULT_FIRE_TIME = 0.15

CATAPULT_START_ANGLE = -30
CATAPULT_END_ANGLE = 90

bacon.window.resizable = True
bacon.window.fullscreen = True
bacon.window.target = bacon.Image(width=1920, height=1200, atlas=0)

textures = {
    'catapult_frame': bacon.Image('res/catapultframe.png'),
    'catapult_spoon': bacon.Image('res/spoon.png'),
    'earth': bacon.Image('res/earth.png'),
    'mouse': bacon.Image('res/mouse.png'),
    'moon': bacon.Image('res/moon.png'),
    'cat': bacon.Image('res/cat.png')
}

sounds = {
    'squeak': bacon.Sound('res/squeak.wav'),
    'explosion': bacon.Sound('res/explosion.wav'),
    'catapult': bacon.Sound('res/catapult.wav')
}

moon_eated_states = [100, 75, 50, 25, 15, 5]

font_16 = bacon.Font(None, 16)
font_24 = bacon.Font(None, 24)
font_72 = bacon.Font(None, 72)

def clamp(v, a, b):
    return min(b, max(a, v))

def rotate(v, angle):
    s = math.sin(angle)
    c = math.cos(angle)
    return vec2(v.x * c - v.y * s, v.x * s + v.y * c)

def verlet_init(o, initial_v):
    assert hasattr(o, 'pos')
    o.last_pos = o.pos - initial_v
def verlet_step(o, a):
    new_pos = (2 * o.pos) - o.last_pos + a
    o.last_pos, o.pos = o.pos, new_pos

class Sprite(object):
    def __init__(self, pos, image):
        self.pos = pos
        self.image = image

    def draw(self):
        ox, oy = self.image.width / 2, self.image.height / 2

        bacon.push_transform()
        bacon.translate(self.pos.x, self.pos.y)
        bacon.draw_image(self.image, -ox, -oy)
        bacon.pop_transform()

class RoundSprite(Sprite):
    def __init__(self, pos, image):
        super(RoundSprite, self).__init__(pos, image)
        self.radius = image.width / 2

    def collides_with(self, thing):
        return length(self.pos - thing.pos) < self.radius + thing.radius

class BoundedSphere(object):
    def __init__(self, pos, radius):
        self.pos = pos
        self.radius = radius

    def collides_with(self, thing):
        return length(self.pos - thing.pos) < self.radius + thing.radius

class Moon(RoundSprite):
    def __init__(self, earth, distance):
        self.earth = earth
        self.distance = distance
        self.angle = 0
        self.health = 1.0
        super(Moon, self).__init__(self.calc_position(self.angle), textures['moon'])

    def clone(self):
        m = Moon(self.earth, self.distance)
        m.pos = self.pos
        m.angle = self.angle
        return m

    def draw(self):
        super(Moon, self).draw()
        healthbar_x = self.pos.x - self.image.width / 2
        healthbar_w = self.image.width
        healthbar_mid = healthbar_x + self.health * healthbar_w
        healthbar_y = self.pos.y - self.image.height / 2 - MOON_HEALTHBAR_OFFSET
        bacon.push_color()
        bacon.set_color(1,0,0,1)
        bacon.draw_rect(healthbar_mid, healthbar_y, healthbar_x + healthbar_w, healthbar_y + MOON_HEALTHBAR_HEIGHT)
        bacon.set_color(0,1,0,1)
        bacon.draw_rect(healthbar_x, healthbar_y, healthbar_mid, healthbar_y + MOON_HEALTHBAR_HEIGHT)
        bacon.pop_color()

    def on_tick(self):
        self.update_by(bacon.timestep)

    def update_by(self, t):
        self.pos = self.future_position(t)
        self.angle += 2 * math.pi * t / MOON_SECONDS_PER_ROTATION

    def calc_position(self, angle):
        return self.earth.pos + rotate(vec2(MOON_DISTANCE, 0), angle)

    def future_position(self, t):
        return self.calc_position(self.angle + t / MOON_SECONDS_PER_ROTATION)

    def take_damage(self, amount):
        for v in moon_eated_states:
            if self.health > v / 100.0:
                self.image = bacon.Image('res/moon%d.png' % v)
                self.health = v / 100.0
                break
        else:
            scene.game = GameOverScreen(scene.game)

class Cat(RoundSprite):
    def __init__(self, pos, direction, power):
        super(Cat, self).__init__(pos, textures['cat'])
        self.dead = False
        self.target = None
        self.attack_speed = 0
        self.attack_sphere = BoundedSphere(self.pos, CAT_ATTACK_RANGE)
        verlet_init(self, power * direction)

    def force_of_gravity(self, body):
        d = body.pos - self.pos
        r = length(d) / 1000
        return 10*normalize(d) / (r * r)

    def on_tick(self):
        # TODO - do fixed timestep properly
        t = bacon.timestep
        t = 1/60.
        self.update_by(t, earth, moon)

    def update_by(self, t, earth, moon):
        if self.target is None:
            earth_G = self.force_of_gravity(earth)
            moon_G = self.force_of_gravity(moon)
            a = earth_G + moon_G
            verlet_step(self, a * t * t)
            self.attack_sphere.pos = self.pos
        else:
            to_target = normalize(self.target.pos - self.pos)
            self.pos += to_target * self.attack_speed * t
            self.last_pos = self.pos
            if self.target.dead:
                self.dead = True

    def mouse_in_attack_range(self, mouse):
        if self.target is None:
            self.target = mouse
            self.attack_speed = (1/bacon.timestep) * length(self.pos - self.last_pos)

class Mouse(RoundSprite):
    def __init__(self, pos):
        super(Mouse, self).__init__(pos, textures['mouse'])
        self.dead = False
        sounds['squeak'].play()

    def on_tick(self):
        time_to_moon = 0
        for i in range(5):
            time_to_moon = length(moon.future_position(time_to_moon) - self.pos) / MOUSE_SPEED

        to_target = normalize(moon.future_position(time_to_moon) - self.pos)
        self.pos += to_target * MOUSE_SPEED * bacon.timestep

class Catapult(Sprite):
    def __init__(self):
        super(Catapult, self).__init__(vec2(0, 0), textures['catapult_frame'])
        self.pos = earth.pos - vec2(0, earth.radius) - vec2(0, -5 + self.image.height / 2)
        self.arm = textures['catapult_spoon']
        self.angle = 0
        self.t = 1

    def on_tick(self):
        if self.t != 1:
            self.t += bacon.timestep / CATAPULT_FIRE_TIME
            self.angle = math.pi * self.interp(self.t, CATAPULT_START_ANGLE, CATAPULT_END_ANGLE) / 180.0
            if self.t >= 1 or self.angle > self.end_angle:
                self.t = 1
                self.on_fling()
                self.on_fling = None

    def interp(self, t, a, b):
        return a + t * (b-a)

    def draw(self):
        super(Catapult, self).draw()

        ox, oy = self.arm.width / 2, self.arm.height / 2
        bacon.push_transform()
        bacon.translate(self.pos.x + 17, self.pos.y - 15)
        bacon.rotate(self.angle)
        bacon.draw_image(self.arm, -2*ox + 16, -oy)
        bacon.pop_transform()

        self.angle = 0

    def get_launch_pos(self, direction):
        end_angle = self.get_end_angle(direction)
        return self.pos + vec2(17, -15) + rotate(vec2(-self.arm.width + 25, 0), end_angle)

    def get_end_angle(self, direction):
        return clamp(math.atan2(direction.x, -1 * direction.y), 0, math.pi/2)

    def fling(self, direction, on_fling):
        self.t = 0
        self.end_angle = self.get_end_angle(direction)
        self.on_fling = on_fling

class CatSpawner(object):
    def __init__(self):
        self.cooldown = 0
        self.pos = catapult.pos - vec2(0, 10)

    def direction(self):
        return normalize(vec2(bacon.mouse.x, bacon.mouse.y) - self.pos)
    def launch_power(self):
        # draw from x to y
        # power is from a to b
        l = length(vec2(bacon.mouse.x, bacon.mouse.y) - self.pos)

        x = 50.0
        y = 650.0
        a = 4.0
        b = 14.0

        l = clamp(l, x, y)
        return a + (b - a) * ((l - x) / (y - x))
    
    def try_spawn(self, game):
        if self.cooldown <= 0:
            direction = self.direction()
            launch_power = self.launch_power()
            pos = catapult.get_launch_pos(direction)
            offset = (earth.radius + textures['cat'].width / 2 + 1) * self.direction()
            self.cooldown = CAT_SPAWN_COOLDOWN
            sounds['catapult'].play()
            catapult.fling(self.direction(), lambda: game.cats.append(Cat(pos, direction, launch_power)))

    def on_tick(self, game):
        if bacon.mouse.left:
            self.try_spawn(game)

        self.cooldown -= bacon.timestep

    def draw(self, game):
        bacon.draw_string(font_16, 'Power: %d' % self.launch_power(), 
            x=0, y=0,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

        self.simulate_launch()

    def simulate_launch(self):
        f_moon = moon.clone()
        pos = catapult.get_launch_pos(self.direction())
        cat = Cat(pos, self.direction(), self.launch_power())
        v = []
        TOTAL_STEPS = 100
        for i in range(TOTAL_STEPS):
            v.append(cat.pos)
            dt = 1 / 60.0
            f_moon.update_by(dt)
            cat.update_by(dt, earth, f_moon)
            if cat.collides_with(f_moon) or cat.collides_with(earth):
                break
        
        bacon.push_color()
        c = 0.4
        for i in range(1, len(v)):
            bacon.set_color(c, c, c, 0)
            bacon.draw_line(v[i].x, v[i].y, v[i-1].x, v[i-1].y)
            c -= 0.4 * (1.0 / TOTAL_STEPS)
        bacon.pop_color()


class Game(bacon.Game):
    def __init__(self):
        self.cats = []
        self.mice = []
        self.down = False
        self.spawn_timer = MOUSE_INITIAL_SPAWN_DELAY
        self.cat_spawner = CatSpawner()
        self.catapult = Catapult()
        self.score = 0

    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.w:
                scene.game = GameOverScreen(self)

    def handle_collision(self):
        for c in self.cats:
            if c.collides_with(earth) or c.collides_with(moon):
                c.dead = True

        for m in self.mice:
            if m.collides_with(earth):
                m.dead = True
            elif m.collides_with(moon):
                moon.take_damage(MOUSE_DAMAGE)
                m.dead = True

        for cat in self.cats:
            for mouse in self.mice:
                if cat.attack_sphere.collides_with(mouse):
                    cat.mouse_in_attack_range(mouse)
                if cat.collides_with(mouse):
                    cat.dead = True
                    mouse.dead = True
                    sounds['explosion'].play()
                    self.score += 5

        self.cats[:] = [c for c in self.cats if not c.dead]
        self.mice[:] = [m for m in self.mice if not m.dead]

    def find_mouse_spawn(self):
        i = random.uniform(0, 2*WINDOW_WIDTH + 2*WINDOW_HEIGHT-1)
        if i < WINDOW_WIDTH:  return vec2(i, 0)
        i -= WINDOW_WIDTH
        if i < WINDOW_WIDTH:  return vec2(i, WINDOW_HEIGHT)
        i -= WINDOW_WIDTH
        if i < WINDOW_HEIGHT: return vec2(0, i)
        i -= WINDOW_HEIGHT
        assert i < WINDOW_HEIGHT
        return vec2(WINDOW_WIDTH, i)
        
    def on_tick(self):
        bacon.clear(0.1, 0.1, 0.1, 0.0)
        bacon.draw_string(font_16, 'spawn_timer: %f' % self.spawn_timer, 
            x=0, y=20,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

        bacon.draw_string(font_24, 'Score: %d' % self.score,
            x=WINDOW_WIDTH/2, y=0,
            align=bacon.Alignment.center,
            vertical_align=bacon.VerticalAlignment.top)

        steps = 1
        if bacon.Keys.space in bacon.keys:
            steps = 8

        for i in range(steps):
            self.update_state()

        for cat in self.cats:
            cat.draw()
        for mouse in self.mice:
            mouse.draw()
        earth.draw()
        moon.draw()
        catapult.draw()
        self.cat_spawner.draw(self)

    def update_state(self):
        self.handle_collision()

        if len(self.cats) > 200:
            self.cats = self.cats[10:]

        self.spawn_timer -= bacon.timestep

        if self.spawn_timer < 0:
            self.spawn_timer = MOUSE_SPAWN_COOLDOWN
            self.mice.append(Mouse(self.find_mouse_spawn()))

        moon.on_tick()
        for cat in self.cats:
            cat.on_tick()
        for mouse in self.mice:
            mouse.on_tick()

        catapult.on_tick()
        self.cat_spawner.on_tick(self)

class GameOverScreen(bacon.Game):
    def __init__(self, game):
        self.game = game
        self.t = 0
        self.fade_image = None
        self.y = 0
        self.yvel = 0

        self.state = "fade-in"
        
    def on_tick(self):
        bacon.clear(0.1, 0.1, 0.1, 0.0)
        bacon.clear(0,0,0,0)

        if self.fade_image is None:
            self.fade_image = bacon.Image(width = WINDOW_WIDTH, height = WINDOW_HEIGHT)
            bacon.push_target(self.fade_image)
            self.game.on_tick()
            bacon.pop_target()

        if self.state == "fade-in":
            self.t += bacon.timestep / GAME_OVER_FADE
            self.yvel += bacon.timestep * GAME_OVER_GRAVITY
            self.y += self.yvel

            bacon.push_color()
            bacon.set_color(0.1, 0.1, 0.1, 1)
            bacon.fill_rect(0,0, WINDOW_WIDTH, self.y)
            bacon.pop_color()

            bacon.draw_image(self.fade_image, 0, self.y)

            bacon.push_color()
            bacon.set_color(0,0,0, self.smoothstep(self.t))
            bacon.fill_rect(0,0, WINDOW_WIDTH, WINDOW_HEIGHT)
            bacon.pop_color()

            if self.t > 1:
                self.state = "pre-game-over"
                self.t = GAME_OVER_AFTERFADE_WAIT

        elif self.state == "pre-game-over":
            self.t -= bacon.timestep
            if self.t <= 0:
                self.state = "game-over"
                self.t = 1

        elif self.state == "game-over" or self.state == "game-over-score":
            bacon.draw_string(font_72, 'GAME OVER',
                x=WINDOW_WIDTH/2, y=WINDOW_HEIGHT/2,
                align=bacon.Alignment.center,
                vertical_align=bacon.VerticalAlignment.center)

            if self.state == "game-over-score":
                bacon.draw_string(font_24, 'SCORE: %d' % self.game.score,
                    x=WINDOW_WIDTH/2, y=WINDOW_HEIGHT/2 + 72,
                    align=bacon.Alignment.center,
                    vertical_align=bacon.VerticalAlignment.center)

            bacon.push_color()
            bacon.set_color(0,0,0, self.smoothstep(self.t))
            if self.state == "game-over":
                bacon.fill_rect(0,0, WINDOW_WIDTH, WINDOW_HEIGHT)
            else:
                bacon.fill_rect(0, WINDOW_HEIGHT/2+36, WINDOW_WIDTH, WINDOW_HEIGHT)
            bacon.pop_color()

            if self.t > 0:
                self.t -= bacon.timestep / GAME_OVER_FADETEXT

            if self.state == "game-over" and self.t <= 0:
                self.t = 1
                self.state = "game-over-score"

    def smoothstep(self, t):
        return 3*t*t - 2*t*t*t

class SceneDispatcher(bacon.Game):
    def __init__(self, game):
        self.game = game

    def on_tick(self):
        self.game.on_tick()

    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.q:
                sys.exit()
                return
            elif key == bacon.Keys.f:
                bacon.window.fullscreen = not bacon.window.fullscreen
                return
        self.game.on_key(key, value)

earth = RoundSprite(vec2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), textures['earth'])
moon = Moon(earth, 600)
catapult = Catapult()
scene = SceneDispatcher(Game())
bacon.run(scene)
