.PHONY: install install-dev test lint clean build

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -xvs tests/

lint:
	flake8 kupa/
	black --check kupa/

format:
	black kupa/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete

build:
	python setup.py sdist bdist_wheel
