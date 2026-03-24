output "app_labels" {
  description = "Application labels for service selection"
  value       = kubernetes_deployment.service.spec[0].template[0].metadata[0].labels
}

output "service_dns" {
  description = "Internal Kubernetes DNS for the service"
  value       = "${kubernetes_service.service.metadata[0].name}.${kubernetes_service.service.metadata[0].namespace}.svc.cluster.local"
}
