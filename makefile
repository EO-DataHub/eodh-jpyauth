# Default input parameters
docker ?= docker

.SILENT:
MAKEFLAGS += --no-print-directory

.PHONY: build
build:
	uv build

.PHONY: publish
publish: build
	uv publish --token $(token)
