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
  type        = string
  description = "The ID of the VPC network"
}

variable "subnet_id" {
  type = string
}

variable "psc_googleapis_ip" {
  type        = string
  description = "Internal IP of the global PSC endpoint. Required and must not fall within any subnet CIDR range"
}
