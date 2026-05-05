terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "docker_image" "dashboard" {
  name         = "siddheshinde1/devops-dashboard:latest"
  keep_locally = true
}

resource "docker_container" "dashboard" {
  image = docker_image.dashboard.image_id
  name  = "tf-devops-dashboard"
  ports {
    internal = 5000
    external = 5001
  }
  restart = "unless-stopped"
}
