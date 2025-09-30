# variables.tf

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "env" {
  description = "Environment name"
  type        = string
}

variable "application" {
  description = "Application name"
  type        = string
}

variable "team" {
  description = "Team name"
  type        = string
}

variable "identity_center_role_arn" {
  description = "ARN of the Identity Center role that will access the resources"
  type        = string
}

variable "lakeformation_admin_arns" {
  description = "List of ARNs to set as Lake Formation administrators"
  type        = list(string)
  default     = [] # Will be populated with current account or specific users/roles
}
