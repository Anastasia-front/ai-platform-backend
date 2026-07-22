#!/bin/bash
yum update -y

yum install -y docker
service docker start
usermod -a -G docker ec2-user

yum install -y nginx
systemctl enable nginx
systemctl start nginx

# login to ECR (region auto)
aws ecr get-login-password --region eu-central-1 \
| docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com

# shared network so the api/worker containers can reach redis by name,
# without redis ever binding a host port (not publicly reachable)
docker network create ai-platform 2>/dev/null || true

# redis: Celery broker only, internal network, no -p / host port published
docker run -d \
  --name redis \
  --network ai-platform \
  --restart unless-stopped \
  redis:7-alpine

# pull & run backend (FastAPI web process)
docker pull <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/ai-platform-backend:latest

docker run -d \
  -p 127.0.0.1:8000:8000 \
  --name backend \
  --network ai-platform \
  --restart unless-stopped \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  --env-file /etc/ai-platform/backend.env \
  <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/ai-platform-backend:latest

# celery worker: separate process from the FastAPI web container, same
# image, so long-running jobs survive web-process restarts/deploys
docker run -d \
  --name worker \
  --network ai-platform \
  --restart unless-stopped \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  --env-file /etc/ai-platform/backend.env \
  <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/ai-platform-backend:latest \
  celery -A app.core.celery_app worker --loglevel=info
