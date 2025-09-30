# AWS S3 Tables with Apache Iceberg - Terraform Implementation

This directory contains PoC Terraform IaC for deploying Apache Iceberg tables using the AWS S3 Tables service with AWS Glue catalog integration.  It also contains a basic demo / test python script used to verify things.

## Architecture Overview

The infrastructure creates:
- **AWS S3 Tables bucket** - Managed storage for Iceberg table data
- **S3 Tables namespace and table** - Logical organization for tables
- **AWS Glue Catalog database** - Metadata storage for table schemas
- **Lake Formation permissions** - Access control and governance
- **IAM policies** - Secure access between services

## Prerequisites

### AWS Requirements
- AWS CLI configured with appropriate credentials. (Older versions may not support AWS S3 Tables)
- Terraform >= 1.0
- AWS Account with permissions (basically Admin due to IAM requirements) for:
  - S3 Tables
  - AWS Glue
  - Lake Formation
  - IAM

### ⚠️ Critical: Enable S3 Table Buckets Integration

**This step must be completed before running Terraform**, otherwise the deployment will fail.

1. Navigate to the [S3 Table Buckets Console](https://console.aws.amazon.com/s3tables/home) in your target region
2. Locate the section titled **"Integration with AWS analytics services"**
3. Click the **"Enable integration"** button
4. Confirm that the integration status shows **"Enabled"** for your deployment region

This integration allows services like Athena, Glue, Redshift, and EMR to interact with S3 Table Buckets. Without this step, your Iceberg tables won't be accessible through these analytics services.

> **Note**: This is a one-time setup per AWS region. Once enabled, all future S3 Table Buckets in that region will have access to AWS analytics services integration.

### Python Requirements
- Python 3.8+
- pyiceberg python module w/deps
- boto3 (for AWS SDK)

## Quick Start

### 1. High Level Deploy Infrastructure

Create a `terraform.tfvars` file replacing the values below as appropriate for your environment or deploy:

```hcl
env                      = "dev"
application              = "myapp"
team                     = "NGWPC"
region                   = "us-east-1"
identity_center_role_arn = "arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_DataRole"

# Optional: Specify Lake Formation admins
lakeformation_admin_arns = [
  "arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_DataRole",
  "arn:aws:iam::123456789012:role/aws-reserved/sso.amazonaws.com/AWSReservedSSO_Admin"
]
```

Deploy the infrastructure:

```bash
terraform init
terraform plan
terraform apply
```

### 3. Set Environment Variables

After deployment, set these environment variables for the Python demo:

```bash
# From Terraform outputs
export ICEBERG_WAREHOUSE_PATH=$(terraform output -raw s3tables_table_warehouse_location)
export AWS_DEFAULT_REGION="us-east-1"
```

### 4. Install Python Dependencies in your preferred active virtual environment

```bash
pip install pyiceberg boto3 mypy_boto3_glue pyarrow
```

### 5. Run the Demo

```bash
python iceberg_demo.py
```

## Terraform Configuration

### Variables

| Variable | Description | Type | Default | Required |
|----------|-------------|------|---------|----------|
| `region` | AWS region | string | `us-east-1` | No |
| `env` | Environment name (test/oe/other) | string | - | Yes |
| `application` | Application name | string | - | Yes |
| `team` | Team name (for future tagging if supported) | string | - | Yes |
| `identity_center_role_arn` | IAM role ARN for accessing resources | string | - | Yes |
| `lakeformation_admin_arns` | Lake Formation administrator ARNs | list(string) | `[]` | No |

### Outputs

| Output | Description |
|--------|-------------|
| `s3tables_bucket_arn` | ARN of the S3 Tables bucket |
| `s3tables_table_warehouse_location` | Warehouse location for Iceberg tables (devs need this!!!) |
| `glue_database_name` | Name of the Glue catalog database |
| `lakeformation_admins` | List of Lake Formation administrators |

## Python Integration

### Basic Usage

The provided `iceberg_demo.py` demonstrates:
- Connecting to AWS Glue catalog
- Creating/loading Iceberg tables
- Very Basic schema definition

### Configuration

The Python script uses these environment variables:
- `ICEBERG_WAREHOUSE_PATH` - S3 Tables warehouse location
- `AWS_REGION` - AWS region for services
- `AWS_DEFAULT_REGION` - Default AWS region

## Permissions and Security

### Lake Formation Integration

The infrastructure automatically configures basic Lake Formation settings. This can get very granular in the future.
- Database-level permissions for the specified Identity Center role (SoftwareEngineersFull)
- Table-level permissions are supported, but have not been tested
