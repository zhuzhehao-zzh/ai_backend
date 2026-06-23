"""Upload deploy script to cloud server."""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('101.43.30.20', username='ubuntu')

script = """#!/bin/bash
cd /root/Desktop/career/ai_backend
sudo git pull origin main
sudo fuser -k 8000/tcp 2>/dev/null
sleep 2
sudo nohup ./venv/bin/python -u main.py > /tmp/server11.log 2>&1 &
sleep 6
curl -s http://localhost:8000/health && echo ' -- OK' || echo ' -- FAIL'
"""

stdin, stdout, stderr = ssh.exec_command("cat > /root/Desktop/career/deploy.sh && chmod +x /root/Desktop/career/deploy.sh", timeout=10)
stdin.write(script)
stdin.flush()
stdin.channel.shutdown_write()
stdout.channel.recv_exit_status()
print('deploy.sh uploaded')

ssh.close()
