output "service_uri" {
  value     = aiven_pg.caged.service_uri
  sensitive = true
}

output "service_host" {
  value = aiven_pg.caged.service_host
}

output "service_port" {
  value = aiven_pg.caged.service_port
}