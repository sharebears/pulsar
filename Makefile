lint:
	isort -rc .
_tests:
	./scripts/permissions_checker.py
_docs:
	find plugin/docs/ -type f -name "*.rst" -exec touch "{}" \;
	sphinx-build -M html plugins/docs ../pulsar-docs-compiled
tests: _tests
docs: _docs
