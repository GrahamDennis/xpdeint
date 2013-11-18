# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         = a4

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d ../../documentation/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help clean html web pickle htmlhelp latex changes linkcheck

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html      to make standalone HTML files"
	@echo "  pickle    to make pickle files (usable by e.g. sphinx-web)"
	@echo "  htmlhelp  to make HTML files and a HTML help project"
	@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  changes   to make an overview over all changed/added/deprecated items"
	@echo "  linkcheck to check all external links for integrity"

clean:
	-rm -rf ../../documentation

html:
	mkdir -p ../../documentation ../../documentation/doctrees
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) ../../documentation
	cp images/*.dia ../../documentation/_images/
	@echo
	@echo "Build finished. The HTML pages are in ../../documentation."

pickle:
	mkdir -p ../../documentation/pickle ../../documentation/doctrees
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) ../../documentation/pickle
	@echo
	@echo "Build finished; now you can process the pickle files or run"
	@echo "  sphinx-web ../../documentation/pickle"
	@echo "to start the sphinx-web server."

web: pickle

htmlhelp:
	mkdir -p ../../documentation ../../documentation/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) ../../documentation
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in ../../documentation."

latex:
	mkdir -p ../../documentation/latex ../../documentation/doctrees
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) ../../documentation/latex
	@echo
	@echo "Build finished; the LaTeX files are in ../../documentation/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	mkdir -p ../../documentation/changes ../../documentation/doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) ../../documentation/changes
	@echo
	@echo "The overview file is in ../../documentation/changes."

linkcheck:
	mkdir -p ../../documentation/linkcheck ../../documentation/doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) ../../documentation/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in ../../documentation/linkcheck/output.txt."
