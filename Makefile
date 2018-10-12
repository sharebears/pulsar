lint:
	isort -rc .
_tests:
	./scripts/permissions_checker.py
_docs:
	find docs/ -type f -name "*.rst" -exec touch "{}" \;
	sphinx-build -M html docs ../pulsar-docs
tests: _tests
docs: _docs
