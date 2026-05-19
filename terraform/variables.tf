variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "quantum-mind"
}

variable "environment" {
  description = "Deployment environment (staging, production)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "quantum_mind"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "ecs_cpu" {
  description = "ECS task CPU units (256, 512, 1024, 2048)"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "ECS task memory in MiB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecr_image_url" {
  description = "Full ECR image URL including tag"
  type        = string
}

variable "secrets_manager_arn" {
  description = "ARN of the AWS Secrets Manager secret containing app credentials"
  type        = string
}
