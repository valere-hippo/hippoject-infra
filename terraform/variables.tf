variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with DNS edit access"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for the root domain"
  type        = string
}

variable "cloudflare_proxied" {
  description = "Whether Cloudflare should proxy the public DNS records"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Short project prefix used in resource names"
  type        = string
  default     = "hippoject"
}

variable "root_domain" {
  description = "Primary public domain"
  type        = string
  default     = "hippocloud.de"
}

variable "server_type" {
  description = "Hetzner Cloud server type"
  type        = string
  default     = "cpx62"
}

variable "server_image" {
  description = "Hetzner Cloud image"
  type        = string
  default     = "ubuntu-24.04"
}

variable "server_location" {
  description = "Hetzner Cloud location"
  type        = string
  default     = "fsn1"
}

variable "volume_size_gb" {
  description = "Attached persistent volume size in GB"
  type        = number
  default     = 80
}

variable "enable_backups" {
  description = "Enable Hetzner Cloud backups"
  type        = bool
  default     = true
}

variable "ssh_key_name" {
  description = "Name for the bootstrap SSH key in Hetzner Cloud"
  type        = string
  default     = "hippoject-bootstrap"
}

variable "ssh_public_key" {
  description = "Public SSH key content used for initial bootstrap access"
  type        = string
}

variable "admin_ipv4_cidrs" {
  description = "IPv4 CIDRs allowed to reach SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "admin_ipv6_cidrs" {
  description = "IPv6 CIDRs allowed to reach SSH"
  type        = list(string)
  default     = ["::/0"]
}

variable "default_ttl" {
  description = "Default DNS TTL"
  type        = number
  default     = 300
}
