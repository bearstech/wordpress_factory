.Python:
	virtualenv .
	./bin/pip install --upgrade pex wheel setuptools
	./bin/pip install -r requirements.txt

clean:
	rm -f wpfactory
	rm -rf dist

install: .Python
	./bin/python setup.py install

pex: .Python
	rm -rf ~/.pex
	./bin/python setup.py sdist
	./bin/pex -r docopt -r pyyaml -e wpfactory:main -o wpfactory -s .


