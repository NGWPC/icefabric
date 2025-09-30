provider "aws" {
    region = var.region
}

data "aws_caller_identity" "current" {}

resource "aws_s3tables_table_bucket" "icefabric" {
    name = "${var.env}-${var.application}"
}

resource "aws_s3tables_namespace" "icefabric" {
    namespace        = var.application
    table_bucket_arn = aws_s3tables_table_bucket.icefabric.arn
}

resource "aws_s3tables_table" "icefabric" {
    name             = var.application
    namespace        = aws_s3tables_namespace.icefabric.namespace
    table_bucket_arn = aws_s3tables_table_bucket.icefabric.arn
    format           = "ICEBERG"
}

data "aws_iam_policy_document" "icefabric_bucket_policy_document" {
    statement {
        sid    = "AllowGlueAccess"
        effect = "Allow"
        principals {
            type        = "Service"
            identifiers = ["glue.amazonaws.com"]
        }
        actions = [
            "s3tables:*"
        ]
        resources = [
            "${aws_s3tables_table_bucket.icefabric.arn}/*",
            aws_s3tables_table_bucket.icefabric.arn
        ]
    }
    statement {
        sid    = "AllowAccountAccess"
        effect = "Allow"
        principals {
            type        = "AWS"
            identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
        }
        actions = [
            "s3tables:*"
        ]
        resources = [
            "${aws_s3tables_table_bucket.icefabric.arn}/*",
            aws_s3tables_table_bucket.icefabric.arn
        ]
    }
}

resource "aws_s3tables_table_bucket_policy" "icefabric_policy" {
    resource_policy  = data.aws_iam_policy_document.icefabric_bucket_policy_document.json
    table_bucket_arn = aws_s3tables_table_bucket.icefabric.arn
}

# AWS Glue Catalog Database for Iceberg Tables Metadata
resource "aws_glue_catalog_database" "icefabric_db" {
    name        = "icefabric_db"
    description = "Glue database for Iceberg tables in ${var.application} namespace"
}

# Grant Lake Formation permissions for the database
resource "aws_lakeformation_permissions" "database_permissions" {
    principal = var.identity_center_role_arn
    permissions = [
        "CREATE_TABLE",
        "DESCRIBE",
        "ALTER"
    ]
    permissions_with_grant_option = [
        "CREATE_TABLE",
        "DESCRIBE",
        "ALTER"
    ]
    database {
        name = aws_glue_catalog_database.icefabric_db.name
    }
}

# EDFS currently plans to manage Tables outside of Terraform, but one can grant permissions
# for table(s) (if it exists or after creation) in terraform
#resource "aws_lakeformation_permissions" "table_permissions" {
#  principal = var.identity_center_role_arn
#  permissions = [
#    "SELECT",
#    "INSERT",
#    "DELETE",
#    "ALTER",
#    "DESCRIBE"
#  ]
#  permissions_with_grant_option = [
#    "SELECT",
#    "INSERT",
#    "DELETE",
#    "ALTER",
#    "DESCRIBE"
#  ]
#  table {
#    database_name = aws_glue_catalog_database.icefabric_db.name
#    name          = "icefabric"
#  }
#}

# Set Lake Formation Data Lake Settings (initialize Lake Formation)
resource "aws_lakeformation_data_lake_settings" "main" {
    # Define Lake Formation administrators (This shows up as a popup when you enter the console if we don't set it via IaC.)
    admins = length(var.lakeformation_admin_arns) > 0 ? var.lakeformation_admin_arns : [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
    ]

    # Optional: Allow external data filtering (for cross-account access)
    allow_external_data_filtering = false

    # Optional: Allow full table external data access
    allow_full_table_external_data_access = false

    # Trusted resource owners (for cross-account scenarios)
    trusted_resource_owners = [data.aws_caller_identity.current.account_id]
}


# Outputs
output "s3tables_bucket_arn" {
    value = aws_s3tables_table_bucket.icefabric.arn
}

output "s3tables_table_warehouse_location" {
    value = aws_s3tables_table.icefabric.warehouse_location
}

output "glue_database_name" {
    value = aws_glue_catalog_database.icefabric_db.name
}

output "lakeformation_admins" {
    value = aws_lakeformation_data_lake_settings.main.admins
}
