import socket
import qrcode
import os

from bottle import ServerAdapter
from qrcode.image.pure import PymagingImage

_local_ip = None

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


class WSGIRefServer(ServerAdapter):
    def run(self, app):  # pragma: no cover
        from wsgiref.simple_server import make_server
        from wsgiref.simple_server import WSGIRequestHandler, WSGIServer
        import socket

        class FixedHandler(WSGIRequestHandler):
            def address_string(self):  # Prevent reverse DNS lookups please.
                return self.client_address[0]

            def log_request(*args, **kw):
                if not self.quiet:
                    return WSGIRequestHandler.log_request(*args, **kw)

        handler_cls = self.options.get('handler_class', FixedHandler)
        server_cls = self.options.get('server_class', WSGIServer)

        if ':' in self.host:  # Fix wsgiref for IPv6 addresses.
            if getattr(server_cls, 'address_family') == socket.AF_INET:

                class server_cls(server_cls):
                    address_family = socket.AF_INET6

        self.srv = make_server(self.host, self.port, app, server_cls,
                               handler_cls)
        self.port = self.srv.server_port  # update port actual port (0 means random)

        # 此处获取到随机端口
        url = f'http://{get_host_ip()}:{self.port}'
        print(url)
        img = qrcode.make(url, image_factory=PymagingImage)
        f = open(f'qr_{os.getpid()}.png', 'wb')
        img.save(f)
        f.close()
        f = open(f'qr_{os.getpid()}.txt', 'w')
        f.write(url)
        f.close()

        try:
            self.srv.serve_forever()
        except KeyboardInterrupt:
            self.srv.server_close()  # Prevent ResourceWarning: unclosed socket
            raise
