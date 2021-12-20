provider "aws" {
  region = "us-east-1"
}

// Terraform state managed remotely.
terraform {
  backend "s3" {
    bucket         = "johnsosoka-com-tf-backend"
    key            = "project/jscom-contact-listener/state/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state"
  }
}