# Default input parameters
docker ?= docker

.SILENT:
MAKEFLAGS += --no-print-directory

.PHONY: run-dev
run-dev:
	cd test && \
	$(docker) compose up --build -d && \
	$(docker) compose logs -f -t

.PHONY: stop-dev
stop-dev:
	cd test && \
	$(docker) compose down

.PHONY: destroy-dev
destroy-dev:
	cd test && \
	$(docker) compose rm -fsv

.PHONY: build
build:
	uv build

.PHONY: publish
publish: build
	uv publish --token $(token)
