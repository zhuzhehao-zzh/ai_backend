#!/bin/bash
# Deploy latest code to cloud server and restart
cd /root/Desktop/career/ai_backend
sudo git pull origin main
sudo fuser -k 8000/tcp 2>/dev/null
sleep 2
sudo nohup ./venv/bin/python -u main.py > /tmp/server11.log 2>&1 &
sleep 6
curl -s http://localhost:8000/health && echo ' -- OK' || echo ' -- FAIL'
