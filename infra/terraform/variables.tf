variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r7g.large"
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "croppilot"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r7g.large"
}

variable "api_cpu" {
  description = "API task CPU units"
  type        = number
  default     = 2048
}

variable "api_memory" {
  description = "API task memory (MB)"
  type        = number
  default     = 4096
}

variable "api_desired_count" {
  description = "Desired number of API tasks"
  type        = number
  default     = 2
}

variable "api_min_count" {
  description = "Minimum API tasks for autoscaling"
  type        = number
  default     = 2
}

variable "api_max_count" {
  description = "Maximum API tasks for autoscaling"
  type        = number
  default     = 10
}

variable "qdrant_host" {
  description = "Qdrant vector database host"
  type        = string
  default     = "localhost"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
}
