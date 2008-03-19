templates = $(wildcard *.tmpl)

SUBDIRS = Integrators

.PHONY: all compile clean

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


# remove all compiled files
clean:
	@rm -f .COMPILE
	@rm -f *.pyc
	@rm -f $(templates:.tmpl=.py)
	@rm -f $(templates:.tmpl=.py.bak)
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) clean); done
