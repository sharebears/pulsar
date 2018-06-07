lint:
	isort -rc .
test:
	flake8
	./scripts/permissions_checker.py
	mypy --no-strict-optional pulsar/ # --html-report .mypy-html pulsar/
	pytest --cov-report term-missing --cov-branch --cov=pulsar tests/
tests: test
