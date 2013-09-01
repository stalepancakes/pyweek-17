import sys
import math
import bacon
from vectypes import *

WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1200

bacon.window.resizable = True
# TODO - need to wait for bug to be fixed
#bacon.window.target = bacon.Image(width=1920, height=1200, atlas=0)
bacon.window.fullscreen = True

textures = {
    'earth': bacon.Image('res/earth.png'),
    'moon': bacon.Image('res/moon.png'),
    'cat': bacon.Image('res/cat.png')
}

MOON_DISTANCE = 500

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

    def draw(self):
        ox = self.image.width / 2
        oy = self.image.height / 2

        bacon.push_transform()
        bacon.translate(self.pos.x, self.pos.y)
        bacon.draw_image(self.image, -ox, -oy)
        bacon.pop_transform()

class Moon(Sprite):
    def __init__(self, earth, distance):
        self.earth = earth
        self.distance = distance
        self.angle = 0
        super(Moon, self).__init__(self.calc_position(), textures['moon'])

    def on_tick(self):
        self.pos = self.calc_position()
        self.angle += bacon.timestep #/ 3.0

    def calc_position(self):
        return self.earth.pos + rotate(vec2(MOON_DISTANCE, 0), self.angle)

class Cat(Sprite):
    def __init__(self, pos, direction, power):
        super(Cat, self).__init__(pos, textures['cat'])
        verlet_init(self, power * direction)

    def force_of_gravity(self, body):
        d = body.pos - self.pos
        r = length(d) / 1000
        return 10*normalize(d) / (r * r)

    def on_tick(self):
        t = bacon.timestep
        t = 1/60.
        G = 3600
        # earth_G = t2 * G * normalize(earth.pos - self.pos)
        # moon_G = 0.15 * t2 * G * normalize(moon.pos - self.pos)
        earth_G = self.force_of_gravity(earth)
        moon_G = self.force_of_gravity(moon)
        a = earth_G + moon_G
        verlet_step(self, a * t * t)

    def collides(self):
        return length(earth.pos - self.pos) < 49 \
            or length(moon.pos - self.pos) < 49

class Game(bacon.Game):
    def __init__(self):
        self.cats = []
        self.down = False
        self.power = 12

    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.q:
                sys.exit()
            elif key == bacon.Keys.f:
                bacon.window.fullscreen = not bacon.window.fullscreen

    def on_mouse_button(self, button, pressed):
        # when left mouse button is released
        if button == bacon.MouseButtons.left and pressed: 
            self.down = True
        if button == bacon.MouseButtons.left and not pressed: 
            self.down = False

    def on_mouse_scroll(self, dx, dy):
        isUp = dy == 1.0
        if isUp:
            self.power += 1
        else:
            self.power -= 1

    def on_tick(self):
        bacon.clear(0.1, 0.1, 0.1, 1.0)

        bacon.draw_string(font, 'Power: %d' % self.power, 
            x=0, y=0,
            align=bacon.Alignment.left,
            vertical_align=bacon.VerticalAlignment.top)

        if self.down:
            direction = normalize(vec2(bacon.mouse.x, bacon.mouse.y) - earth.pos)
            self.cats.append(Cat(earth.pos + 50*direction, direction, self.power))

        self.cats = [cat for cat in self.cats if not cat.collides()]

        if len(self.cats) > 200:
            self.cats = self.cats[10:]

        moon.on_tick()
        for cat in self.cats:
            cat.on_tick()

        earth.draw()
        moon.draw()
        for cat in self.cats:
            cat.draw()
        to_cursor = normalize(vec2(bacon.mouse.x, bacon.mouse.y) - earth.pos)
        bacon.draw_line(earth.pos.x, earth.pos.y, earth.pos.x + 100*to_cursor.x, earth.pos.y + 100*to_cursor.y)

earth = Sprite(vec2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), textures['earth'])
moon = Moon(earth, 600)
bacon.run(Game())