SUBDIRS = xpdeint

.PHONY: all update clean check distclean

all:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) all); done

update:
	@svn up
	@$(MAKE) $(MFLAGS) all

# remove all compiled files
clean:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) clean); done

# check examples compile
check:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) check); done

distclean:
	@for i in $(SUBDIRS); do \
	(cd $$i; $(MAKE) $(MFLAGS) distclean); done
