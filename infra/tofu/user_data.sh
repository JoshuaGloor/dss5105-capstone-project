#!/bin/bash
# Runs once on first boot. Installs Docker and the compose plugin.
#
# Templated by OpenTofu: docker_compose_version and compose_arch.
# compose_arch ensures architecture is only defined in tofu/main.tf
# and binary below does not drift from instance selected.
set -euxo pipefail

dnf install -y docker
systemctl enable --now docker

# Install compose and verify checksum. Download under the upstream filename,
# since that is the name recorded inside the .sha256 file.
cd /tmp
base="https://github.com/docker/compose/releases/download/${docker_compose_version}"
file="docker-compose-linux-${compose_arch}"
curl -fsSL "$base/$file" -o "$file"
curl -fsSL "$base/$file.sha256" -o "$file.sha256"
sha256sum -c "$file.sha256"

mkdir -p /usr/local/lib/docker/cli-plugins
install -m 0755 "$file" /usr/local/lib/docker/cli-plugins/docker-compose
rm -f "$file" "$file.sha256"

# Fail loudly here rather than leaving a half-built box for the deploy to trip over.
docker compose version

mkdir -p /opt/app
