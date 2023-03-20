# SPDX-FileCopyrightText: 2023 Fredrik Salomonsson <plattfot@posteo.net>
#
# SPDX-License-Identifier: GPL-3.0-or-later

DOC_SRC := picmover.1 picmover.5
DOC := $(patsubst %, doc/%.gz, $(DOC_SRC))
SOURCE := picmover.py
DESTDIR ?= /usr
PREFIX ?= src

.PHONY: all
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
.PHONY: install
install: $(DOC) | $(DESTDIR)
	@cd $(PREFIX) && \
	cp --parents bin/picmover share/man/man1/picmover.1.gz share/man/man5/picmover.5.gz $(DESTDIR)

.PHONY: uninstall
uninstall:
	@rm -fv $(strip $(DESTDIR))/bin/picmover
	@rm -fv $(strip $(DESTDIR))/share/man/man1/picmover.1.gz
	@rm -fv $(strip $(DESTDIR))/share/man/man5/picmover.5.gz

.PHONY: clean
clean:
	rm -rfv $(PREFIX)
	rm doc/picmover.*.gz
