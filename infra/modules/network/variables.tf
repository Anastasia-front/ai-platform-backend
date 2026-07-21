variable "project_name" {
  type = string
}

variable "ssh_allowed_cidrs" {
  type = list(string)
}

variable "frontend_security_group_id" {
  description = "Frontend EC2 Security Group ID allowed to reach the backend over private VPC networking."
  type        = string
}

variable "public_http_allowed_cidrs" {
  description = "CIDR ranges allowed to reach the backend public HTTP endpoint."
  type        = list(string)
  default     = []
}
