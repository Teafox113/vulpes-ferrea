# Vulpes Ferrea — build commands
# Windows without make: run the python commands shown on each target directly.

PY ?= python3

.PHONY: all build fonts setup clean

all: build

## setup: install dependencies
setup:
	$(PY) -m pip install -r requirements.txt

## build: regenerate outlines from the generator, then build every deliverable
build:
	$(PY) scripts/build_glyphs.py

## fonts: rebuild fonts and documentation from sources/glyphs.json only (no outline changes)
fonts:
	$(PY) scripts/export_fonts.py

## clean: remove Python caches
clean:
	rm -rf scripts/__pycache__
