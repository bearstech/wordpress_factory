.Python:
	virtualenv .
	./bin/pip install pex wheel
	./bin/pip install -r requierements.txt

clean:
	rm -f wpfactory.pex
	rm -rf build
	rm -rf dist

pex: .Python
	./bin/python setup.py sdist
	./bin/python setup.py bdist_wheel
	./bin/pex -r docopts -r pyyaml -e wp_factory:main --repo=dist -r wpfactory -o wpfactory.pex


