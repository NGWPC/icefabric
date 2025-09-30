terraform {
  backend "s3" {
    bucket         = "ngwpc-infra-test"
    key            = "terraform/icefabric/test/edfs/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true  # Encrypt the state file
    #dynamodb_table = "dynamodb-lock-table"  # Optional / FUTURE for state locking
  }
}
