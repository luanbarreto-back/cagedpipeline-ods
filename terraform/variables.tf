variable "aiven_api_token" {
  description = "Token pessoal da Aiven"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Nome do projeto no console da Aiven"
  type        = string
}

variable "cloud_name" {
  description = "Nuvem/região do plano gratuito"
  type        = string
  default     = "do-sfo"
}

variable "plan" {
  description = "Plano gratuito do PostgreSQL"
  type        = string
  default     = "free-1-1gb"
}