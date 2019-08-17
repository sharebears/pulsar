lint:
	isort -rc .

tests:
	./scripts/permissions_checker.py

docs:
	find plugins/docs/ -type f -name "*.rst" -exec touch "{}" \;
	sphinx-build -M html plugins/docs ../pulsar-docs-compiled

.PHONY: lint tests docs
