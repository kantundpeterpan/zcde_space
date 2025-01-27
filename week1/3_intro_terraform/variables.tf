variable "credentials" {
    description = "Credentials"
    default = "./workspaceaddon-436615-4bcf737409b7.json"
}

variable "project" {
    description = "Project"
    default = "workspaceaddon-436615"
}

variable "region" {
    description = "Region"
    default = "us-central1"
}


variable "location" {
    description = "Project location"
    default = "EU"
}

variable "bq_dataset_name" {
    description = "The BQ dataset name"
    default = "demo_dataset"
}

variable "gcs_bucket_name" {
    description = "Storage Bucket Name"
    default = "workspaceaddon-436615-terra-bucket"
}

variable "gcs_class" {
    description = "Bucket Storage Class"
    default = "STANDARD"
}