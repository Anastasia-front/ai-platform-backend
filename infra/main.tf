module "network" {
  source = "./modules/network"

  project_name      = var.project_name
  ssh_allowed_cidrs = var.ssh_allowed_cidrs
}


module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  aws_region   = var.aws_region
}

module "iam" {
  source = "./modules/iam"

  project_name       = var.project_name
  aws_region         = var.aws_region
  uploads_bucket_arn = module.s3.bucket_arn
}

module "ec2" {
  source = "./modules/ec2"

  project_name     = var.project_name
  key_name         = var.key_name
  ami              = var.ec2_ami
  subnet_id        = module.network.subnet_id
  security_group   = module.network.ec2_security_group
  instance_profile = module.iam.instance_profile
  user_data        = "${path.module}/userdata.sh"
}

module "ollama" {
  source = "./modules/ollama"

  project_name                = var.project_name
  aws_region                  = var.aws_region
  instance_type               = var.ollama_instance_type
  key_name                    = var.key_name
  subnet_id                   = module.network.subnet_id
  vpc_id                      = module.network.vpc_id
  backend_security_group_id   = module.network.ec2_security_group
  instance_profile            = module.iam.instance_profile
  associate_public_ip_address = var.ollama_associate_public_ip_address
  root_volume_size            = var.ollama_root_volume_size
  data_volume_size            = var.ollama_data_volume_size
  models                      = var.ollama_models
  enable_private_dns          = var.ollama_enable_private_dns
  ssh_allowed_cidrs           = var.ssh_allowed_cidrs
}

module "rds" {
  source = "./modules/rds"

  project_name   = var.project_name
  username       = var.db_username
  password       = var.db_password
  security_group = module.network.rds_security_group
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
}

module "ssm" {
  source = "./modules/ssm"

  project_name = var.project_name

  env_values = merge(
    var.env_values,
    {
      DATABASE_URL     = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.endpoint}/app"
      AWS_S3_BUCKET    = module.s3.bucket_name
      AWS_REGION       = var.aws_region
      GOOGLE_CLIENT_ID = var.google_client_id
      OLLAMA_BASE_URL  = module.ollama.base_url
    }
  )
}
