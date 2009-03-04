.PHONY: all update configure clean check

all: waf_build/config.log wscript
	@./waf-light build
	@sh version.sh

update:
	@(cd ..; $(MAKE) $(MFLAGS) update;)

waf_build/config.log: wscript waf_extensions/cheetah.py
	@./waf-light configure

# check examples compile
check:
	@for i in examples/*.xmds; do \
	echo $$i; xpdeint $$i; done