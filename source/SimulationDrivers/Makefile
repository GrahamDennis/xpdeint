templates = $(wildcard *.tmpl)

.PHONY: all compile

all: compile

compile: .COMPILE

# compile templates as needed
# this is a bit of a hack. is there a better way?
.COMPILE: $(templates)
	@if test "$?"; then \
	cheetah compile --settings='$(cheetah_settings)' $?; fi
	@touch .COMPILE


# remove all compiled files
clean:
	@rm -f .COMPILE
	@rm -f *.pyc
	@rm -f $(templates:.tmpl=.py)
	@rm -f $(templates:.tmpl=.py.bak)
