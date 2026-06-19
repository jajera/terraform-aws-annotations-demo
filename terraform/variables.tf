variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-2"
}

variable "enable_scheduler" {
  description = "Create a one-time EventBridge schedule to invoke ingest Lambda. Default false so apply/destroy never require schedule_time."
  type        = bool
  default     = false
}

variable "deploy_amplify_on_apply" {
  description = "Build and deploy the React app to Amplify after apply (avoids the default Welcome page)."
  type        = bool
  default     = true
}

variable "schedule_time" {
  description = "UTC datetime for one-time scheduler (YYYY-MM-DDTHH:mm:ss). Used only when enable_scheduler is true; set in terraform.tfvars or -var."
  type        = string
  default     = "2099-01-01T00:00:00"

  validation {
    condition = can(regex(
      "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$",
      var.schedule_time,
    ))
    error_message = "schedule_time must be UTC format YYYY-MM-DDTHH:mm:ss."
  }
}

variable "enable_dynamodb" {
  description = "Enable optional DynamoDB annotation mirror"
  type        = bool
  default     = false
}

variable "private_bucket_name" {
  description = "Name for the private destination bucket"
  type        = string
  default     = "volcano-annotations-demo-private"
}

variable "geonet_bucket" {
  description = "Public source bucket for GeoNet camera images"
  type        = string
  default     = "geonet-open-data"
}

variable "camera_path" {
  description = "Camera path segment in GeoNet key structure"
  type        = string
  default     = "TKAH/TKAH.01"
}

variable "amplify_app_name" {
  description = "Amplify application name"
  type        = string
  default     = "volcano-annotations-demo"
}
