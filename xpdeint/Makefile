templates = $(wildcard *.tmpl)
cheetah_settings = directiveStartToken="@",commentStartToken="@\#",multiLineCommentStartToken="@*",multiLineCommentEndToken="*@"

SUBDIRS = SimulationDrivers Geometry Vectors Segments Operators Features

.PHONY: all compile clean check

MYMAKEFLAGS = 'cheetah_settings=$(cheetah_settings)'

all: compile
	@for i in $(SUBDIRS); do \
	(cd $$i; env $(MYMAKEFLAGS) $(MAKE) $(MFLAGS) all); done

compile: .COMPILE

# compile templates as needed
# this is a bit of a hack. is there a better way?
.COMPILE: $(templates)
	@if test "$?"; then \
	cheetah compile --settings='$(cheetah_settings)' $?; fi
	@touch .COMPILE
	@./version.sh


# remove all compiled files
clean:
	@rm -f .COMPILE
	@rm -f *.pyc
	@rm -f $(templates:.tmpl=.py)
	@rm -f $(templates:.tmpl=.py.bak)
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) clean); done

# check examples compile
check:
	@for i in examples/*.xmds; do \
	echo $$i; xpdeint $$i; done