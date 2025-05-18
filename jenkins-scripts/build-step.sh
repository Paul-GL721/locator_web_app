#!/bin/bash

#### CHECK VERSIONS OF DOCKER AND COMPOSE ###
docker-compose --version
docker version
echo "Building the docker production image"

# Build, tag, and push the production image to Docker Registry
# Build, tag, and push the staging image to docker public repository
docker build -t ${DOCKER_ACCOUNT}/${REMOTE_REPO_NAME}:V$VERSION -f ./$BASE_DIRECTORY/Dockerfile ./$BASE_DIRECTORY

whoami
echo usr=$USER

# Switch user and login and push image to docker hub 
#(credentials are in the pass credsStore) 
sudo su ubuntu <<HERE
whoami
echo usr=$USER
docker push ${DOCKER_ACCOUNT}/${REMOTE_REPO_NAME}:V$VERSION
HERE

echo "Docker image pushed successfully to Docker Registry!"