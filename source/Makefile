templates = $(wildcard *.tmpl)
cheetah_settings = directiveStartToken="@",commentStartToken="@\#",multiLineCommentStartToken="@*",multiLineCommentEndToken="*@"

.PHONY: compile
compile: .COMPILE

# compile templates as needed
# this is a bit of a hack. is there a better way?
.COMPILE: $(templates)
	@cheetah compile --settings='$(cheetah_settings)' $?
	@touch .COMPILE
	./version.sh

# remove all compiled files
clean:
	@rm -f .COMPILE
	@rm -f *.pyc
	@rm -f $(templates:.tmpl=.py)
	@rm -f $(templates:.tmpl=.py.bak)
