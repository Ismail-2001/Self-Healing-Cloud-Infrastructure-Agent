terraform {
  required_version = ">= 1.0"
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.11"
    }
  }
}

provider "kubernetes" {
  config_path = "~/.kube/config"
}

module "payment_service" {
  source       = "../../modules/service"
  service_name = "payment-service"
  namespace    = "production"
  image        = "nginx:alpine" # Mocking real service image
  port         = 80
  replicas     = 3
  chaos_enabled = true
}

module "checkout_service" {
  source       = "../../modules/service"
  service_name = "checkout-service"
  namespace    = "production"
  image        = "nginx:alpine"
  port         = 80
  replicas     = 2
}
