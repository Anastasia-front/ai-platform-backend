data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_security_group" "ec2" {
  name   = "${var.project_name}-ec2-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    description = "Allow restricted SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"

    cidr_blocks = var.ssh_allowed_cidrs
  }

  ingress {
    description = "Allow frontend EC2 to reach backend over private VPC"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"

    security_groups = [
      var.frontend_security_group_id
    ]
  }

  ingress {
    description = "Allow public HTTP traffic to host Nginx"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"

    cidr_blocks = var.public_http_allowed_cidrs
  }

  ingress {
    description = "Allow public HTTPS traffic for API documentation"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"

    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound IPv4 traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"

    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name   = "${var.project_name}-rds-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    description = "Allow PostgreSQL access from backend EC2"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"

    security_groups = [
      aws_security_group.ec2.id
    ]
  }

  egress {
    description = "Allow all outbound IPv4 traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"

    cidr_blocks = ["0.0.0.0/0"]
  }
}