#!/bin/bash
APP_DIR="/home/cyopn/server/monitor/"

cd "$APP_DIR"
flask run --host=0.0.0.0 --port=5000 > "$APP_DIR/flask.log" 2>&1 &

sleep 2

ngrok start --all > "$APP_DIR/ngrok.log" 2>&1 &

echo "Flask iniciado en puerto 5000"
echo "Ngrok iniciado"