init:
	pip install -r requirements.txt
lint:
	flake8 .
format:
	black .
publish:
	pip install --upgrade build
	pip install --upgrade twine
	python -m build
	twine upload dist/*
	rm -fr build dist src/pysdrradio.egg-info