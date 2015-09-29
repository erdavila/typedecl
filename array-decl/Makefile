MAIN_TARGET := array_decl
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

.PHONY: clean-all
clean-all: clean
	rm -f $(MAIN_TARGET).cpp 

$(MAIN_TARGET).cpp: $(MAIN_TARGET).py
	./$< > $@

$(EXE): $(MAIN_TARGET).hpp

$(EXE): $(MAIN_TARGET).cpp
	g++ -Wall -std=c++1y $< -o $@
