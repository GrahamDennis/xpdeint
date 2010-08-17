# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         = a4

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d ../userdoc/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

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
	-rm -rf ../userdoc

html:
	mkdir -p ../userdoc ../userdoc/doctrees
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) ../userdoc
	@echo
	@echo "Build finished. The HTML pages are in ../userdoc."

pickle:
	mkdir -p ../userdoc/pickle ../userdoc/doctrees
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) ../userdoc/pickle
	@echo
	@echo "Build finished; now you can process the pickle files or run"
	@echo "  sphinx-web ../userdoc/pickle"
	@echo "to start the sphinx-web server."

web: pickle

htmlhelp:
	mkdir -p ../userdoc ../userdoc/doctrees
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) ../userdoc
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in ../userdoc."

latex:
	mkdir -p ../userdoc/latex ../userdoc/doctrees
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) ../userdoc/latex
	@echo
	@echo "Build finished; the LaTeX files are in ../userdoc/latex."
	@echo "Run \`make all-pdf' or \`make all-ps' in that directory to" \
	      "run these through (pdf)latex."

changes:
	mkdir -p ../userdoc/changes ../userdoc/doctrees
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) ../userdoc/changes
	@echo
	@echo "The overview file is in ../userdoc/changes."

linkcheck:
	mkdir -p ../userdoc/linkcheck ../userdoc/doctrees
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) ../userdoc/linkcheck
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in ../userdoc/linkcheck/output.txt."
