resource "kubernetes_deployment" "service" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
    labels = {
      app              = var.service_name
      "shcia-managed"  = "true"
      "chaos-enabled"  = var.chaos_enabled ? "true" : "false"
    }
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = var.service_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.service_name
        }
      }

      spec {
        container {
          image = var.image
          name  = var.service_name

          port {
            container_port = var.port
          }

          resources {
            requests = {
              cpu    = var.cpu_request
              memory = var.memory_request
            }
            limits = {
              cpu    = var.cpu_limit
              memory = var.memory_limit
            }
          }

          liveness_probe {
            http_get {
              path = "/health"
              port = var.port
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }

          readiness_probe {
            http_get {
              path = "/ready"
              port = var.port
            }
            initial_delay_seconds = 5
            period_seconds        = 5
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "service" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
  }

  spec {
    selector = {
      app = var.service_name
    }

    port {
      port        = 80
      target_port = var.port
    }

    type = "ClusterIP"
  }
}

resource "kubernetes_pod_disruption_budget" "service" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
  }

  spec {
    min_available = "50%"
    selector {
      match_labels = {
        app = var.service_name
      }
    }
  }
}
