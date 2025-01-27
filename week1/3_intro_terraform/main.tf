terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.17.0"
    }
  }
}

provider "google" {
  # Configuration options

  project = "workspaceaddon-436615"
  region  = "us-central1"
}

resource "google_storage_bucket" "demo-bucket" {
  name          = "workspaceaddon-436615-terra-bucket"
  location      = "EU"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1 #days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}