locals {
  server_name = "${var.project_name}-prod"

  dns_records = {
    auth          = { name = "auth",          value = hcloud_server.hippoject.ipv4_address }
    hippoject     = { name = "hippoject",     value = hcloud_server.hippoject.ipv4_address }
    hippoject_api = { name = "hippoject-api", value = hcloud_server.hippoject.ipv4_address }
  }
}

resource "hcloud_ssh_key" "bootstrap" {
  name       = var.ssh_key_name
  public_key = var.ssh_public_key
}

resource "hcloud_firewall" "hippoject" {
  name = "${var.project_name}-firewall"

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "22"
    source_ips = concat(var.admin_ipv4_cidrs, var.admin_ipv6_cidrs)
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "80"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = "443"
    source_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "tcp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "udp"
    port            = "1-65535"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }

  rule {
    direction       = "out"
    protocol        = "icmp"
    destination_ips = ["0.0.0.0/0", "::/0"]
  }
}

resource "hcloud_server" "hippoject" {
  name        = local.server_name
  server_type = var.server_type
  image       = var.server_image
  location    = var.server_location
  backups     = var.enable_backups
  ssh_keys    = [hcloud_ssh_key.bootstrap.id]
  user_data = templatefile("${path.module}/templates/cloud-init.yaml.tftpl", {
    hostname = local.server_name
  })

  public_net {
    ipv4_enabled = true
    ipv6_enabled = true
  }

  labels = {
    project = var.project_name
    service = "hippoject"
    env     = "production"
  }
}

resource "hcloud_firewall_attachment" "hippoject" {
  firewall_id = hcloud_firewall.hippoject.id
  server_ids  = [hcloud_server.hippoject.id]
}

resource "hcloud_volume" "hippoject" {
  name      = "${var.project_name}-data"
  size      = var.volume_size_gb
  format    = "ext4"
  server_id = hcloud_server.hippoject.id
  automount = true

  labels = {
    project = var.project_name
    service = "hippoject"
    env     = "production"
  }
}

resource "cloudflare_dns_record" "a_records" {
  for_each = local.dns_records

  zone_id = var.cloudflare_zone_id
  name    = each.value.name
  type    = "A"
  ttl     = var.default_ttl
  content = each.value.value
  proxied = var.cloudflare_proxied
}

output "server_name" {
  value = hcloud_server.hippoject.name
}

output "server_ipv4" {
  value = hcloud_server.hippoject.ipv4_address
}

output "server_ipv6" {
  value = hcloud_server.hippoject.ipv6_address
}

output "volume_linux_device" {
  value = hcloud_volume.hippoject.linux_device
}

output "hippoject_domains" {
  value = {
    for key, record in local.dns_records : key => "${record.name}.${var.root_domain}"
  }
}

output "ansible_inventory_entry" {
  value = "${hcloud_server.hippoject.name} ansible_host=${hcloud_server.hippoject.ipv4_address} ansible_user=root"
}

output "ssh_command" {
  value = "ssh root@${hcloud_server.hippoject.ipv4_address}"
}
