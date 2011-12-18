.PHONY: all update clean check distclean

all: wscript waf_extensions/cheetah.py c4che/
	@waf/waf-light build
	@sh version.sh

update:
	@(cd ..; $(MAKE) $(MFLAGS) update;)

c4che: wscript waf_extensions/cheetah.py
	@waf/waf-light configure

clean:
	@waf/waf-light clean

# check examples compile
check:
	@for i in examples/*.xmds; do \
	echo $$i; xmds2 $$i; done

distclean:
	@waf/waf-light distclean