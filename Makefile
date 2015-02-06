.Python:
	virtualenv .
	./bin/pip install --upgrade pex wheel setuptools

clean:
	rm -f wpfactory
	rm -rf dist

install: .Python
	./bin/python setup.py install

#pex: .Python
#	rm -rf ~/.pex
#	./bin/python setup.py sdist
#	./bin/pex -r six -r requests -r docker-compose -r clint -r docopt -r pyyaml -e wpfactory:main -o wpfactory -s .


