variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "production"
}

variable "service_name" {
  description = "Name of the service"
  type        = string
}

variable "image" {
  description = "Container image for the service"
  type        = string
}

variable "port" {
  description = "Service container port"
  type        = number
  default     = 8080
}

variable "replicas" {
  description = "Initial replica count"
  type        = number
  default     = 3
}

variable "cpu_request" {
  description = "Resource request (CPU)"
  type        = string
  default     = "100m"
}

variable "memory_request" {
  description = "Resource request (Memory)"
  type        = string
  default     = "128Mi"
}

variable "cpu_limit" {
  description = "Resource limit (CPU)"
  type        = string
  default     = "200m"
}

variable "memory_limit" {
  description = "Resource limit (Memory)"
  type        = string
  default     = "256Mi"
}

variable "chaos_enabled" {
  description = "Enable chaos experiments on this service"
  type        = bool
  default     = false
}
