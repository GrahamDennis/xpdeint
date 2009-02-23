.PHONY: all update configure clean check

all: waf_build/config.log wscript ../waf
	@../waf build

update:
	@(cd ..; $(MAKE) $(MFLAGS) update;)

waf_build/config.log: wscript ../waf ../waf_extensions/cheetah.py
	@../waf configure

# check examples compile
check:
	@for i in examples/*.xmds; do \
	echo $$i; xpdeint $$i; done