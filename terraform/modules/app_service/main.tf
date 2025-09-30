locals {
  common_tags = {
    Application = var.app_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# Security Groups
# The security group for the instance should now only allow traffic from within the appropriate VPCs
resource "aws_security_group" "instance" {
  name_prefix = "${var.app_name}-${var.environment}-instance"
  description = "Security group for API instances"
  vpc_id      = data.aws_vpc.main.id

  ingress {
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = var.is_test_env ? null : [aws_security_group.alb[0].id]
    cidr_blocks     = var.is_test_env ? concat([data.aws_vpc.main.cidr_block], var.additional_vpc_cidrs) : null
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = concat([data.aws_vpc.main.cidr_block], var.additional_vpc_cidrs)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}-instance"
  })

  lifecycle {
    create_before_destroy = true
  }
}


# The ALB security group should now only allow internal access
resource "aws_security_group" "alb" {
  count = var.is_test_env ? 0 : 1

  name_prefix = "${var.app_name}-${var.environment}-alb"
  description = "Security group for API load balancer"
  vpc_id      = data.aws_vpc.main.id

  ingress {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = concat([data.aws_vpc.main.cidr_block], var.additional_vpc_cidrs)
  }

  ingress {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = concat([data.aws_vpc.main.cidr_block], var.additional_vpc_cidrs)
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}-alb"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# IAM Resources
resource "aws_iam_role" "instance_role" {
  name = "${var.app_name}-${var.environment}-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  lifecycle {
    create_before_destroy = true
  }

  tags = local.common_tags
}

resource "aws_lakeformation_permissions" "icefabric_tbl" {
  principal   = aws_iam_role.instance_role.arn
  permissions = ["DESCRIBE", "SELECT"]
  catalog_id = data.aws_caller_identity.current.account_id

  lf_tag_policy {
    resource_type = "TABLE"

    expression {
      key    = "Team"
      values = ["EDFS"]
    }

    expression {
      key    = "Environment"
      values = ["Test"]
    }
  }
}

resource "aws_iam_role_policy" "instance_policy" {
  name_prefix = "instance-policy"
  role        = aws_iam_role.instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
    {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = compact([
          var.ad_secret
        ])
      },
      {
        Sid    = "CloudWatchLogsAccess"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.api_logs.arn}:*",
          aws_cloudwatch_log_group.api_logs.arn
        ]
      },
      {
        Sid    = "LakeFormationDataAccess"
        Effect = "Allow"
        Action = "lakeformation:GetDataAccess"
        Resource = "*"
      },
      {
        Sid    = "GlueCatalogReadOnlyAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartitions"
        ]
        Resource = [
          var.glue_catalog_arn,
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:database/*",
          "arn:aws:glue:${var.aws_region}:${data.aws_caller_identity.current.account_id}:table/*/*"
        ]
      },
      {
        Sid    = "S3IcebergDataAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          "${var.data_lake_bucket_arn}",
          "${var.data_lake_bucket_arn}/*",
          "${var.data_bucket_arn}",
          "${var.data_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "instance_profile" {
  name = "${var.app_name}-${var.environment}-instance-profile"
  role = aws_iam_role.instance_role.name
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "session_manager_logging" {
  role       = aws_iam_role.instance_role.id
  policy_arn = var.session_manager_logging_policy_arn
}

# Test Environment Resources
resource "aws_instance" "test_instance" {
  count = var.is_test_env ? 1 : 0

  ami           = var.ami_id != null ? var.ami_id : data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  root_block_device {
    volume_type = var.root_volume_type
    volume_size = var.root_volume_size
    encrypted   = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  iam_instance_profile        = aws_iam_instance_profile.instance_profile.name
  vpc_security_group_ids      = [aws_security_group.instance.id]
  subnet_id                   = data.aws_subnets.private.ids[0]  # Use private subnet
  associate_public_ip_address = false

  user_data_replace_on_change = true
  user_data_base64 = base64encode(templatefile("${path.module}/templates/user_data.sh.tpl", {
    aws_region           = var.aws_region
    container_port       = var.container_port
    s3_bucket            = trimsuffix(var.data_lake_bucket_arn, "/*")
    directory_id         = var.directory_id,
    directory_name       = var.directory_name,
    ad_secret            = var.ad_secret,
    ad_dns_1             = var.ad_dns_1,
    ad_dns_2             = var.ad_dns_2,
    log_group_name       = aws_cloudwatch_log_group.api_logs.name
    environment          = var.environment
    docker_image_uri     = var.docker_image_uri
    deployment_timestamp = var.deployment_timestamp
  }))

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Production Environment Resources
resource "aws_launch_template" "app" {
  count = var.is_test_env ? 0 : 1

  name_prefix   = "${var.app_name}-${var.environment}"
  image_id      = coalesce(var.ami_id, data.aws_ami.ubuntu.id)
  instance_type = var.instance_type
  update_default_version = true

  network_interfaces {
    associate_public_ip_address = false
    security_groups             = [aws_security_group.instance.id]
    delete_on_termination       = true
  }

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size           = var.root_volume_size
      volume_type           = var.root_volume_type
      encrypted             = true
      kms_key_id            = var.kms_key_arn
      delete_on_termination = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  iam_instance_profile {
    name = aws_iam_instance_profile.instance_profile.name
  }

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh.tpl", {
    aws_region           = var.aws_region
    container_port       = var.container_port
    s3_bucket            = trimsuffix(var.data_lake_bucket_arn, "/*")
    directory_id         = var.directory_id,
    directory_name       = var.directory_name,
    ad_secret            = var.ad_secret,
    ad_dns_1             = "10.3.1.74",
    ad_dns_2             = "10.3.0.60",
    log_group_name       = aws_cloudwatch_log_group.api_logs.name
    environment          = var.environment
    docker_image_uri     = var.docker_image_uri
    deployment_timestamp = var.deployment_timestamp
  }))

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(local.common_tags, {
      Name = "${var.app_name}-${var.environment}"
    })
  }

  tag_specifications {
    resource_type = "volume"
    tags = local.common_tags
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_group" "app" {
  count = var.is_test_env ? 0 : 1

  name                = "${var.app_name}-${var.environment}"
  desired_capacity    = var.asg_desired_capacity
  max_size            = var.asg_max_size
  min_size            = var.asg_min_size
  target_group_arns   = [aws_lb_target_group.app[0].arn]
  vpc_zone_identifier = data.aws_subnets.private.ids
  health_check_grace_period = 900 # Adjust depending on the App / Use Case instantiation time
  health_check_type   = "ELB"

  launch_template {
    id      = aws_launch_template.app[0].id
    version = "$Latest"
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage  = 100
      instance_warmup         = 900
      checkpoint_delay        = 900
      checkpoint_percentages  = [25, 50, 75, 100]
    }
  }

  dynamic "tag" {
    for_each = merge(local.common_tags, {
      Name = "${var.app_name}-${var.environment}"
    })
    content {
      key                 = tag.key
      value              = tag.value
      propagate_at_launch = true
    }
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes       = [desired_capacity]
  }

  depends_on = [aws_lb.app]
}

# Load Balancer Resources
resource "aws_lb" "app" {
  count = var.is_test_env ? 0 : 1

  name               = "${var.app_name}-${var.environment}"
  internal           = true  # Make ALB internal since we're in private subnets
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = data.aws_subnets.private.ids  # Use private subnets
  idle_timeout       = 600 # Default is 60 seconds, but some geopackage GETS take a long time.

  enable_deletion_protection = var.enable_deletion_protection

  access_logs {
    bucket  = aws_s3_bucket.alb_logs[0].id
    prefix  = "${var.app_name}-${var.environment}"
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}"
  })
}

resource "aws_lb_target_group" "app" {
  count = var.is_test_env ? 0 : 1

  name     = "${var.app_name}-${var.environment}"
  port     = var.container_port
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.main.id

  health_check {
    enabled             = true
    healthy_threshold   = 3
    interval            = 30
    matcher            = "200"  # Accept 200 from the version endpoint
    path               = "/version/"
    port               = "traffic-port"
    timeout            = 10
    unhealthy_threshold = 3
  }

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb_listener" "https" {
  count = var.is_test_env || var.certificate_arn == null ? 0 : 1

  load_balancer_arn = aws_lb.app[0].arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app[0].arn
  }
}

resource "aws_lb_listener" "http_redirect" {
  count = var.is_test_env ? 0 : 1

  load_balancer_arn = aws_lb.app[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# ALB Logs Bucket
resource "aws_s3_bucket" "alb_logs" {
  count  = var.is_test_env ? 0 : 1
  bucket = "${var.app_name}-${var.environment}-alb-logs-${data.aws_caller_identity.current.account_id}"

  lifecycle {
    prevent_destroy = false
  }

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "alb_logs" {
  count  = var.is_test_env ? 0 : 1
  bucket = aws_s3_bucket.alb_logs[0].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "alb_logs" {
  count  = var.is_test_env ? 0 : 1
  bucket = aws_s3_bucket.alb_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn == null ? "AES256" : "aws:kms"
      kms_master_key_id = var.kms_key_arn  # Will use AES256 if null
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "alb_logs" {
  count  = var.is_test_env ? 0 : 1
  bucket = aws_s3_bucket.alb_logs[0].id

  rule {
    id     = "cleanup_old_logs"
    status = "Enabled"

    # Filter block with an empty prefix applies the rule to all objects
    filter {
      prefix = ""
    }

    expiration {
      days = 90
    }
  }
}

resource "aws_s3_bucket_policy" "alb_logs" {
  count  = var.is_test_env ? 0 : 1
  bucket = aws_s3_bucket.alb_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${lookup(var.alb_service_account_ids, var.aws_region)}:root"
        }
        Action = "s3:PutObject"
        Resource = [
          "${aws_s3_bucket.alb_logs[0].arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = "s3:PutObject"
        Resource = [
          "${aws_s3_bucket.alb_logs[0].arn}/*",
        ]
        Condition = {
          StringEquals = {
            "s3:x-amz-acl": "bucket-owner-full-control"
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.alb_logs[0].arn
      },
      {
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.alb_logs[0].arn,
          "${aws_s3_bucket.alb_logs[0].arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport": "false"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_public_access_block" "alb_logs" {
  count  = var.is_test_env ? 0 : 1
  bucket = aws_s3_bucket.alb_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Route 53 Records
resource "aws_route53_record" "test" {
  count = var.is_test_env ? 1 : 0

  zone_id = var.hosted_zone_id
  name    = "${var.app_name}.${var.environment}.nextgenwaterprediction.com"
  type    = "A"
  ttl     = 300

  records = [
    aws_instance.test_instance[0].private_ip
  ]
}

resource "aws_route53_record" "app" {
  count = var.is_test_env ? 0 : 1

  zone_id = var.hosted_zone_id
  name    = "${var.app_name}.${var.environment}.nextgenwaterprediction.com"
  type    = "A"

  alias {
    name                   = aws_lb.app[0].dns_name
    zone_id                = aws_lb.app[0].zone_id
    evaluate_target_health = true
  }
}

# CloudWatch Resources
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/ec2/${var.app_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  count = var.is_test_env || var.sns_alert_topic_arn == null ? 0 : 1

  alarm_name          = "${var.app_name}-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "High CPU utilization for ${var.app_name} in ${var.environment}"
  alarm_actions       = [var.sns_alert_topic_arn]
  ok_actions          = [var.sns_alert_topic_arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app[0].name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  count = var.is_test_env || var.sns_alert_topic_arn == null ? 0 : 1

  alarm_name          = "${var.app_name}-${var.environment}-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "MemoryUtilization"
  namespace           = "System/Linux"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "High memory utilization for ${var.app_name} in ${var.environment}"
  alarm_actions       = [var.sns_alert_topic_arn]
  ok_actions          = [var.sns_alert_topic_arn]

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.app[0].name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "high_5xx_errors" {
  count = var.is_test_env || var.sns_alert_topic_arn == null ? 0 : 1

  alarm_name          = "${var.app_name}-${var.environment}-high-5xx"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "High 5XX error count for ${var.app_name} in ${var.environment}"
  alarm_actions       = [var.sns_alert_topic_arn]
  ok_actions          = [var.sns_alert_topic_arn]

  dimensions = {
    LoadBalancer = aws_lb.app[0].arn_suffix
  }

  tags = local.common_tags
}