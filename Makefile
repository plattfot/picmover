DOC_SRC := picmover.1 picmover.5
DOC := $(patsubst %, doc/%.gz, $(DOC_SRC))
SOURCE := picmover.py
DESTDIR ?= /usr 
PREFIX ?= src

all: $(DOC) | $(PREFIX) 
	@cp $(SOURCE) $(PREFIX)/bin/picmover
	@cp doc/picmover.1.gz $(PREFIX)/share/man/man1
	@cp doc/picmover.5.gz $(PREFIX)/share/man/man5
	@chmod 755 $(PREFIX)/bin/picmover
	@echo "Done"

$(PREFIX):
	@mkdir -p $@/share/man
	@mkdir -p $@/bin

# prep for man
%.gz: %
	gzip -c $< > $@

install: $(DOC)
	@cp $(PREFIX)/bin/picmover $(DESTDIR)/bin/picmover  
	@cp $(PREFIX)/share/man/man1/picmover.1.gz $(DESTDIR)/share/man/man1/picmover.1.gz
	@cp $(PREFIX)/share/man/man5/picmover.5.gz $(DESTDIR)/share/man/man5/picmover.5.gz

uninstall: 
	@rm -fv $(DESTDIR)/bin/picmover
	@rm -fv $(DESTDIR)/share/man/man1/picmover.1.gz
	@rm -fv $(DESTDIR)/share/man/man5/picmover.5.gz

clean:
	rm -rfv $(PREFIX)
	rm doc/picmover.*.gz
