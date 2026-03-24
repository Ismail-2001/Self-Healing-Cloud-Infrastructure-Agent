# Monorepo Management Makefile
#
# Usage:
#   make build-all
#   make test-all
#   make provision-iac
#   make deploy-k8s

SHELL := /bin/bash

SERVICES := observer diagnosis planner execution chaos cost-guardian
LIBS := shcia-core shcia-contracts

.PHONY: help build-all test-all clean install-deps

help:
	@echo "SHCIA Monorepo Developer Console"
	@echo "--------------------------------"
	@echo "build-all       - Build all service Docker images"
	@echo "test-all        - Run unit and integration tests across services"
	@echo "lint-all        - Enforce code style on all subprojects"
	@echo "provision-iac   - Run terraform plan/apply on production"
	@echo "clean           - Clear all build artifacts and caches"

install-deps:
	pip install -e libs/shcia-core
	pip install -e libs/shcia-contracts
	pip install -r requirements.txt

build-all:
	docker-compose build

test-all:
	pytest tests/unit
	pytest tests/integration

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

provision-iac:
	cd iac/terraform/environments/production && terraform init && terraform apply -auto-approve
