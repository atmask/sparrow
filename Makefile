# Variables
DOCKER_IMAGE := sparrow
DOCKER_TAG := $(shell cat version.txt)
SPARROW_DIR := $(shell pwd)

.PHONY: all
all: venv build build_docker

################
#  Components  #
################
.PHONY: venv
venv:
	echo "Creating virtual environment..."
	poetry install

.PHONY: build
build:
	@echo "Building package..."
	@poetry build

.PHONY: build_docker
build_docker: build
	@echo "Building Docker Image..."
	docker buildx build --platform linux/amd64 -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

.PHONY: build_docker_dev
build_docker_dev:
	@echo "Building Developer Docker Image..."
	docker buildx build --platform linux/amd64 -t $(DOCKER_IMAGE)-dev . -f ./Dockerfile-Dev

.PHONY: run_docker
run_docker:
	@echo "Running Docker container with code volume..."
	docker run -it -v $(SPARROW_DIR):/mnt/sparrow -p 5000:5000 $(DOCKER_IMAGE)-dev /bin/bash