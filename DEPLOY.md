# Deployment Guide

Deploy the AI Backend to a cloud server (VPS) with Nginx reverse proxy and
systemd auto-start.

---

## 1. Connect to your server

```bash
ssh user@your-server-ip
```

## 2. Install system dependencies

```bash
# For Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx
```

## 3. Clone the repository

```bash
git clone https://github.com/zhuzhehao-zzh/ai_backend.git
cd ai_backend
```

## 4. Set up Python environment

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 5. Configure API key

```bash
echo "MOONSHOT_API_KEY=sk-your-kimi-key-here" > .env
echo "MOONSHOT_BASE_URL=https://api.moonshot.cn/v1" >> .env
```

## 6. Test the server

```bash
./venv/bin/python main.py
```

Visit `http://your-server-ip:8000/health` — you should see `{"status":"ok"}`.
Press **Ctrl+C** to stop after confirming it works.

---

## 7. Set up systemd service (auto-start on boot)

Create a service file:

```bash
sudo tee /etc/systemd/system/ai-backend.service > /dev/null <<'EOF'
[Unit]
Description=AI Backend - College Application Guidance API
After=network.target

[Service]
Type=simple
User=zzh
WorkingDirectory=/home/zzh/ai_backend
ExecStart=/home/zzh/ai_backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=on-failure
RestartSec=5
EnvironmentFile=/home/zzh/ai_backend/.env

[Install]
WantedBy=multi-user.target
EOF
```

Start and enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl start ai-backend
sudo systemctl enable ai-backend

# Check status
sudo systemctl status ai-backend
```

---

## 8. Set up Nginx reverse proxy (with optional domain)

```bash
# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Create site config
sudo tee /etc/nginx/sites-available/ai-backend > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;  # Replace with your domain if you have one

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable and test
sudo ln -sf /etc/nginx/sites-available/ai-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Your API is now accessible at:

```
http://your-server-ip/
http://your-server-ip/health
http://your-server-ip/docs          # Swagger UI
```

---

## 9. (Optional) Set up firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

---

## 10. (Optional) Add a domain with HTTPS

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com
```

---

## Quick start (if already set up)

```bash
ssh user@your-server
sudo systemctl start ai-backend
sudo systemctl status ai-backend
```

## Update to latest code

```bash
ssh user@your-server
cd ai_backend
git pull
sudo systemctl restart ai-backend
```
