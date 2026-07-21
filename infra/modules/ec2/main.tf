resource "aws_instance" "api" {
  ami = var.ami

  instance_type = var.instance_type

  key_name = var.key_name

  subnet_id = var.subnet_id

  vpc_security_group_ids = [
    var.security_group
  ]

  iam_instance_profile = var.instance_profile

  user_data = file(var.user_data)

  tags = {
    Name = "${var.project_name}-backend"
  }
}

resource "aws_eip" "api" {
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-backend-eip"
  }
}

resource "aws_eip_association" "api" {
  instance_id   = aws_instance.api.id
  allocation_id = aws_eip.api.id
}
