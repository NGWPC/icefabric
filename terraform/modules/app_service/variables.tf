variable "environment" {
  description = "Environment name (test or oe)"
  type        = string

  validation {
    condition     = contains(["test", "oe"], var.environment)
    error_message = "Environment must be either 'test' or 'oe'."
  }
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "app_name" {
  description = "Name of the application for resource naming"
  type        = string
}

variable "docker_image_uri" {
  description = "The full URI of the Docker image to deploy (e.g., ghcr.io/ngwpc/icefabric:latest)"
  type        = string
}

variable "vpc_name" {
  description = "Name of the VPC to deploy into"
  type        = string
  default     = "main"
}

variable "subnet_name_pattern" {
  description = "Pattern to match for target subnets in the VPC"
  type        = string
  default     = "App*"
}

variable "data_lake_bucket_arn" {
  description = "ARN of the S3 bucket for the Iceberg data lake."
  type        = string
}

variable "data_bucket_arn" {
  description = "ARN of the S3 bucket for app data."
  type        = string
}

variable "glue_catalog_arn" {
  description = "ARN of the Glue Catalog."
  type        = string
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone ID for DNS records"
  type        = string
}

variable "ami_id" {
  description = "AMI ID for EC2 instances. If not provided, latest ubuntu-jammy-22.04-amd64-server AMI will be used."
  type        = string
  default     = null

  validation {
    condition     = var.ami_id == null || can(regex("^ami-[a-f0-9]{17}$", var.ami_id))
    error_message = "If provided, AMI ID must be valid (e.g., ami-123456789abcdef01)."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "root_volume_type" {
  description = "Type of root volume (gp2, gp3, io1, etc.)"
  type        = string
  default     = "gp3"
}

variable "root_volume_size" {
  description = "Size of root volume in GB"
  type        = number
  default     = 20
}

variable "is_test_env" {
  description = "Whether this is a test environment (true for single instance, false for ASG/ALB)"
  type        = bool
}

variable "asg_min_size" {
  description = "Minimum number of instances in the ASG"
  type        = number
  default     = 1
}

variable "asg_max_size" {
  description = "Maximum number of instances in the ASG"
  type        = number
  default     = 3
}

variable "asg_desired_capacity" {
  description = "Desired number of instances in the ASG"
  type        = number
  default     = 2
}

variable "certificate_arn" {
  description = "ARN of ACM certificate for HTTPS. Required only for non-test, load balanced environments."
  type        = string
  default     = null

  validation {
    condition     = var.certificate_arn == null || can(regex("^arn:aws:acm:[a-z0-9-]+:\\d{12}:certificate/[a-zA-Z0-9-]+$", var.certificate_arn))
    error_message = "If provided, must be a valid ACM certificate ARN."
  }
}

variable "container_port" {
  description = "Port that the container listens on"
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "Path for ALB health check"
  type        = string
  default     = "/health"
}

variable "health_check_interval" {
  description = "Interval for health checks (in seconds)"
  type        = number
  default     = 15
}

variable "health_check_timeout" {
  description = "Timeout for health checks (in seconds)"
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Number of consecutive successful health checks before considering target healthy"
  type        = number
  default     = 2
}

variable "health_check_unhealthy_threshold" {
  description = "Number of consecutive failed health checks before considering target unhealthy"
  type        = number
  default     = 2
}

variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs"
  type        = number
  default     = 30
}

variable "sns_alert_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms. Required only for non-test environments."
  type        = string
  default     = null

  validation {
    condition     = var.sns_alert_topic_arn == null || can(regex("^arn:aws:sns:[a-z0-9-]+:\\d{12}:[a-zA-Z0-9-_]+$", var.sns_alert_topic_arn))
    error_message = "If provided, must be a valid SNS topic ARN."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for ALB"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "ARN of KMS key for encryption. If not provided, AWS managed keys will be used."
  type        = string
  default     = null
}

variable "session_manager_logging_policy_arn" {
  description = "ARN of the Session Manager logging policy"
  type        = string
  default     = "arn:aws:iam::591210920133:policy/AWSAccelerator-SessionManagerLogging"
}

variable "additional_vpc_cidrs" {
  description = "List of additional VPC CIDR blocks that should have access to the instance in test environment"
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for cidr in var.additional_vpc_cidrs : can(regex("^([0-9]{1,3}\\.){3}[0-9]{1,3}/[0-9]{1,2}$", cidr))])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation (e.g., '10.0.0.0/16')."
  }
}

variable "directory_id" {
  description = "ID of the AWS Managed Microsoft AD directory for Windows instances"
  type        = string
  default     = ""
}

variable "directory_name" {
  description = "Fully qualified domain name of the AWS Managed Microsoft AD"
  type        = string
  default     = ""
}

variable "ad_secret" {
  description = "ARN of the Secrets Manager secret containing AD join credentials"
  type        = string
}

variable "ad_dns_1" {
  description = "Primary DNS server IP address for the AWS Managed Microsoft AD"
  type        = string
  default     = ""
}

variable "ad_dns_2" {
  description = "Secondary DNS server IP address for the AWS Managed Microsoft AD"
  type        = string
  default     = ""
}

variable "deployment_timestamp" {
  description = "Timestamp to force redeployment of the container (format: YYYYMMDDHHMMSS)"
  type        = string
  default     = null
}