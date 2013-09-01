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

def rotate(v, angle):
    s = math.sin(angle)
    c = math.cos(angle)
    return vec2(v.x * c - v.y * s, v.x * s + v.y * c)

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
    def __init__(self, pos):
        super(Cat, self).__init__(pos, textures['cat'])

    def on_tick(self):
        self.pos += bacon.timestep * vec2(-100, 0)

class Game(bacon.Game):
    def __init__(self):
        self.cats = []

    def on_init(self):
        print bacon.window.width, bacon.window.height
        global earthpos
        earthpos = vec2(bacon.window.width / 2, bacon.window.height / 2)

    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.q:
                sys.exit()
            elif key == bacon.Keys.f:
                bacon.window.fullscreen = not bacon.window.fullscreen

    def on_mouse_button(self, button, pressed):
        # when left mouse button is released
        if button == bacon.MouseButtons.left and not pressed: 
            self.cats.append(Cat(earth.pos - vec2(0, 50)))

    def on_tick(self):
        bacon.clear(0.2, 0.2, 0.2, 1.0)

        moon.on_tick()
        for cat in self.cats:
            cat.on_tick()

        earth.draw()
        moon.draw()
        for cat in self.cats:
            cat.draw()

        # print moon.pos, bacon.window.content_scale

earth = Sprite(vec2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2), textures['earth'])
moon = Moon(earth, 600)
bacon.run(Game())