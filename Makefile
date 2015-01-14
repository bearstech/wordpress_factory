.Python:
	virtualenv .
	./bin/pip install --upgrade pex wheel setuptools
	./bin/pip install -r requierements.txt

clean:
	rm -f wpfactory.pex

pex: .Python
	rm ~/.pex/ -rf
	./bin/pex -r docopt -r pyyaml -r wpfactory -e wpfactory:main -o wpfactory.pex -s .


