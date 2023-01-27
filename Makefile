VERSION = $$(poetry run toml get --toml-path pyproject.toml tool.poetry.version)

restore:
	poetry install
	poetry run pre-commit install

test:
	poetry run coverage run -m pytest tests -x --show-capture=stdout
	poetry run coverage report

format:
	poetry run autoflake -r --in-place --remove-all-unused-imports pydantic_xml tests
	poetry run black pydantic_xml tests
	poetry run isort pydantic_xml tests

type:
	poetry run mypy dexml

type-strict:
	poetry run mypy dexml --strict

check:
	poetry run pylint -j8 -E dexml

style:
	poetry run pylint dexml --fail-under=8

build:
	poetry build

update-init:
	@sed -i "s/__version__ = .*/__version__ = \"$(VERSION)\"/g" dexml/__init__.py
	git commit -am "v"$(VERSION)

release: update-init build
	poetry publish --skip-existing
	git tag $(VERSION)
	git push origin $(VERSION)
	git push

release-patch:
	poetry version patch
	make release
