variable "project_name" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "instance_type" {
  #  description = "EC2 GPU instance type used by Ollama."
  type = string
  #  default     = "g5.xlarge"
}

variable "key_name" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "backend_security_group_id" {
  type = string
}

variable "instance_profile" {
  type = string
}

variable "associate_public_ip_address" {
  description = "Assign a public IP for bootstrap internet access. Keep false when deploying in a private subnet with NAT."
  type        = bool
  default     = true
}

variable "root_volume_size" {
  description = "Root EBS volume size in GiB."
  type        = number
  #  default     = 80
}

variable "data_volume_size" {
  description = "Persistent Ollama model/data EBS volume size in GiB."
  type        = number
  default     = 250
}

variable "models" {
  description = "Ollama models to pre-pull during bootstrap."
  type        = list(string)
  #  default     = ["llama3.1:8b", "nomic-embed-text"]
}

variable "enable_private_dns" {
  description = "Create a private Route 53 record for Ollama inside the VPC."
  type        = bool
  default     = true
}

variable "ssh_allowed_cidrs" {
  type = list(string)
}