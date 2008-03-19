SOURCE = $(wildcard ../xpdeint/*py)

default: html

pdf: $(SOURCE)
	epydoc --config=epydoc.cfg --pdf

html: $(SOURCE)
	epydoc --config=epydoc.cfg --html

.PHONY: clean
clean:
	rm -rf html
	rm -rf pdf
