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