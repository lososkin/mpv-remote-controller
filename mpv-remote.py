import sys,os
import datetime

def kill_processes(proc):
    stream = os.popen('pgrep '+proc)
    ids = stream.read().split()
    for id in ids:
        os.popen('kill -9 '+id)

kill_processes('-f "manage.py runserver"')
kill_processes('mpv')

st = os.popen('python3 '+os.path.dirname(os.path.realpath(__file__))+'/manage.py runserver 0.0.0.0:8000')

if len(sys.argv)>1:
    stream = os.popen('mpv '+'--input-ipc-server=/tmp/mpvsocket '+' '.join(['"'+x+'"' for x in sys.argv[1:]]))
    stream.read()
