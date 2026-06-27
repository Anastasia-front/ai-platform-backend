variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "ssh_allowed_cidr" {
  type = string
}

variable "ec2_ami" {
  type = string
}

variable "db_username" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "env_values" {
  type = map(string)

  sensitive = true
}