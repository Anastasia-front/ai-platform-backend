#!/bin/bash
yum update -y

yum install -y docker
service docker start
usermod -a -G docker ec2-user

# login to ECR (region auto)
aws ecr get-login-password --region eu-central-1 \
| docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com

# pull & run backend
docker pull <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/ai-platform-backend:latest

docker run -d \
  -p 8000:8000 \
  --name backend \
  <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/ai-platform-backend:latest