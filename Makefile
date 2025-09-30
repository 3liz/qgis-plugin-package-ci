SHELL:=bash

PYTHON_MODULE=qgispluginci

-include .localconfig.mk

REQUIREMENT_GROUPS= \
	dev \
	tests \
	$(NULL)

.PHONY: update-requirements

# Rebuild requirements only if uv.lock change
requirements.txt: uv.lock

requirements.txt:
	@echo "Updating requirements.txt"
	@uv export --all-extras --no-dev --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--no-emit-workspace \
		-q -o requirements.txt;

update-requirements: requirements.txt $(patsubst %,update-requirements-%, $(REQUIREMENT_GROUPS))

update-requirements-dev: uv.lock
	@echo "Updating requirements for 'dev'"
	@uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		-q -o requirements/tests.txt

update-requirements-%: uv.lock
	@echo "Updating requirements for '$*'"; 
	@uv export --format requirements.txt \
		--no-annotate \
		--no-editable \
		--no-hashes \
		--only-group $* \
		-q -o requirements/$*.txt; \

#
# Static analysis
#

LINT_TARGETS=$(PYTHON_MODULE) $(EXTRA_LINT_TARGETS)

lint:
	@ $(UV_RUN) ruff check --preview  --output-format=concise $(LINT_TARGETS)

lint-fix:
	@ $(UV_RUN) ruff check --preview --fix $(LINT_TARGETS)

format:
	@ $(UV_RUN) format $(LINT_TARGETS) 

typecheck:
	@ $(UV_RUN) mypy $(LINT_TARGETS)

scan:
	@ $(UV_RUN) bandit -r $(PYTHON_MODULE) $(SCAN_OPTS)


check-uv-install:
	@which uv > /dev/null || { \
		echo "You must install uv (https://docs.astral.sh/uv/)"; \
		exit 1; \
	}

#
# Tests
#

test:
	$(UV_RUN) pytest -v tests/

#
# Build package
#
.PHONY: dist
dist:
	@rm -rf dist/*
	@uv build  --wheel

#
# Code managment
#

# Display a summary of codes annotations
show-annotation-%:
	@grep -nR --color=auto --include=*.py '# $*' lizmap/ || true

# Output variable
echo-variable-%:
	@echo "$($*)"
