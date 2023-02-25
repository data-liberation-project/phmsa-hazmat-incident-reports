.PHONY: README.md tests venv

PYTHON_DIRS=scripts tests

requirements.txt: requirements.in
	pip-compile requirements.in

venv:
	python -m venv venv
	venv/bin/pip install -r requirements.txt

format:
	black $(PYTHON_DIRS)
	isort $(PYTHON_DIRS)

lint:
	black --check $(PYTHON_DIRS)
	isort --check $(PYTHON_DIRS)
	flake8 $(PYTHON_DIRS)

mypy:
	mypy $(PYTHON_DIRS) --strict --ignore-missing-imports --explicit-package-bases 

tests:
	python -m pytest -sv --cov tests
