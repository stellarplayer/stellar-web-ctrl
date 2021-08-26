import traceback
import StellarPlayer
import requests
import threading
import json
import time
import os
import io
import sys
import socket

plugin_dir = os.path.dirname(__file__)
sys.path.append(plugin_dir)

import qrcode
from qrcode.image.pure import PymagingImage
try:
    from bottle import route, run, template, request, response, get, post, TEMPLATE_PATH
except:
    sys.exit(0)


_local_ip = None
_plugin_dir = os.path.dirname(__file__)
_template_dir = os.path.join(_plugin_dir, 'templates')


def get_host_ip():
    global _local_ip
    s = None
    try:
        if not _local_ip:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            _local_ip = s.getsockname()[0]
        return _local_ip
    finally:
        if s:
            s.close()


class MyPlugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self,player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        self.stoped = False
        self.status = 'stop'
        

    def handleRequest(self, method, args):
        if method == 'onPlay':
            print('---------------onPlay')  
            self.status = 'play'
        elif method == 'onStop':
            print('---------------onStop')
            self.status = 'stop'
        elif method == 'onPause':
            play, = args      
            self.status = 'play' if play else 'pause'
        else:
            print(f'handleRequest {method=} {args=}')

    def show(self):
        controls = [
            {
                'type': 'image',
                'value': f'http://{get_host_ip()}:1234/qr'
            }
        ]        
        self.doModal('main', 400, 400, '', controls)

    def start(self):
        self.stoped = False
        super().start()
        t = threading.Thread(target=self.webserver_thread, daemon=True)
        t.start()
        

    def stop(self):
        self.stoped = True
        super().stop()

    def webserver_thread(self):
        url = f'http://{get_host_ip()}:1234'
        print(url)
        img = qrcode.make(url, image_factory=PymagingImage)
        f = open("qr.png", "wb")
        img.save(f)
        f.close()

        @get('/')
        def index():
            return template('index.html')

        @get('/qr')
        def qr():
            f = open("qr.png", "rb")
            bytes = f.read()
            response.set_header('Content-type', 'image/png')
            return bytes

        @get('/info')
        def progress():  
            return json.dumps({
                'status': self.status,
                'pos': self.player.getProgress()
            })

        @post('/progress')
        def progress():  
            pos = request.forms.get('pos')
            self.player.setProgress(pos)
            return f'{pos}'

        @post('/pause')
        def pause():  
            play = request.forms.get('play')
            self.player.pause(play)
            return f'{play}'

        @post('/stop')
        def stop():  
            self.player.stop()
            return f''

        @post('/prev')
        def prev():  
            self.player.prev()
            return f''

        @post('/next')
        def next():  
            self.player.next()
            return f''
        
        if not _template_dir in TEMPLATE_PATH:
            TEMPLATE_PATH.append(_template_dir)

        run(host='0.0.0.0', port=1234)

   
           
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = MyPlugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()
