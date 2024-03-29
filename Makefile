.PHONY: README.md tests venv output/feed.rss

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
	mypy $(PYTHON_DIRS)

tests:
	python -m pytest -sv --cov tests

fetch-data:
	venv/bin/python scripts/00-fetch.py 

discover-dates:
	venv/bin/python scripts/01-get-discovery-dates.py

publish-feed:
	venv/bin/python scripts/03-generate-rss.py

ensure-unstaged:
	@git diff --cached --quiet || (echo "Cannot run while files staged" && false)

run-feed: ensure-unstaged output/feed.rss
	git add output/feed.rss
	git diff --cached --quiet || git commit -m "Update feed"
