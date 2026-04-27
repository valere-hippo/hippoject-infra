terraform {
  required_version = ">= 1.5.0"

  required_providers {
    hetznerdns = {
      source  = "timohirt/hetznerdns"
      version = ">= 2.1.0"
    }
  }
}

provider "hetznerdns" {
  apitoken = var.hetznerdns_token
}
