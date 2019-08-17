lint:
	isort -rc .
	black -S -t py36 -l 79 .

tests:
	./scripts/permissions_checker.py

docs:
	find plugins/docs/ -type f -name "*.rst" -exec touch "{}" \;
	sphinx-build -M html plugins/docs ../pulsar-docs

.PHONY: lint tests docs
