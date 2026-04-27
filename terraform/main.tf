locals {
  a_records = {
    auth          = { name = "auth",          value = var.server_ipv4 }
    hippoject     = { name = "hippoject",     value = var.server_ipv4 }
    hippoject_api = { name = "hippoject-api", value = var.server_ipv4 }
  }
}

resource "hetznerdns_zone" "root" {
  name = var.root_domain
  ttl  = var.default_ttl
}

resource "hetznerdns_record" "a_records" {
  for_each = local.a_records

  zone_id = hetznerdns_zone.root.id
  name    = each.value.name
  value   = each.value.value
  type    = "A"
  ttl     = var.default_ttl
}

output "hippoject_domains" {
  value = {
    for key, record in local.a_records : key => "${record.name}.${var.root_domain}"
  }
}
