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

try:
    from bottle import route, run, template, request, response, get, post, TEMPLATE_PATH
except:
    sys.exit(0)

from . import ss


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
        self.url = ''
        

    def handleRequest(self, method, args):
        if method == 'onPlay':
            print('---------------onPlay')  
            self.status = 'play'
        elif method == 'onStopPlay':
            print('---------------onStopPlay')
            self.status = 'stop'
        elif method == 'onPause':
            play, = args      
            self.status = 'play' if play else 'pause'
        else:
            print(f'handleRequest {method=} {args=}')

    def show(self):
        qrPath = os.path.join(self.player.dataDirectory, f'qr_{os.getpid()}.png')
        urlPath = os.path.join(self.player.dataDirectory, f'qr_{os.getpid()}.txt')
        self.url = open(urlPath).read()
        controls = [
            {'type':'label','name':'手机与电脑接入同一网络内，用手机扫描二维码', 'height': 20, 'hAlign': 'center'},
            {'type':'link','name': self.url, 'height': 20, 'hAlign': 'center', '@click': 'onUrlClick'},
            {
                'type': 'image',
                'value': f'{qrPath}'
            }
        ]        
        self.doModal('main', 400, 440, '', controls)

    def start(self):
        self.stoped = False
        super().start()
        t = threading.Thread(target=self.webserverThread, daemon=True)
        t.start()
        

    def stop(self):
        self.stoped = True
        super().stop()

    def webserverThread(self):
        @get('/')
        def index():
            return template('index.html')

        @get('/info')
        def progress():  
            pos, total = self.player.getProgress()
            return json.dumps({
                'status': self.status,
                'pos': pos,
                'total': total 
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

        run(host='0.0.0.0', port=0, server=ss.WSGIRefServer)

   
           
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = MyPlugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()
