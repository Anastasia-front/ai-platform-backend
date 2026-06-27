variable "project_name" {}

variable "ami" {}

variable "instance_type" {
  default = "t3.micro"
}

variable "subnet_id" {}

variable "security_group" {}

variable "instance_profile" {}

variable "user_data" {}