provider "aws" {
  region = var.region
}

module "iceberg" {
  source                    = "../../modules/iceberg"  # Path to the iceberg module
  env                       = var.env
  team                      = var.team
  application               = var.application
  identity_center_role_arn  = var.identity_center_role_arn
  lakeformation_admin_arns  = var.lakeformation_admin_arns
}

output "s3tables_bucket_arn" {
    value = module.iceberg.s3tables_bucket_arn
}

output "s3tables_table_warehouse_location" {
  value = module.iceberg.s3tables_table_warehouse_location
}

output "glue_database_name" {
  value = module.iceberg.glue_database_name
}

output "lakeformation_admins" {
  value = module.iceberg.lakeformation_admins
}
