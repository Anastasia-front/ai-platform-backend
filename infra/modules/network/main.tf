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
    from_port = 22
    to_port   = 22
    protocol  = "tcp"

    cidr_blocks = var.ssh_allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc_security_group_ingress_rule" "backend_http_from_frontend" {
  security_group_id            = aws_security_group.ec2.id
  referenced_security_group_id = var.frontend_security_group_id

  ip_protocol = "tcp"
  from_port   = 80
  to_port     = 80

  description = "Allow frontend EC2 to reach backend over private VPC"
}

resource "aws_vpc_security_group_ingress_rule" "backend_http_public" {
  for_each = toset(var.public_http_allowed_cidrs)

  security_group_id = aws_security_group.ec2.id
  cidr_ipv4         = each.value

  ip_protocol = "tcp"
  from_port   = 80
  to_port     = 80

  description = "Allow public HTTP access to backend docs endpoint"
}

resource "aws_vpc_security_group_ingress_rule" "backend_https_public" {
  security_group_id = aws_security_group.ec2.id
  cidr_ipv4         = "0.0.0.0/0"

  ip_protocol = "tcp"
  from_port   = 443
  to_port     = 443

  description = "Allow public HTTPS traffic for API documentation"
}

resource "aws_security_group" "rds" {
  name   = "${var.project_name}-rds-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"

    security_groups = [
      aws_security_group.ec2.id
    ]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"

    cidr_blocks = ["0.0.0.0/0"]
  }
}
