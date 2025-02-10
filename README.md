# IP Tool

A Python application to gather IP ranges from system interfaces and check for IP range collisions. Designed for use in containerized environments or Kubernetes clusters.

---

## Features

1. **Fetch IP Ranges**: Collects IP ranges from system interfaces and saves them to a file.
2. **Collision Detection**: Detects overlapping IP ranges between containers.
3. **File Locking**: Ensures thread-safe file operations using `FileLock`.

---

## Requirements

- Python 3.9 or above (3.12 was used for development)
- For required Python Libraries please refer to the requirements.txt file

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/tothdave/MSCI-HA.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

Run the script with the desired options:

### Fetch IP Ranges
```bash
python ip_tool.py
```

### Check for Collisions
```bash
python ip_tool.py --check-collision <file_path>
```

## Running Tests

To test the application:

1. Run the tests from command line or from VS Code
   ```bash
   python -m unittest discover
   ```

## Running with Docker

You can run the app using Docker with the following commands:

### 1. Create a Docker Volume
```bash
docker volume create ip-tool
```

### 2. Gather IP Ranges
```bash
docker run -it \
-e IP_RANGES_DIR_PATH=ip-tool-data/ip-ranges \
-e POD_NAME=test1 \
-v ip-tool:/home/msci-user/ip-tool-data \
ip_tool:latest
```

### 3. Gather IP Ranges for Another Pod
```bash
docker run -it \
-e IP_RANGES_DIR_PATH=ip-tool-data/ip-ranges \
-e POD_NAME=test2 \
-v ip-tool:/home/msci-user/ip-tool-data \
ip_tool:latest
```

### 4. Check for Collisions
```bash
docker run -it \
-e IP_RANGES_DIR_PATH=ip-tool-data/ip-ranges \
-e POD_NAME=test1 \
-v ip-tool:/home/msci-user/ip-tool-data \
ip_tool:latest --check-collision <file_name_on_mount>
```

## Running the IP-Tool Containers on Minikube

### Prerequisites

### 1. Install Minikube
Follow the [official installation guide](https://minikube.sigs.k8s.io/docs/start/) for your operating system.

### 2. Start Minikube
Start your Minikube cluster:
```bash
minikube start
```

### 3. Enable NFS on Minikube node

Start your Minikube cluster:
```bash
minikube ssh
```

Run the following commands to set up NFS
```
sudo -i

apt update && apt -y upgrade

apt install -y nfs-server

mkdir /data

chown 1001:1001 /data #id of msci-user

cat <<EOF >> /etc/exports
/data <Insert ip addr of node here>(rw,no_subtree_check,no_root_squash)
EOF

systemctl enable --now nfs-server

exportfs -ar
```

### 4.Create Cluster

Create namespace:
```bash
kubectl create namespace msci-home-assignment
```

Change default ns:
```bash
kubectl config set-context --current --namespace=msci-home-assignment
```

Apply k8s files:
```bash
kubectl apply -f pv.yaml
kubectl apply -f pvc.yaml
kubectl apply -f ip-tool-job.yaml
kubectl apply -f ip-tool-collisions-job.yaml
```