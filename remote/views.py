from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json, socket, os
from django.conf import settings

def index(request):
    return render(request, 'remote/index.html')

def subs(request):
    return render(request, 'remote/subs.html')

def media(request):
    return render(request, 'remote/media.html')

@csrf_exempt
def command(request):
    command = json.loads(request.body)['command']
    if command=='sub':
        command = '{ "command": ["osd-auto","cycle", "sub"] }'
    elif command=='audio':
        command = '{ "command": ["osd-auto","cycle", "audio"] }'
    elif command=='speed+':
        command = '{ "command": ["osd-auto","add", "speed","0.1"] }'
    elif command=='speed-':
        command = '{ "command": ["osd-auto","add", "speed","-0.1"] }'
    elif command=='-10s':
        command = '{ "command": ["osd-auto","seek", "-10"] }'
    elif command=='+10s':
        command = '{ "command": ["osd-auto","seek", "10"] }'
    elif command=='volumeup':
        command = '{ "command": ["osd-auto","add", "volume","5"] }'
    elif command=='volumedown':
        command = '{ "command": ["osd-auto","add", "volume","-5"] }'
    elif command=='-min':
        command = '{ "command": ["osd-auto","seek", "-60"] }'
    elif command=='+min':
        command = '{ "command": ["osd-auto","seek", "60"] }'
    elif command=='space':
        command = '{ "command": ["cycle", "pause"] }'
    elif command=='forward':
        command = '{ "command": ["osd-auto","playlist-next"] }'
    elif command=='back':
        command = '{ "command": ["osd-auto","playlist-prev"] }'
    elif command=='f':
        command = '{ "command": ["cycle", "fullscreen"] }'
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(settings.SOCKET_PATH)
        s.send(bytes(command, 'utf-8') + b'\n')
        s.close()
    except:
        print("File socket no found!","1) Ensure mpv is running.","2) Check input-ipc-server option in your mpv config.","3) Check socket_path in mpvremote/settings.py",sep='\n')
    return HttpResponse("OK", status = 200)

@csrf_exempt
def getDirs(request):
    res = {'dirs':[],'files':[]}
    for x in os.listdir():
        if os.path.isdir(x):
            res['dirs'].append(x)
        else:
            res['files'].append(x)
    res['dirs'].sort()
    res['files'].sort()
    return HttpResponse(json.dumps(res) ,status=200)

@csrf_exempt
def changeDir(request):
    d = json.loads(request.body)['dir']
    if os.path.isdir(os.path.join(os.getcwd(),d)):
        os.chdir(d)
        return HttpResponse(json.dumps({'type':'dir'}), status = 200)
    else:
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(settings.SOCKET_PATH)
            s.send(bytes('{ "command": ["sub-add", "'+os.path.join(os.getcwd(),d)+'"]}', 'utf-8') + b'\n')
            s.close()
        except (FileNotFoundError, ConnectionRefusedError):
            print("File socket no found!","1) Ensure mpv is running.","2) Check input-ipc-server option in your mpv config.","3) Check socket_path in mpvremote/settings.py",sep='\n')
        return HttpResponse(json.dumps({'type':'file'}), status = 200)

@csrf_exempt
def appendToPlaylist(request):
    filenames = json.loads(request.body)['files']
    try:
        for filename in filenames:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(settings.SOCKET_PATH)
            s.send(bytes('{ "command": ["loadfile", "'+os.path.join(os.getcwd(),filename)+'","append"]}', 'utf-8') + b'\n')
            s.close()
    except (FileNotFoundError, ConnectionRefusedError):
        print("File socket no found!","1) Ensure mpv is running.","2) Check input-ipc-server option in your mpv config.","3) Check socket_path in mpvremote/settings.py",sep='\n')
    return HttpResponse("OK", status = 200)

@csrf_exempt
def playNow(request):
    filenames = json.loads(request.body)['files']
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(settings.SOCKET_PATH)
        s.send(bytes('{ "command": ["loadfile", "'+os.path.join(os.getcwd(),filenames[0])+'","replace"]}', 'utf-8') + b'\n')
        s.close()
        for filename in filenames[1:]:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(settings.SOCKET_PATH)
            s.send(bytes('{ "command": ["loadfile", "'+os.path.join(os.getcwd(),filename)+'","append"]}', 'utf-8') + b'\n')
            s.close()
    except (FileNotFoundError, ConnectionRefusedError):
        s = os.popen('mpv --input-ipc-server='+settings.SOCKET_PATH+' '+' '.join(['"'+os.path.join(os.getcwd(),filename)+'"' for filename in filenames]))
        s.read()
    return HttpResponse("OK", status = 200)
