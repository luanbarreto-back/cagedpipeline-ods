terraform {
  required_providers {
    aiven = {
      source  = "aiven/aiven"
      version = ">= 4.0.0, < 5.0.0"
    }
  }
}

provider "aiven" {
  api_token = var.aiven_api_token
}

resource "aiven_pg" "caged" {
  project      = var.project_name
  cloud_name   = var.cloud_name
  plan         = var.plan
  service_name = "pg-caged-ods"
}