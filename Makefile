OBJS = test-typedecl.o test-vardecl.o main.o
MAIN_TARGET = typedecl
MAIN_TARGET_TEST = test-typedecl.cpp
EXE := $(MAIN_TARGET)

MAKEDEPS = g++ -Wall -std=c++1y -MM $< -o $(@:.o=.d) -MT $@ -MP
COMPILE  = g++ -Wall -std=c++1y -c  $< -o $@
LINK     = g++ -Wall $+ -o $@


.PHONY: all
all: $(EXE)

.PHONY: clean
clean:
	rm -f *.o *.d $(EXE)

.PHONY: clean-all
clean-all: clean
	rm -f $(MAIN_TARGET_TEST)


$(EXE): $(OBJS)
	$(LINK)

$(MAIN_TARGET_TEST): $(MAIN_TARGET).py
	./$< > $@  ||  (rm $@  &&  false)

%.o: %.cpp
	$(MAKEDEPS)
	$(COMPILE)


-include $(OBJS:.o=.d)
