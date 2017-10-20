DESTDIR ?= /usr
PREFIX ?= pkg
BUILD ?= build

DOCS = 1 5
SRCS = main.cpp
TEST = main.cpp picmover.cpp

CXX = g++

CXXFLAGS = -std=c++17 -Wall
LDFLAGS = 

ifeq ($(DEBUG),)
  CXXFLAGS += -O2 -flto
else
  CXXFLAGS += -g -DNDEBUG
endif

.PHONY: all
all: docs exec 

.PHONY: docs
docs: $(foreach x,$(DOCS),$(PREFIX)/share/man/man$x/picmover.$x.gz)

.PHONY: exec
exec: $(PREFIX)/bin/picmover

.PHONY: install
install: all | $(DESTDIR)
	cp -a $(PREFIX)/* $(DESTDIR)/

.PHONY: test
test: $(BUILD)/test/picmover
	./$<

.PHONY: clean
clean:
	rm -rfv $(PREFIX) $(BUILD)

## Executable
$(PREFIX)/bin/picmover: $(SRCS:%.cpp=$(BUILD)/%.o) | $(PREFIX)/bin; $(link)
$(BUILD)/%.o: src/%.cpp | $(BUILD); $(compile)

## Test
$(BUILD)/test/picmover: $(TEST:%.cpp=$(BUILD)/test/%.o) | $(BUILD)/test; $(link)
$(BUILD)/test/%.o: test/%.cpp | $(BUILD)/test; $(compile)

## Create directories
$(PREFIX)/% $(BUILD)/%: ; @$(mkdir)
$(DESTDIR) $(BUILD): ; @$(mkdir)

## Docs generation:
$(foreach x,$(DOCS),$(eval $(call doc_recipe,$x)))

## Compiling and linking recepies
define compile =
$(CXX) $(CXXFLAGS) $(XCXXFLAGS) -c $< -o $@
endef

define link =
$(CXX) $(LDFLAGS) $(XLDFLAGS) $< -o $@
endef

define mkdir =
mkdir -p $@
endef

define doc_recipe =
$$(PREFIX)/share/man/man$1/picmover.$1.gz: doc/picmover.$1 | $(PREFIX)/share/man/man$1
	gzip -c $$< > $$@
endef

