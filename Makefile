DOC_SRC := picmover.1 picmover.5
DOC := $(patsubst %, doc/%.gz, $(DOC_SRC))
SOURCE := picmover.py
DESTDIR ?= /usr 

all: $(DOC) 
	@echo "Done"

# prep for man
%.gz: %
	gzip -c $< > $@

install: $(DOC)
	@chmod 755 picmover.py
	@cp picmover.py $(DESTDIR)/bin/picmover
	@cp doc/picmover.1.gz $(DESTDIR)/share/man/man1
	@cp doc/picmover.5.gz $(DESTDIR)/share/man/man5


uninstall: 
	@rm -fv $(DESTDIR)/bin/picmover
	@rm -fv $(DESTDIR)/share/man/man1/picmover.1.gz
	@rm -fv $(DESTDIR)/share/man/man5/picmover.5.gz

clean:
	rm doc/picmover.*.gz
