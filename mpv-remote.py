from http.server import HTTPServer, BaseHTTPRequestHandler
import os
import json
import socket
import threading


SOCKET_PATH = "/tmp/mpvsocket"
SERVER_ADRESS = ('0.0.0.0', 8000)

static_files = {}
for static_file in os.listdir('static'):
    with open(f'static/{static_file}', 'rb') as f:
        static_files[static_file] = f.read()


class HttpRequestHandler(BaseHTTPRequestHandler):
    def response(self, code, content_type, data):
        self.send_response(code)
        self.send_header('content-type',content_type)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/':
            self.response(200, 'text/html', static_files['index.html'])
        elif self.path == '/styles.css':
            self.response(200, 'text/css', static_files['styles.css'])
        elif self.path == '/subs':
            self.response(200, 'text/html', static_files['subs.html'])
        elif self.path == '/media':
            self.response(200, 'text/html', static_files['media.html'])
        elif self.path == "/getdirs/":
            res = {'dirs':[],'files':[]}
            for x in os.listdir():
                if os.path.isdir(x):
                    res['dirs'].append(x)
                else:
                    res['files'].append(x)
            res['dirs'].sort()
            res['files'].sort()
            self.response(200, 'application/json', json.dumps(res, ensure_ascii=False).encode("utf-8"))
        else:
            self.response(404, 'text/html', b'404')

    def do_POST(self):
        if self.path == "/changedir/":
            self.send_response(200)
            self.send_header('content-type','application/json')
            self.end_headers()
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            d = json.loads(data_string)['dir']
            if os.path.isdir(os.path.join(os.getcwd(),d)):
                os.chdir(d)
                self.wfile.write(json.dumps({'type':'dir'}, ensure_ascii=False).encode("utf-8"))
            else:
                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect(SOCKET_PATH)
                    s.send(bytes('{ "command": ["sub-add", "'+os.path.join(os.getcwd(),d)+'"]}', 'utf-8') + b'\n')
                    s.close()
                except (FileNotFoundError, ConnectionRefusedError):
                    print("Socket file not found!","1) Ensure mpv is running.","2) Check input-ipc-server option in your mpv config.","3) Check SOCKET_PATH in mpv-remote.py",sep='\n')
                self.wfile.write(json.dumps({'type':'file'}, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/playnow/":
            self.response(200, 'application/json', b'')
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            filenames = json.loads(data_string)['files']
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(SOCKET_PATH)
                s.send(bytes('{ "command": ["loadfile", "'+os.path.join(os.getcwd(),filenames[0])+'","replace"]}', 'utf-8') + b'\n')
                s.close()
                for filename in filenames[1:]:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect(SOCKET_PATH)
                    s.send(bytes('{ "command": ["loadfile", "'+os.path.join(os.getcwd(),filename)+'","append"]}', 'utf-8') + b'\n')
                    s.close()
            except (FileNotFoundError, ConnectionRefusedError):
                def open_mpv():
                    s = os.popen('mpv --input-ipc-server='+SOCKET_PATH+' '+' '.join(['"'+os.path.join(os.getcwd(),filename)+'"' for filename in filenames]))
                    s.read()
                mpv_thread = threading.Thread(target=open_mpv, args=(), daemon=True)
                mpv_thread.start()
        elif self.path == "/appendtoplaylist/":
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            filenames = json.loads(data_string)['files']
            try:
                for filename in filenames:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.connect(SOCKET_PATH)
                    s.send(bytes('{ "command": ["loadfile", "'+os.path.join(os.getcwd(),filename)+'","append"]}', 'utf-8') + b'\n')
                    s.close()
            except (FileNotFoundError, ConnectionRefusedError):
                print("Socket file not found!","1) Ensure mpv is running.","2) Check input-ipc-server option in your mpv config.","3) Check SOCKET_PATH in mpv-remote.py",sep='\n')
            self.response(200, 'application/json', b'')
        elif self.path == "/command/":
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            command = json.loads(data_string)['command']
            command_mapper = {
                'sub': '["osd-auto","cycle", "sub"]',
                'audio': '["osd-auto","cycle", "audio"]',
                'speed+': '["osd-auto","add", "speed","0.1"]',
                'speed-': '["osd-auto","add", "speed","-0.1"]',
                '-10s': '["osd-auto","seek", "-10"]',
                '+10s': '["osd-auto","seek", "10"]',
                'volumeup': '["osd-auto","add", "volume","5"]',
                'volumedown': '["osd-auto","add", "volume","-5"]',
                '-min': '["osd-auto","seek", "-60"]',
                '+min': '["osd-auto","seek", "60"]',
                'space': '["cycle", "pause"]',
                'forward': '["osd-auto","playlist-next"]',
                'back': '["osd-auto","playlist-prev"]',
                'f': '["cycle", "fullscreen"]',
            }
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(SOCKET_PATH)
                s.send(bytes(f'{{ "command": {command_mapper[command]} }}', 'utf-8') + b'\n')
                s.close()
            except (FileNotFoundError, ConnectionRefusedError):
                print("Socket file not found!","1) Ensure mpv is running.","2) Check input-ipc-server option in your mpv config.","3) Check SOCKET_PATH in mpv-remote.py",sep='\n')
            self.response(200, 'application/json', b'')
        else:
            self.response(404, 'text/html', b'404')

http_server = HTTPServer(SERVER_ADRESS, HttpRequestHandler)

try:
    print(f"Starting mpv control server at http://{SERVER_ADRESS[0]}:{SERVER_ADRESS[1]}/")
    if SERVER_ADRESS[0] == '0.0.0.0':
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            print("IP in local network:", s.getsockname()[0])
            s.close()
        except:
            pass
    print("Quit the mpv server with CONTROL-C.")
    http_server.serve_forever()
except KeyboardInterrupt:
    http_server.server_close()
    print("\nMPV remote controller server stopped.")