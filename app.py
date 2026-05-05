import os
import datetime
from flask import Flask, render_template, jsonify
import psutil

app = Flask(__name__)


def get_cpu():
    freq = psutil.cpu_freq()
    return {
        "percent": psutil.cpu_percent(interval=0.5),
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "freq_mhz": round(freq.current, 0) if freq else 0,
    }


def get_memory():
    mem = psutil.virtual_memory()
    return {
        "percent": mem.percent,
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
    }


def get_disk():
    path = "/" if os.name != "nt" else "C:\\"
    disk = psutil.disk_usage(path)
    return {
        "percent": disk.percent,
        "total_gb": round(disk.total / (1024 ** 3), 2),
        "used_gb": round(disk.used / (1024 ** 3), 2),
        "free_gb": round(disk.free / (1024 ** 3), 2),
    }


def get_network():
    net = psutil.net_io_counters()
    return {
        "bytes_sent_mb": round(net.bytes_sent / (1024 ** 2), 2),
        "bytes_recv_mb": round(net.bytes_recv / (1024 ** 2), 2),
    }


def get_uptime():
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"


def get_docker_containers():
    try:
        import docker
        client = docker.from_env()
        containers = client.containers.list(all=True)
        result = []
        for c in containers:
            image = c.image.tags[0] if c.image.tags else "none"
            ports = list(c.ports.keys()) if c.ports else []
            result.append({
                "id": c.short_id,
                "name": c.name,
                "image": image,
                "status": c.status,
                "ports": ", ".join(ports) if ports else "-",
            })
        return {"data": result, "error": None}
    except ImportError:
        return {"data": [], "error": "docker library not installed"}
    except Exception as e:
        return {"data": [], "error": str(e)}


def get_k8s_pods():
    try:
        from kubernetes import client, config
        try:
            config.load_incluster_config()
        except Exception:
            config.load_kube_config()
        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)
        result = []
        for p in pods.items:
            result.append({
                "name": p.metadata.name,
                "namespace": p.metadata.namespace,
                "status": p.status.phase or "Unknown",
                "node": p.spec.node_name or "-",
                "restarts": sum(
                    cs.restart_count
                    for cs in (p.status.container_statuses or [])
                ),
            })
        return {"data": result, "error": None}
    except ImportError:
        return {"data": [], "error": "kubernetes library not installed"}
    except Exception as e:
        return {"data": [], "error": str(e)}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/metrics")
def metrics():
    return jsonify({
        "cpu": get_cpu(),
        "memory": get_memory(),
        "disk": get_disk(),
        "network": get_network(),
        "uptime": get_uptime(),
        "docker": get_docker_containers(),
        "kubernetes": get_k8s_pods(),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
 
