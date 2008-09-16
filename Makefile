SUBDIRS = xpdeint

.PHONY: all clean check

all:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) all); done

# remove all compiled files
clean:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) clean); done

# check examples compile
check:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) check); done
