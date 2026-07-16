variable "aws_region" {
  type = string
}

variable "project_name" {
  type = string
}

variable "key_name" {
  type = string
}

variable "ssh_allowed_cidrs" {
  description = "IPs allowed to SSH"
  type        = list(string)
}

variable "ec2_ami" {
  type = string
}

variable "ollama_instance_type" {
  #  description = "EC2 GPU instance type used by Ollama."
  type = string
  #  default     = "g5.xlarge"
}

variable "ollama_associate_public_ip_address" {
  description = "Assign a public IP to the Ollama instance for bootstrap internet access. Keep false when using a private subnet with NAT."
  type        = bool
  default     = true
}

variable "ollama_root_volume_size" {
  description = "Root EBS volume size in GiB for the Ollama instance."
  type        = number
  default     = 80
}

variable "ollama_data_volume_size" {
  description = "Persistent Ollama model/data EBS volume size in GiB."
  type        = number
  default     = 250
}

variable "ollama_models" {
  description = "Ollama models to pre-pull during instance bootstrap."
  type        = list(string)
  default     = ["llama3.1:8b", "nomic-embed-text"]
}

variable "ollama_enable_private_dns" {
  description = "Create ollama.internal as a private Route 53 record in the existing VPC."
  type        = bool
  default     = true
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
