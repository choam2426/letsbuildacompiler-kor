.PHONY: check

check:
	uvx ty check --ignore possibly-missing-attribute
	uvx ruff check
	uvx ruff format
