.PHONY:
test.unit:
	poetry run pytest --cov=netbox_sd  tests/unit