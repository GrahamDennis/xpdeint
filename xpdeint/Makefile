.PHONY: all update clean check distclean

all: wscript waf_extensions/cheetah.py c4che/
	@support/waf-light build
	@sh version.sh

update:
	@(cd ..; $(MAKE) $(MFLAGS) update;)

c4che: wscript waf_extensions/cheetah.py
	@support/waf-light configure

clean:
	@support/waf-light clean

# check examples compile
check:
	@for i in examples/*.xmds; do \
	echo $$i; xmds2 $$i; done

distclean:
	@support/waf-light distclean