# GPU AMI — keep commented for future GPU instance usage.
#
# data "aws_ssm_parameter" "deep_learning_gpu_ami" {
#   # AWS publishes regional Deep Learning GPU AMIs in SSM. Using the public
#   # parameter avoids pinning a temporary AMI ID and keeps GPU driver support
#   # current for the selected region.
#   name = "/aws/service/deeplearning/ami/x86_64/base-oss-nvidia-driver-gpu-ubuntu-22.04/latest/ami-id"
# }

# CPU-only Ubuntu AMI for t3.small.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name = "name"
    values = [
      "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
    ]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

resource "aws_security_group" "ollama" {
  name        = "${var.project_name}-ollama-sg"
  description = "Private Ollama inference access from backend only"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Ollama API from backend"
    from_port       = 11434
    to_port         = 11434
    protocol        = "tcp"
    security_groups = [var.backend_security_group_id]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"

    cidr_blocks = var.ssh_allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_cloudwatch_log_group" "ollama" {
  name              = "/${var.project_name}/ollama"
  retention_in_days = 30
}

resource "aws_instance" "ollama" {
  # GPU version for future use:
  # ami = data.aws_ssm_parameter.deep_learning_gpu_ami.value

  # CPU-only Ubuntu AMI for t3.small:
  ami = data.aws_ami.ubuntu.id

  instance_type               = var.instance_type
  key_name                    = var.key_name
  subnet_id                   = var.subnet_id
  associate_public_ip_address = var.associate_public_ip_address
  iam_instance_profile        = var.instance_profile

  # Basic EC2 monitoring remains enabled automatically.
  # Set to true only if you need paid 1-minute detailed monitoring.
  monitoring = false

  user_data_replace_on_change = true

  vpc_security_group_ids = [
    aws_security_group.ollama.id
  ]

  user_data = templatefile("${path.module}/userdata.sh", {
    aws_region           = var.aws_region
    cloudwatch_log_group = aws_cloudwatch_log_group.ollama.name
    models               = var.models
  })

  root_block_device {
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  ebs_block_device {
    device_name           = "/dev/sdf"
    volume_size           = var.data_volume_size
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = false
  }

  tags = {
    Name = "${var.project_name}-ollama"
  }
}

resource "aws_eip" "ollama" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-ollama-eip"
  }
}

resource "aws_eip_association" "ollama" {
  instance_id   = aws_instance.ollama.id
  allocation_id = aws_eip.ollama.id
}

resource "aws_route53_zone" "internal" {
  count = var.enable_private_dns ? 1 : 0

  name = "internal"

  vpc {
    vpc_id = var.vpc_id
  }
}

resource "aws_route53_record" "ollama" {
  count = var.enable_private_dns ? 1 : 0

  zone_id = aws_route53_zone.internal[0].zone_id
  name    = "ollama.ai-platform.internal"
  type    = "A"
  ttl     = 60
  records = [aws_instance.ollama.private_ip]
}
