from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json, socket

def index(request):
    return render(request, 'remote/index.html')

@csrf_exempt
def command(request):
    command = json.loads(request.body)['command']
    if command=='sub':
        command = '{ "command": ["keypress", "J"] }'
    elif command=='audio':
        command = '{ "command": ["keypress", "#"] }'
    elif command=='speed+':
        command = '{ "command": ["keypress", "]"] }'
    elif command=='speed-':
        command = '{ "command": ["keypress", "["] }'
    elif command=='-10s':
        command = '{ "command": ["keypress", "left"] }'
    elif command=='+10s':
        command = '{ "command": ["keypress", "right"] }'
    elif command=='volumeup':
        command = '{ "command": ["keypress", "0"] }'
    elif command=='volumedown':
        command = '{ "command": ["keypress", "9"] }'
    elif command=='-min':
        command = '{ "command": ["keypress", "down"] }'
    elif command=='+min':
        command = '{ "command": ["keypress", "up"] }'
    elif command=='space':
        command = '{ "command": ["keypress", "space"] }'
    elif command=='forward':
        command = '{ "command": ["keypress", ">"] }'
    elif command=='back':
        command = '{ "command": ["keypress", "<"] }'
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect("/tmp/mpvsocket")
    if command=='+10s' or command=='-10s':
        s.send(bytes(command, 'utf-8') + b'\n')
    s.send(bytes(command, 'utf-8') + b'\n')
    s.close()
    return HttpResponse("OK", status = 200)
