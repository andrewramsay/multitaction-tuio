from __future__ import division
import pyglet
from pyglet.gl import *
from pythonosc import dispatcher, osc_server
from threading import Thread
from copy import deepcopy

MAX_FINGERS = 10
MAX_SCALE = 25
TUIO_PORT = 3333
FPS = 60

class TactionDemo(pyglet.window.Window):

    def __init__(self):
        screens = pyglet.canvas.Display().get_screens()
        super(TactionDemo, self).__init__(screens[1].width, screens[1].height, fullscreen=True, vsync=False, screen=screens[1], mode=screens[1].get_modes()[0])
        self.fingers = []
        self.marker_image = pyglet.image.load('target.png')
        self.marker_image.anchor_x = int(self.marker_image.width / 2)
        self.marker_image.anchor_y = int(self.marker_image.height / 2)
        self.markers = [pyglet.sprite.Sprite(self.marker_image, x=-100, y=-100) for x in range(MAX_FINGERS)]
        self.status = pyglet.text.Label('Fingers: ', font_name='Lucida Sans Mono', font_size=20, x=30, y=self.height-40, anchor_x='left', anchor_y='top')

    def run(self):
        disp = dispatcher.Dispatcher()
        disp.map("/tuio/2Dcur", self.handle_2Dcur)
        self.serv = osc_server.ThreadingOSCUDPServer(('', TUIO_PORT), disp)
        self.serv_thread = Thread(target=self.serv.serve_forever)
        self.serv_thread.daemon = True
        self.serv_thread.start()
        pyglet.clock.schedule_interval(self.update, 1/FPS)
        pyglet.app.run()

    def update(self, dt):
        self.draw(dt)

    def draw(self, dt):
        glClearColor(0.0, 0.0, 0.0, 1)
        self.clear()

        self.status.text = 'Fingers: %d' % (len(self.fingers))
        self.status.draw()

        glLineWidth(3.0)
        glColor3f(1,1,1)
        for i, f in enumerate(self.fingers):
            self.markers[i].x = self.width * f[1]
            self.markers[i].y = self.height - (self.height * f[2])
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2f', (self.markers[i].x, self.markers[i].y, self.markers[i].x + (f[3] * self.width), self.markers[i].y - (self.height * f[4]))))
            self.markers[i].scale = 1 + (MAX_SCALE * f[5])
            self.markers[i].draw()

    def handle_2Dcur(self, addr, *args):
        """This callback will get triggered each time a new TUIO "bundle" of
            data arrives. A minimal bundle when no fingers are detected
            will just contain an "alive" message and an "fseq" message, 
            and the callback should be triggered once for each, in that
            order.

            When fingers are detected, the callback will be triggered 
            extra times between the "alive" and "fseq" calls, once per
            finger, eg:
                alive
                finger 1
                finger 2
                ...
                finger n
                fseq

            The "alive" message contains a list of the currently active
            finger object session IDs. 

            The "fseq" message contains a sequence number.

            The "set" message contains a session ID for the finger/object,
            the x and y positions (normalized to 0-1.0), the X and Y
            velocity vectors for the finger, and the motion acceleration
            of the object. 
        """
        msg = args[0]
        if msg == 'alive':
            self.newfingers = []
        elif msg == 'fseq':
            self.fingers = deepcopy(self.newfingers[:MAX_FINGERS])
        elif msg == 'set':
            (unused, session_id, x, y, xv, yv, m) = args
            self.newfingers.append((session_id, x, y, xv, yv, m))
        else:
            print('???', addr, msg, args)

if __name__ == "__main__":
    TactionDemo().run()
