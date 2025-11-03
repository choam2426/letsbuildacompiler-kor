.PHONY: check test

check:
	uvx ty check --ignore possibly-missing-attribute
	uvx ruff check
	uvx ruff format

test:
	uv run python -m unittest discover -s tests/

