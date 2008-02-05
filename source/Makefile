templates = $(wildcard *.tmpl)
cheetah_settings = directiveStartToken="@",commentStartToken="@\#",multiLineCommentStartToken="@*",multiLineCommentEndToken="*@"

# compile all the templates
compile: $(templates:.tmpl=.py)

# How to make a py from a tmpl
%.py: %.tmpl
	@cheetah compile --settings='$(cheetah_settings)' $<

# remove all compiled files
clean:
	@rm -f *.pyc
	@rm -f $(templates:.tmpl=.py)
