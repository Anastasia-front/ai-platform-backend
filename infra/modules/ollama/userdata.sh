#!/bin/bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list

#  or NVIDIA Container Toolkit, see https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker
# curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
# curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
#   | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
#   > /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 
# nvidia-container-toolkit

systemctl enable --now docker
# nvidia-ctk runtime configure --runtime=docker
# systemctl restart docker

curl -fsSL "https://amazoncloudwatch-agent-${aws_region}.s3.${aws_region}.amazonaws.com/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb" -o /tmp/amazon-cloudwatch-agent.deb
dpkg -i /tmp/amazon-cloudwatch-agent.deb

ROOT_SOURCE="$(findmnt -n -o SOURCE /)"
ROOT_PARENT="$(lsblk -no PKNAME "$ROOT_SOURCE" | head -n 1)"
if [ -n "$ROOT_PARENT" ]; then
  ROOT_DEVICE="/dev/$ROOT_PARENT"
else
  ROOT_DEVICE="$ROOT_SOURCE"
fi
DATA_DEVICE="$(lsblk -ndo NAME,TYPE | awk '$2 == "disk" { print "/dev/" $1 }' | while read -r device; do
  if [ "$device" != "$ROOT_DEVICE" ] && ! findmnt -rn "$device" >/dev/null; then
    echo "$device"
    break
  fi
done)"
if [ -z "$DATA_DEVICE" ]; then
  echo "No unmounted EBS data device found for Ollama storage" >&2
  exit 1
fi

if ! blkid "$DATA_DEVICE"; then
  mkfs -t xfs "$DATA_DEVICE"
fi

mkdir -p /var/lib/ollama
if ! grep -q " /var/lib/ollama " /etc/fstab; then
  DATA_UUID="$(blkid -s UUID -o value "$DATA_DEVICE")"
  echo "UUID=$DATA_UUID /var/lib/ollama xfs defaults,nofail 0 2" >> /etc/fstab
fi
mount -a

cat >/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<EOF
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/cloud-init-output.log",
            "log_group_name": "${cloudwatch_log_group}",
            "log_stream_name": "{instance_id}/cloud-init"
          }
        ]
      }
    }
  }
}
EOF
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

docker pull ollama/ollama:latest
docker run -d \
  --name ollama \
  --restart unless-stopped \
  # --gpus all \
  -p 11434:11434 \
  -v /var/lib/ollama:/root/.ollama \
  -e OLLAMA_HOST=0.0.0.0:11434 \
  -e OLLAMA_NUM_PARALLEL=1 \
  -e OLLAMA_MAX_LOADED_MODELS=1 \
  -e OLLAMA_KEEP_ALIVE=2m \
  ollama/ollama:latest

%{ for model in models ~}
docker exec ollama ollama pull ${model}
%{ endfor ~}
