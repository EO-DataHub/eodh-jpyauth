# Default input parameters
docker ?= docker

.SILENT:
MAKEFLAGS += --no-print-directory

.PHONY: run-test
run-test:
	cd test; $(docker) compose up --build
