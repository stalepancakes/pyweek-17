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

EARTH_RADIUS = 75
MOON_SECONDS_PER_ROTATION = 15.0

bacon.window.resizable = True
bacon.window.fullscreen = True
bacon.window.target = bacon.Image(width=1920, height=1200, atlas=0)

textures = {
    'catapult': bacon.Image('res/catapult.png'),
    'earth': bacon.Image('res/earth.png'),
    'mouse': bacon.Image('res/mouse.png'),
    'moon': bacon.Image('res/moon.png'),
    'cat': bacon.Image('res/cat.png')
}

font = bacon.Font(None, 16)

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
        ox = self.image.width / 2
        oy = self.image.height / 2

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

class Moon(RoundSprite):
    def __init__(self, earth, distance):
        self.earth = earth
        self.distance = distance
        self.angle = 0
        super(Moon, self).__init__(self.calc_position(self.angle), textures['moon'])

    def clone(self):
        m = Moon(self.earth, self.distance)
        m.pos = self.pos
        m.angle = self.angle
        return m

    def on_tick(self):
        self.update_by(bacon.timestep)
        self.draw()

    def update_by(self, t):
        self.pos = self.future_position(t)
        self.angle += 2 * math.pi * t / MOON_SECONDS_PER_ROTATION

    def calc_position(self, angle):
        return self.earth.pos + rotate(vec2(MOON_DISTANCE, 0), angle)

    def future_position(self, t):
        return self.calc_position(self.angle + t / MOON_SECONDS_PER_ROTATION)

class Cat(RoundSprite):
    def __init__(self, pos, direction, power):
        super(Cat, self).__init__(pos, textures['cat'])
        self.dead = False
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
        earth_G = self.force_of_gravity(earth)
        moon_G = self.force_of_gravity(moon)
        a = earth_G + moon_G
        verlet_step(self, a * t * t)

class Mouse(RoundSprite):
    def __init__(self, pos):
        super(Mouse, self).__init__(pos, textures['mouse'])
        self.dead = False

    def on_tick(self):
        time_to_moon = 0
        for i in range(5):
            time_to_moon = length(moon.future_position(time_to_moon) - self.pos) / MOUSE_SPEED
            # f = moon.future_position(time_to_moon)
            # bacon.draw_line(self.pos.x, self.pos.y, f.x, f.y)

        to_target = normalize(moon.future_position(time_to_moon) - self.pos)
        self.pos += to_target * MOUSE_SPEED * bacon.timestep

class Catapult(Sprite):
    def __init__(self):
        super(Catapult, self).__init__(vec2(0, 0), textures['catapult'])
        self.pos = earth.pos - vec2(0, earth.radius) - vec2(0, -5 + self.image.height / 2)

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

        x = 20.0
        y = 150.0
        a = 4.0
        b = 18.0

        l = clamp(l, x, y)
        return a + (b - a) * ((l - x) / (y - x))
    
    def try_spawn(self, game):
        if self.cooldown <= 0:
            offset = (earth.radius + textures['cat'].width / 2 + 1) * self.direction()
            game.cats.append(Cat(self.pos, self.direction(), self.launch_power()))
            self.cooldown = CAT_SPAWN_COOLDOWN

    def on_tick(self, game):
        if bacon.mouse.left:
            self.try_spawn(game)

        bacon.draw_string(font, 'Power: %d' % self.launch_power(), 
            x=0, y=0,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

        line_end = self.pos + self.launch_power() * 8 * self.direction()
        bacon.draw_line(self.pos.x, self.pos.y, line_end.x, line_end.y)

        self.cooldown -= bacon.timestep

        self.simulate_launch()

    def simulate_launch(self):
        f_moon = moon.clone()
        cat = Cat(self.pos, self.direction(), self.launch_power())
        v = []
        for i in range(100):
            v.append(cat.pos)
            dt = 1 / 60.0
            f_moon.update_by(dt)
            cat.update_by(dt, earth, f_moon)
        
        bacon.push_color()
        bacon.set_color(0.4,0.4,0.4,1.0)
        for i in range(1, len(v)):
            bacon.draw_line(v[i].x, v[i].y, v[i-1].x, v[i-1].y)
        bacon.pop_color()


class Game(bacon.Game):
    def __init__(self):
        self.cats = []
        self.mice = []
        self.down = False
        self.spawn_timer = MOUSE_INITIAL_SPAWN_DELAY
        self.cat_spawner = CatSpawner()
        self.catapult = Catapult()

    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.q:
                sys.exit()
            elif key == bacon.Keys.f:
                bacon.window.fullscreen = not bacon.window.fullscreen

    def handle_collision(self):
        for c in self.cats:
            if c.collides_with(earth) or c.collides_with(moon):
                c.dead = True

        for m in self.mice:
            if m.collides_with(earth) or m.collides_with(moon):
                m.dead = True

        for x in self.cats:
            for y in self.mice:
                if x.collides_with(y):
                    x.dead = True
                    y.dead = True

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
        bacon.clear(0.1, 0.1, 0.1, 1.0)

        bacon.draw_string(font, 'spawn_timer: %f' % self.spawn_timer, 
            x=0, y=20,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

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
            cat.draw()
        for mouse in self.mice:
            mouse.on_tick()
            mouse.draw()
        earth.draw()
        moon.draw()
        catapult.draw()
        self.cat_spawner.on_tick(self)

earth = RoundSprite(vec2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), textures['earth'])
moon = Moon(earth, 600)
catapult = Catapult()
bacon.run(Game())