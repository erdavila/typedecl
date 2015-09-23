MAIN_TARGET := type-names
_UNAME := $(shell uname -o)

ifeq ($(_UNAME), Cygwin)
  EXT := .exe
else
  EXT := 
endif

EXE := $(MAIN_TARGET)$(EXT)


.PHONY: all
all: $(EXE)

.PHONY: clean
clean:
	rm -f $(EXE)

$(EXE): $(MAIN_TARGET).hpp

$(EXE): $(MAIN_TARGET).cpp
	g++ -Wall -std=c++1y $< -o $@
