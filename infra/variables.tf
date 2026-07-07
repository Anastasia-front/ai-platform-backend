variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "key_name" {
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

variable "google_client_id" {
  type        = string
  description = "OAuth client ID used by the backend to verify Google ID tokens."
}

variable "env_values" {
  type = map(string)

  sensitive = true
}
