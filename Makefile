.PHONY: docker-build docker-run docker-push docker-test help

IMAGE_NAME ?= charlie-agents
IMAGE_TAG ?= latest
REGISTRY ?= ghcr.io/henriquemoody

help:
	@echo "Available targets:"
	@echo "  docker-build    - Build the Docker image"
	@echo "  docker-run      - Run the Docker container"
	@echo "  docker-push     - Push to container registry"
	@echo "  docker-test     - Test the Docker image"

docker-build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-run:
	docker run --rm -v $(PWD):/workspace $(IMAGE_NAME):$(IMAGE_TAG)

docker-push:
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(REGISTRY)/$(IMAGE_NAME):$(IMAGE_TAG)

docker-test:
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) list-agents
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) --help

format:
	ruff format .

lint:
	ruff check .

test:
	pytest --tb=no -q --show-capture=no --disable-warnings --tb=no

test-coverage:
	pytest --tb=no -q --show-capture=no --disable-warnings --tb=no --cov=charlie

analyze:
	mypy --install-types --non-interactive src/charlie

qa:
	make format
	make lint
	make analyze
	make test