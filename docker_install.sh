#!/usr/bin/env bash
#Installation for 20.04

# download Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Update repository
sudo apt-get update

# Install Dpcker and Docker-compose
sudo apt-get install -y docker-ce
sudo apt-get install docker-compose -y

# Enable userns-remap on the daemon
sudo echo "{
  \"userns-remap\": \"default\"
}" > /etc/docker/daemon.json
sudo systemctl restart docker

# add group docker for run docker commands without sudo
sudo groupadd docker

# Add current user to the docker group.
sudo usermod -aG docker "${USER}"

# Activate the changes to groups
newgrp docker
