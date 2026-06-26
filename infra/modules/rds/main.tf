resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-db"

  engine = "postgres"

  engine_version = "15"

  instance_class = "db.t3.micro"

  allocated_storage = 20

  db_name = "app"

  username = var.username

  password = var.password

  skip_final_snapshot = true

  publicly_accessible = false

  vpc_security_group_ids = [
    var.security_group
  ]
}