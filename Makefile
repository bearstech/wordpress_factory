.Python:
	virtualenv .
	./bin/pip install --upgrade pex wheel setuptools
	./bin/pip install -r requierements.txt

clean:
	rm -f wpfactory.pex
	rm -rf build
	rm -rf dist

pex: .Python
	./bin/python setup.py sdist
	./bin/python setup.py bdist_wheel
	./bin/pex -r docopt -r pyyaml -e wpfactory:main --repo=dist -r wpfactory -o wpfactory.pex -s .


