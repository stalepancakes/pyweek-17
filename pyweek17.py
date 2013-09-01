import sys
import math
import bacon
from vectypes import *

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1200

MOON_DISTANCE = 500
MOUSE_SPEED = 1
CAT_SPAWN_COOLDOWN = 0.3

bacon.window.resizable = True
# TODO - need to wait for bug to be fixed
#bacon.window.target = bacon.Image(width=1920, height=1200, atlas=0)
bacon.window.fullscreen = True

textures = {
    'earth': bacon.Image('res/earth.png'),
    'mouse': bacon.Image('res/mouse.png'),
    'moon': bacon.Image('res/moon.png'),
    'cat': bacon.Image('res/cat.png')
}

font = bacon.Font(None, 16)

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
        assert image.height == image.width
        self.radius = image.width / 2

    def draw(self):
        ox = self.image.width / 2
        oy = self.image.height / 2

        bacon.push_transform()
        bacon.translate(self.pos.x, self.pos.y)
        bacon.draw_image(self.image, -ox, -oy)
        bacon.pop_transform()

    def collides_with(self, thing):
        return length(self.pos - thing.pos) < self.radius + thing.radius

class Moon(Sprite):
    def __init__(self, earth, distance):
        self.earth = earth
        self.distance = distance
        self.angle = 0
        super(Moon, self).__init__(self.calc_position(), textures['moon'])

    def on_tick(self):
        self.pos = self.calc_position()
        self.angle += bacon.timestep / 3.0
        self.draw()

    def calc_position(self):
        return self.earth.pos + rotate(vec2(MOON_DISTANCE, 0), self.angle)

class Cat(Sprite):
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
        G = 3600
        earth_G = self.force_of_gravity(earth)
        moon_G = self.force_of_gravity(moon)
        a = earth_G + moon_G
        verlet_step(self, a * t * t)

class Mouse(Sprite):
    def __init__(self, pos):
        super(Mouse, self).__init__(pos, textures['mouse'])
        self.dead = False

    def on_tick(self):
        to_moon = normalize(moon.pos - self.pos)
        self.pos += to_moon * MOUSE_SPEED

class CatSpawner(object):
    def __init__(self):
        self.cooldown = 0
        self.launch_power = 12

    def try_spawn(self, game):
        if self.cooldown <= 0:
            direction = normalize(vec2(bacon.mouse.x, bacon.mouse.y) - earth.pos)
            game.cats.append(Cat(earth.pos + 50*direction, direction, self.launch_power))
            self.cooldown = CAT_SPAWN_COOLDOWN

    def on_tick(self, game):
        if bacon.mouse.left:
            self.try_spawn(game)

        bacon.draw_string(font, 'Power: %d' % self.launch_power, 
            x=0, y=0,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

        self.cooldown -= bacon.timestep

class Game(bacon.Game):
    def __init__(self):
        self.cats = []
        self.mice = []
        self.down = False
        self.spawn_timer = 1
        self.cat_spawner = CatSpawner()

    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.q:
                sys.exit()
            elif key == bacon.Keys.f:
                bacon.window.fullscreen = not bacon.window.fullscreen

    def on_mouse_scroll(self, dx, dy):
        isUp = dy == 1.0
        if isUp:
            self.cat_spawner.launch_power += 1
        else:
            self.cat_spawner.launch_power -= 1

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

    def on_tick(self):
        bacon.clear(0.1, 0.1, 0.1, 1.0)

        self.cat_spawner.on_tick(self)

        bacon.draw_string(font, 'spawn_timer: %f' % self.spawn_timer, 
            x=0, y=20,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

        self.handle_collision()

        if len(self.cats) > 200:
            self.cats = self.cats[10:]

        self.spawn_timer -= bacon.timestep

        if self.spawn_timer < 0:
            self.spawn_timer = 5
            self.mice.append(Mouse(vec2(100, 100)))

        moon.on_tick()
        for cat in self.cats:
            cat.on_tick()
            cat.draw()
        for mouse in self.mice:
            mouse.on_tick()
            mouse.draw()
        earth.draw()
        moon.draw()

        line_end = earth.pos + (100+self.cat_spawner.launch_power*4) * normalize(vec2(bacon.mouse.x, bacon.mouse.y) - earth.pos)
        bacon.draw_line(earth.pos.x, earth.pos.y, line_end.x, line_end.y)

earth = Sprite(vec2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), textures['earth'])
moon = Moon(earth, 600)
bacon.run(Game())