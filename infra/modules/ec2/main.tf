resource "aws_instance" "api" {
  ami = var.ami

  instance_type = var.instance_type

  subnet_id = var.subnet_id

  vpc_security_group_ids = [
    var.security_group
  ]

  iam_instance_profile = var.instance_profile

  user_data = file(var.user_data)

  tags = {
    Name = "${var.project_name}-api"
  }
}