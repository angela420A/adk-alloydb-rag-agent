variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "env" {
  type = string
}

variable "network_id" {
  type = string
}

variable "psc_googleapis_ip" {
  type        = string
  description = "Global PSC endpoint IP output from modules/psc"
}

variable "psc_model_armor_ip" {
  type = string
}