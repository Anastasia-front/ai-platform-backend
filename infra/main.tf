module "network" {
  source = "./modules/network"

  project_name     = var.project_name
  ssh_allowed_cidr = var.ssh_allowed_cidr
}


module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
}

module "iam" {
  source = "./modules/iam"

  project_name       = var.project_name
  uploads_bucket_arn = module.s3.bucket_arn
}

module "ec2" {
  source = "./modules/ec2"

  project_name     = var.project_name
  ami              = var.ec2_ami
  subnet_id        = module.network.subnet_id
  security_group   = module.network.ec2_security_group
  instance_profile = module.iam.instance_profile
  user_data        = "${path.module}/userdata.sh"
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
      DATABASE_URL  = "postgresql+asyncpg://${var.db_username}:${var.db_password}@${module.rds.endpoint}:5432/app"
      AWS_S3_BUCKET = module.s3.bucket_name
      AWS_REGION    = var.aws_region
    }
  )
}
