templates = $(wildcard *.tmpl)

# compile all the templates
compile: $(templates:.tmpl=.py)

# How to make a py from a tmpl
%.py: %.tmpl
	@cheetah compile $<

# remove all compiled files
clean:
	@rm -f *.pyc
	@rm -f $(templates:.tmpl=.py)
