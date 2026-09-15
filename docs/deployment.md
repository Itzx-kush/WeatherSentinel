# Deployment status

Part 1 is distributed as an installable Python package and CLI. It has no HTTP process, database, container, or frontend to deploy. Windows setup is reproducible through `scripts/setup.ps1`.

Docker and production service configuration will be introduced only when a real API exists. This avoids presenting an empty container as deployment readiness.
