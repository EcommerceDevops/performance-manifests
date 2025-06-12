# Performance Testing Framework with Locust & Helmfile

This repository provides a scalable and flexible framework for running various types of performance tests using [Locust](https://locust.io/) on Kubernetes. It leverages [Helmfile](https://github.com/helmfile/helmfile) to declaratively manage test configurations, enabling repeatable and automated performance testing for different scenarios like `load`, `stress`, `spike`, and `endurance` testing.

The core idea is to treat each type of performance test as a distinct **environment** within Helmfile, allowing for tailored configurations for each scenario.

## 🚀 Core Components

| Component               | Chart/Provider        | Purpose                                                                                                                  |
| :---------------------- | :-------------------- | :----------------------------------------------------------------------------------------------------------------------- |
| **Locust**              | `deliveryhero/locust` | The main engine for running distributed performance tests. It simulates user traffic against a target application.       |
| **Test Config Chart**   | `local-chart`         | A local Helm chart responsible for packaging and deploying Locust test scripts (`.py` files) as Kubernetes `ConfigMap`s. |
| **Prometheus Exporter** | `local-chart`         | A sidecar that exposes Locust metrics in a Prometheus-compatible format, enabled via the local chart.                    |

## 📋 Prerequisites

Before you begin, ensure you have the following tools installed:

- [**kubectl**](https://kubernetes.io/docs/tasks/tools/install-kubectl/): To interact with your Kubernetes cluster.
- [**Helm**](https://helm.sh/docs/intro/install/): The package manager for Kubernetes.
- [**Helmfile**](https://github.com/helmfile/helmfile): A declarative spec for deploying Helm charts.

## 📁 Repository Structure

The project is structured to separate test logic (Python scripts) from deployment configuration.

```
.
├── config
│   ├── dev/
│   ├── endurance/
│   ├── load/
│   ├── spike/
│   └── stress/
├── helm-default-values
├── helmfile.yaml.gotmpl
├── locust-dash.json
├── locust-tests
│   └── chart-config/
└── README.md
```

- **`config/`**: This directory contains subdirectories for each performance test type (`load`, `stress`, etc.). Each subdirectory holds a `locust.yml` file that defines the specific parameters for that test (e.g., number of users, spawn rate, worker resources).
- **`helmfile.yaml.gotmpl`**: The main Helmfile definition. It defines the Helm repository, the different test environments, and the release orchestration.
- **`locust-dash.json`**: A pre-built Grafana dashboard definition for visualizing Locust metrics scraped by Prometheus.
- **`locust-tests/chart-config/`**: This is a **local Helm chart** that does not run Locust itself, but rather prepares the configuration for it.
  - `files/`: Contains the actual Locust test scripts (`endurance.py`, `load.py`, etc.) and any shared libraries (`lib/`).
  - `templates/`: Contains templates to create Kubernetes `ConfigMap`s from the test scripts and a `ServiceMonitor` for Prometheus.

## ⚡ Running a Performance Test

Executing a performance test is done by selecting an environment with Helmfile. The target host is specified via an environment variable.

### **Step-by-Step Guide**

1.  **Set the Target Host:**
    Export an environment variable named `HOST` with the full URL of the application you want to test.

    ```bash
    export HOST="https://your-application-url.com"
    ```

2.  **Choose a Test Type and Deploy:**
    Use the `helmfile --environment <test-type> apply` command. Helmfile will use the environment name to select both the correct configuration file and the corresponding test script.

    ```bash
    # To run a STRESS test:
    helmfile --environment stress apply

    # To run a LOAD test:
    helmfile --environment load apply

    # To run an ENDURANCE test:
    helmfile --environment endurance apply
    ```

### Tearing Down the Test Environment

Once your test is complete, you can remove all the deployed resources for that environment with the `destroy` command:

```bash
helmfile --environment stress destroy
```

## ⚙️ How It Works

This framework uses a two-stage release process orchestrated by Helmfile to achieve its flexibility.

1.  **Release 1: `locust-config`**

    - This release uses our local Helm chart at `./locust-tests/chart-config`.
    - Its primary job is to read the Python scripts from the `files/` directory and package them into two `ConfigMap`s:
      - `custom-locust-scripts`: Contains the main test files (`load.py`, `stress.py`, etc.).
      - `custom-locust-libs`: Contains shared library code from the `lib/` folder.
    - It also deploys a `ServiceMonitor` to allow Prometheus to scrape Locust metrics.

2.  **Release 2: `locust`**

    - This release deploys Locust using the official `deliveryhero/locust` Helm chart.
    - It uses a `needs` directive (`needs: - testing/locust-config`) to ensure that the `ConfigMap`s with our test scripts are created **before** the Locust pods start.
    - The configuration for this release is dynamically loaded from the `config/<test-type>/locust.yml` file.

### Dynamic Script Selection

The `helmfile.yaml.gotmpl` uses templating to dynamically select the correct Locust script based on the chosen environment:

```yaml
# In helmfile.yaml.gotmpl, inside the 'locust-config' release:
values:
  - locustfile: "{{ .Environment.Name }}.py"
```

When you run `helmfile --environment stress apply`, this template resolves to `locustfile: "stress.py"`, telling Locust to execute that specific script.

## 🔬 Understanding the Locust Chart Values

The configuration for each test is defined in a `locust.yml` file. This file overrides the default values of the `deliveryhero/locust` chart.

### Default Chart Values (Key Parameters)

Here are some of the most important default values from the `deliveryhero/locust` chart that you can override:

| Parameter                                  | Description                                                                            | Default                  |
| :----------------------------------------- | :------------------------------------------------------------------------------------- | :----------------------- |
| **`loadtest.locust_host`**                 | The target host for the test. We override this with the `HOST` env var.                | `https://www.google.com` |
| **`loadtest.locust_locustfile_configmap`** | The `ConfigMap` containing the Locust scripts. We set this to `custom-locust-scripts`. | `example-locustfile`     |
| **`loadtest.locust_lib_configmap`**        | The `ConfigMap` containing the library files. We set this to `custom-locust-libs`.     | `example-lib`            |
| **`worker.replicas`**                      | The initial number of worker pods.                                                     | `1`                      |
| **`worker.resources`**                     | CPU/Memory requests and limits for worker pods.                                        | `{}` (none)              |
| **`worker.hpa.enabled`**                   | Enables the standard Kubernetes Horizontal Pod Autoscaler.                             | `false`                  |
| **`worker.keda.enabled`**                  | Enables autoscaling with KEDA.                                                         | `false`                  |
| **`master.args`**                          | A list of command-line arguments passed to the Locust master process.                  | `[]` (none)              |
| **`master.resources`**                     | CPU/Memory requests and limits for the master pod.                                     | `{}` (none)              |
| **`service.type`**                         | The type of service to expose the Locust UI.                                           | `ClusterIP`              |

---

### Example Configuration: `config/stress/locust.yml`

This example demonstrates a configuration for a stress test, featuring automated execution and KEDA-based autoscaling.

```yaml
# --- Test Configuration ---
loadtest:
  # The host to be load tested is set by the HOST environment variable.
  locust_host: "https://blazedemo.com" # This is a placeholder, HOST var takes precedence

  # Link to the ConfigMaps created by our 'locust-config' chart
  locust_locustfile_configmap: "custom-locust-scripts"
  locust_lib_configmap: "custom-locust-libs"

# --- Worker and Autoscaling Configuration (KEDA) ---
worker:
  replicas: 1 # Initial replicas, KEDA will manage this
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 1000m
      memory: 1024Mi

  # KEDA Autoscaling Configuration
  keda:
    enabled: true
    minReplicas: 1 # Always keep at least one worker running
    maxReplicas: 20 # Scale up to a maximum of 20 workers
    triggers: |
      - type: metrics-api
        metadata:
          activationTargetValue: "0"   # Activate scaling when user count > 0
          targetValue: "100"   # Add a new worker for every 100 users
          url: "http://{{ template "locust.fullname" . }}.{{ .Release.Namespace }}.svc.cluster.local:{{ $.Values.service.port }}/stats/requests"
          format: json
          valueLocation: 'user_count'

# --- Master Configuration ---
master:
  # Command-line arguments for automated test execution
  args:
    - "--master"
    - "--master-bind-host=0.0.0.0"
    - "--autostart" # Start the test immediately without UI interaction
    - "--users=1500" # Total number of concurrent users to simulate
    - "--spawn-rate=50" # Ramp up 50 users per second
    - "--run-time=3h" # Stop the test automatically after 3 hours
  resources:
    requests:
      cpu: 1000m
      memory: 1024Mi
    limits:
      cpu: 2000m
      memory: 2048Mi

# --- Expose Locust UI ---
service:
  type: NodePort # Use NodePort for easy access during development
```

### Automating Test Behavior with Master Arguments

The `master.args` section is key to running fully automated tests without manual intervention.

- `--autostart`: This flag tells Locust to begin the test as soon as the master and at least one worker are ready. This is essential for CI/CD pipelines.
- `--users=<N>`: Defines the total number of concurrent users to simulate in the test.
- `--spawn-rate=<R>`: Sets the rate at which users are "spawned" or added to the test, in users per second.
- `--run-time=<T>`: Specifies a duration for the test (e.g., `1h30m`). When the time is up, Locust will automatically stop the test and shut down.
- `--autoquit=0`: Can be used to make the master process exit after a test run, which is useful in CI environments.

By combining these arguments in different `locust.yml` files, you can precisely define the behavior of each test type (e.g., a short, intense `spike` test vs. a long, steady `endurance` test) and run them in a fully automated fashion.
