#!/bin/sh
set -eu

rm -f /tmp/.X99-lock
Xvfb :99 -screen 0 1280x850x24 -ac +extension GLX +render -noreset &
sleep 1
openbox >/tmp/openbox.log 2>&1 &
x11vnc -display :99 -forever -shared -nopw -listen 0.0.0.0 -rfbport 5900 >/tmp/x11vnc.log 2>&1 &
websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 &

exec python3 -m app.main --auto-start
