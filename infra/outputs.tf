output "ec2_ip" {
  value = module.ec2.public_ip
}

output "rds_endpoint" {
  value = module.rds.endpoint
}

output "s3_bucket" {
  value = module.s3.bucket_name
}

output "ecr_repository" {
  value = module.ecr.repository_url
}

output "ssm_prefix" {
  value = module.ssm.parameter_prefix
}

output "ollama_private_ip" {
  value = module.ollama.private_ip
}

output "ollama_private_dns_name" {
  value = module.ollama.private_dns_name
}

output "ollama_base_url" {
  value = module.ollama.base_url
}

output "ollama_security_group_id" {
  value = module.ollama.security_group_id
}

output "ollama_cloudwatch_log_group" {
  value = module.ollama.cloudwatch_log_group
}
