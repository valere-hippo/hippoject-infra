variable "hetznerdns_token" {
  description = "Hetzner DNS API token"
  type        = string
  sensitive   = true
}

variable "root_domain" {
  description = "Primary public domain"
  type        = string
  default     = "hippocloud.de"
}

variable "server_ipv4" {
  description = "Public IPv4 of the Hippoject server"
  type        = string
}

variable "default_ttl" {
  description = "Default DNS TTL"
  type        = number
  default     = 300
}
