#!/usr/bin/env bash
python3 /app/cumucore-api-engine.py &
python3 /app/web-app.py &
python3 /app/plugin-api-engine.py &
python3 /app/decision-engine-1.py &

while true; do
	sleep 100
done
