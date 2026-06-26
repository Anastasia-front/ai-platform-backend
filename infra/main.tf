module "network" {
  source = "./modules/network"

  project_name = var.project_name
}

module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
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

module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
}

module "ssm" {
  source = "./modules/ssm"

  project_name = var.project_name
  env_values   = var.env_values
}