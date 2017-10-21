DESTDIR ?= /usr
PREFIX ?= pkg
BUILD ?= build

PREFIX_INC_DIR=$(PREFIX)/include/picmover
PREFIX_MAN_DIR=$(PREFIX)/share/man

DOCS = 1 5
SRCS = main.cpp
TEST = main.cpp picmover.cpp
INCL = $(notdir $(wildcard src/*.hpp))
CXX = g++

CXXFLAGS += -std=gnu++1z
CXXFLAGS += -Wall
CXXFLAGS += -I $(PREFIX)/include
CXXFLAGS += -MMD -MP
LDFLAGS = -lexiv2 -lstdc++fs

ifeq ($(DEBUG),)
  CXXFLAGS += -O2 -flto -DNDEBUG
else
  CXXFLAGS += -g
endif

.PHONY: all docs exec install headers test clean

all: exec docs headers
install: all | $(DESTDIR); cp -a $(PREFIX)/* $(DESTDIR)/
exec: $(PREFIX)/bin/picmover
docs: $(foreach x,$(DOCS),$(PREFIX_MAN_DIR)/man$x/picmover.$x.gz)
headers: $(INCL:%=$(PREFIX_INC_DIR)/%)
test: $(BUILD)/test/picmover ; ./$<
clean: ; rm -rfv $(PREFIX) $(BUILD) $(TEST_SANDBOX)

## Executable
$(PREFIX)/bin/picmover: $(SRCS:%.cpp=$(BUILD)/%.o) | $(PREFIX)/bin; $(link)
$(BUILD)/%.o: src/%.cpp | $(BUILD); $(compile)

## Test
# Catch is using broken pragmas
$(BUILD)/test/picmover: CXXFLAGS += -Wno-unknown-pragmas
$(BUILD)/test/picmover: CXXFLAGS += -DPICMOVER_TEST_PATH="$(PWD)/$(BUILD)/test"
$(BUILD)/test/images: $(PWD)/test/images 
	ln -s $< $@

#TODO: Make picmover a shared library
$(BUILD)/test/picmover: $(BUILD)/picmover.o
$(BUILD)/test/picmover: $(TEST:%.cpp=$(BUILD)/test/%.o) | $(BUILD)/test; $(link)
$(BUILD)/test/%.o: test/%.cpp $(INCL:%=$(PREFIX_INC_DIR)/%) | $(BUILD)/test; $(compile)

## Copy headers
$(INCL:%=$(PREFIX_INC_DIR)/%): $(PREFIX_INC_DIR)/%: src/% | $(PREFIX_INC_DIR) ; cp -a $< $@

## Create directories
$(PREFIX_INC_DIR) $(PREFIX)/bin $(BUILD)/test $(BUILD) $(DESTDIR): ; @$(mkdir)

## Docs generation:
define doc_targets =
$$(PREFIX_MAN_DIR)/man$1: ; @$$(mkdir)
$$(PREFIX_MAN_DIR)/man$1/picmover.$1.gz: doc/picmover.$1 | $(PREFIX_MAN_DIR)/man$1
	gzip -c $$< > $$@
endef

$(foreach x,$(DOCS),$(eval $(call doc_targets,$x)))

## Compiling and linking recepies
define compile =
$(CXX) $(CXXFLAGS) $(XCXXFLAGS) -c $< -o $@
endef

define link =
$(CXX) $^ -o $@ $(LDFLAGS) $(XLDFLAGS)
endef

define mkdir =
mkdir -p $@
endef

## Dependencies
-include $(SRCS:%.cpp=$(BUILD)/%.d)
-include $(TEST:%.cpp=$(BUILD)/test/%.d)

