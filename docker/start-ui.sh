#!/bin/sh
set -eu

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
if [ ! -f /usr/share/novnc/vnc-original.html ]; then
    cp /usr/share/novnc/vnc.html /usr/share/novnc/vnc-original.html
fi
cp /usr/share/novnc/vnc-original.html /usr/share/novnc/vnc-core.html
cp /workspace/docker/novnc-audio.html /usr/share/novnc/vnc.html
cp /workspace/assets/cycling_music.mp3 /usr/share/novnc/music.mp3
printf '{"enabled":false}\n' > /usr/share/novnc/music_state.json

Xvnc :99 -geometry 1600x1000 -depth 24 -dpi 96 \
    -AlwaysShared -SecurityTypes None -localhost=0 -rfbport 5900 >/tmp/xvnc.log 2>&1 &
sleep 1
openbox >/tmp/openbox.log 2>&1 &
websockify --web=/usr/share/novnc/ 6080 localhost:5900 >/tmp/novnc.log 2>&1 &

exec python3 -m app.main --auto-start
