data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "terraform_remote_state" "vpc" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "vpc/terraform.tfstate"
    region = var.region
  }
}


data "terraform_remote_state" "platform" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = var.state_bucket
    key    = "platform/terraform.tfstate"
    region = var.region
  }
}


data "terraform_remote_state" "universal" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "universal/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "account" {
  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "account/terraform.tfstate"
    region = var.region
  }
}

locals {
  name              = "${var.team_name}-${var.env}-${var.project_name}"
  hosted_zone_name  = terraform.workspace == "prod" ? var.domain_name : "${terraform.workspace}.${var.domain_name}"
  internal_hostname = "${var.project_name}.internal"
  host              = terraform.workspace == "prod" ? "${local.internal_hostname}.${var.domain_name}" : "${local.internal_hostname}.${terraform.workspace}.${var.domain_name}"
  public_host       = terraform.workspace == "prod" ? "${var.project_name}.i.ai.gov.uk" : "${var.project_name}.${terraform.workspace}.i.ai.gov.uk"
  host_backend      = terraform.workspace == "prod" ? "${var.project_name}-backend-external.${var.domain_name}" : "${var.project_name}-backend-external.${terraform.workspace}.${var.domain_name}" 
}

data "aws_ssm_parameter" "auth_api_invoke_url" {
  name = "/i-dot-ai-${terraform.workspace}-core-auth-api/auth/INVOKE_URL"
}

data "aws_secretsmanager_secret" "slack" {
  name = "i-dot-ai-${var.env}-platform-slack-webhook"
}

data "aws_secretsmanager_secret_version" "platform_slack_webhook" {
  secret_id = data.aws_secretsmanager_secret.slack.id
}

data "aws_wafv2_ip_set" "ip_whitelist_internal" {
  name  = "i-dot-ai-core-ip-config-ip-set-internal"
  scope = var.scope
}

data "aws_route53_zone" "zone" {
  name = local.hosted_zone_name
}

data "aws_ssm_parameter" "edge_secret" {
  name = "/i-dot-ai-${terraform.workspace}-core-edge-network/header-secret"
}
