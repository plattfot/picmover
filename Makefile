DOC_SRC := picmover.1 picmover.5
DOC := $(patsubst %, doc/%.gz, $(DOC_SRC))
SOURCE := picmover.py
DESTDIR ?= /usr
PREFIX ?= src

all: $(DOC) | $(PREFIX) 
	@cp $(SOURCE) $(PREFIX)/bin/picmover           && \
	cp doc/picmover.1.gz $(PREFIX)/share/man/man1/ && \
	cp doc/picmover.5.gz $(PREFIX)/share/man/man5/ && \
	chmod 755 $(PREFIX)/bin/picmover               && \
	echo "Done"

$(PREFIX) $(DESTDIR):
	@mkdir -p $@/share/man/man1 && \
	mkdir -p $@/share/man/man5  && \
	mkdir -p $@/bin

# prep for man
%.gz: %
	gzip -c $< > $@
# Copy the files, including the tree structure to the destination. Note that this doesn't work on OS X.
install: $(DOC) | $(DESTDIR)
	@cd $(PREFIX) && \
	cp --parents bin/picmover share/man/man1/picmover.1.gz share/man/man5/picmover.5.gz $(DESTDIR)

uninstall: 
	@rm -fv $(strip $(DESTDIR))/bin/picmover
	@rm -fv $(strip $(DESTDIR))/share/man/man1/picmover.1.gz
	@rm -fv $(strip $(DESTDIR))/share/man/man5/picmover.5.gz

clean:
	rm -rfv $(PREFIX)
	rm doc/picmover.*.gz
