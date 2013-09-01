import sys
import bacon

bacon.window.fullscreen = True

class Game(bacon.Game):
    def on_key(self, key, value):
        if value:
            if key == bacon.Keys.q:
                sys.exit()
            elif key == bacon.Keys.f:
                bacon.window.fullscreen = not bacon.window.fullscreen

    def on_tick(self):
        bacon.clear(0, 0, 0, 1)

        bacon.fill_rect(100,100,200,200)

        bacon.fill_rect(500,500,600,600)
        
bacon.run(Game())
