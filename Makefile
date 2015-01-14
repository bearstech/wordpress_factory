.Python:
	virtualenv .
	./bin/pip install --upgrade pex wheel setuptools
	./bin/pip install -r requierements.txt

clean:
	rm -f wpfactory
	rm -rf dist

install: .Python
	./bin/pip install .

pex: .Python
	rm -rf ~/.pex/
	./bin/pex -r docopt -r pyyaml -r wpfactory -e wpfactory:main -o wpfactory -s .


