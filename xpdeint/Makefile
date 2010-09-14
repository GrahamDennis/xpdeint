.PHONY: all update configure clean check

all: waf_build/config.log .lock-wscript wscript waf_build/c4che
	@./waf-light build
	@sh version.sh

update:
	@(cd ..; $(MAKE) $(MFLAGS) update;)

.lock-wscript: wscript waf_extensions/cheetah.py
	@./waf-light configure

waf_build/config.log: wscript waf_extensions/cheetah.py
	@./waf-light configure

waf_build/c4che: wscript waf_extensions/cheetah.py
	@./waf-light configure

clean:
	@./waf-light clean

# check examples compile
check:
	@for i in examples/*.xmds; do \
	echo $$i; xpdeint $$i; done