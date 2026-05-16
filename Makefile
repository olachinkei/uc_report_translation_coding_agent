.PHONY: check lint test format alignment generated-docs generated-docs-check clean-pycache

PYTHON ?= python3

check: clean-pycache lint test alignment

lint:
	$(PYTHON) scripts/harness_lint.py

test:
	@$(PYTHON) -m compileall -q src skills scripts tests; \
	status=$$?; \
	if [ $$status -eq 0 ]; then \
		$(PYTHON) -m unittest discover -s tests; \
		status=$$?; \
	fi; \
	$(MAKE) --no-print-directory clean-pycache >/dev/null; \
	exit $$status

alignment:
	@$(PYTHON) skills/translation-memory-builder/scripts/validate_corpus_alignment.py \
		--corpus-dir data/past_markdown_files \
		--strict; \
	status=$$?; \
	$(MAKE) --no-print-directory clean-pycache >/dev/null; \
	exit $$status

generated-docs:
	$(PYTHON) scripts/refresh_generated_docs.py

generated-docs-check:
	$(PYTHON) scripts/refresh_generated_docs.py --check

format:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format src skills scripts; \
		ruff check --fix src skills scripts; \
	else \
		echo "ruff is not installed. Install dev tools with: python3 -m pip install -e '.[dev]'"; \
		exit 1; \
	fi

clean-pycache:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
