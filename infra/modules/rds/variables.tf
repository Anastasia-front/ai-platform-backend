variable "project_name" {}

variable "username" {}

variable "password" {
  sensitive = true
}

variable "security_group" {}