# JupyterHub configuration file (z2jh-style configmap content)
# Deployed as a ConfigMap: jupyterhub-config, mounted at /etc/jupyterhub/jupyterhub_config.py
import os
import sys

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
c = get_config()  # noqa: F821 (provided by JupyterHub runtime)

# base_url=/ide/ enables sub-path access via LAN IP without hosts configuration
c.JupyterHub.base_url = "/ide/"
c.JupyterHub.port = 8000
c.JupyterHub.ip = "0.0.0.0"

# SQLite database on the persistent hub volume (survives restarts)
c.JupyterHub.db_url = "sqlite:///srv/jupyterhub/jupyterhub.sqlite"
c.JupyterHub.db_type = "sqlite"

# Keep the hub process in the foreground (container main process)
c.JupyterHub.concurrent_spawn_limit = 64

# Upgrade the database automatically on hub start
c.JupyterHub.upgrade_db = True

# Data files / working dir
c.JupyterHub.data_files_path = "/srv/jupyterhub"

# ---------------------------------------------------------------------------
# Authenticator: DummyAuthenticator -> self-registration (any username/password)
# ---------------------------------------------------------------------------
# Users enter any username + any password to self-register and log in.
# This gives multi-tenant access without a shared password.
c.JupyterHub.authenticator_class = "jupyterhub.auth.DummyAuthenticator"
c.DummyAuthenticator.password = None  # None => accept ANY password (self-register)
c.Authenticator.auto_login = False   # show login page so users can pick a username
c.Authenticator.create_users = True  # create users on first login
# Allow any username (students self-register). No whitelist.
c.Authenticator.whitelist = set()
c.Authenticator.allowed_users = set()
c.Authenticator.allow_all = True

# Persist registered users so they survive hub restarts
c.Authenticator.admin_users = set()
c.Authenticator.delete_invalid_users = True

# Enable the "Admin Access" tab (manage users) for admins if configured
c.JupyterHub.admin_access = False

# ---------------------------------------------------------------------------
# Spawner: KubeSpawner -> each user gets their own Pod with persistent storage
# ---------------------------------------------------------------------------
c.JupyterHub.spawner_class = "kubespawner.KubeSpawner"

# Image used for each student's single-user workspace pod.
# Same custom image: Python3 + Java + Go + Node.js + JupyterLab
c.KubeSpawner.image = "10.100.135.132:5000/jupyterhub/custom:4.0.2"
c.KubeSpawner.image_pull_policy = "IfNotPresent"

# Run as non-root (jovyan, uid 1000). Match the scipy-notebook image.
c.KubeSpawner.uid = 1000
c.KubeSpawner.gid = 100
c.KubeSpawner.fs_gid = 100
c.KubeSpawner.supplemental_gids = []

# Workspace container command: start JupyterLab single-user server
c.KubeSpawner.cmd = ["jupyter", "labhub"]  # jupyterlab enabled; falls back to lab
c.KubeSpawner.args = []
# Allow the default working directory (home) to be writable
c.KubeSpawner.working_dir = None

# Naming: jupyterhub-<username>
c.KubeSpawner.name_template = "jupyterhub-{username}"

# ---------------------------------------------------------------------------
# Persistent storage: each user gets 5Gi persistent volume
# ---------------------------------------------------------------------------
c.KubeSpawner.user_storage_pvc_ensure = True
c.KubeSpawner.user_storage_class = "local-path"
c.KubeSpawner.user_storage_access_modes = ["ReadWriteOnce"]
c.KubeSpawner.user_storage_capacity = "5Gi"

# Mount the persistent volume at /home/jovyan/work (persists student work)
c.KubeSpawner.user_storage_mounts = [
    {
        "mountPath": "/home/jovyan/work",
        "name": "user-workspace-{username}",
        "pvc_name_template": "jupyterhub-{username}-workspace",
        "volume_mount_mode": "rw",
    }
]

# Allow the spawned pod to use the existing image's env (Python/Java/Go paths)
c.KubeSpawner.environment = {
    "JUPYTER_ENABLE_LAB": "yes",
    "SHELL": "/bin/bash",
    "GOPATH": "/home/jovyan/go",
}

# Resources per user (scaled for 1000 concurrent users on a 2-node cluster,
# each node ~32 CPU / 130 Gi memory; this keeps headroom for ~500-1000 pods)
c.KubeSpawner.cpu_limit = 2
c.KubeSpawner.cpu_guarantee = 0.2
c.KubeSpawner.mem_limit = "2G"
c.KubeSpawner.mem_guarantee = "256M"

# Spawn timeout: large images / first pull
c.KubeSpawner.start_timeout = 300
c.KubeSpawner.http_timeout = 120

# Schedule user pods across nodes (prefer worker)
c.KubeSpawner.node_selector = {}
# Spread across nodes to avoid hotspotting one node
c.KubeSpawner.pod_affinity_required = False
c.KubeSpawner.pod_anti_affinity = False

# Keep the hub's SA so kubespawner can talk to the API
c.KubeSpawner.service_account = "jupyterhub-user-sa"

# Lifecycle hooks: nothing special
c.KubeSpawner.lifecycle_hooks = {}

# Extra labels for spawned pods
c.KubeSpawner.extra_labels = {
    "app.kubernetes.io/name": "jupyterhub",
    "app.kubernetes.io/component": "singleuser-server",
}

# Notebook directory shown on launch
c.Spawner.notebook_dir = "/home/jovyan/work"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
c.JupyterHub.log_level = "INFO"
c.KubeSpawner.log_level = "INFO"
