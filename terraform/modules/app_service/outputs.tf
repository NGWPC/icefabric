output "instance_security_group_id" {
  description = "ID of the instance security group"
  value       = aws_security_group.instance.id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = var.is_test_env ? null : aws_security_group.alb[0].id
}

output "instance_role_arn" {
  description = "ARN of the instance IAM role"
  value       = aws_iam_role.instance_role.arn
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.api_logs.name
}

output "alb_dns_name" {
  description = "DNS name of the ALB"
  value       = var.is_test_env ? null : aws_lb.app[0].dns_name
}

output "endpoint" {
  description = "API endpoint URL"
  value       = var.is_test_env ? "http://${aws_route53_record.test[0].name}" : "https://${aws_route53_record.app[0].name}"
}

output "asg_name" {
  description = "Name of the Auto Scaling Group"
  value       = var.is_test_env ? null : aws_autoscaling_group.app[0].name
}

output "instance_id" {
  description = "ID of the test instance (test environment only)"
  value       = var.is_test_env ? aws_instance.test_instance[0].id : null
}

output "alb_logs_bucket" {
  description = "Name of the S3 bucket storing ALB logs"
  value       = var.is_test_env ? null : aws_s3_bucket.alb_logs[0].id
}

output "ami_id" {
  description = "AMI ID being used for EC2 instances"
  value       = var.ami_id != null ? var.ami_id : data.aws_ami.ubuntu.id
}
