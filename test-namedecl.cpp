#include <cassert>
#include "typedecl.hpp"

void testNameDecl() {
	assert(namedecl<int>("name") == "int name");
	assert(namedecl<int&>("name") == "int& name");
	assert(namedecl<const int>("name") == "const int name");
	assert(namedecl<int[3]>("name") == "int name[3]");
	assert(namedecl<int(*)[3][4]>("name") == "int(* name)[3][4]");
	assert(namedecl<int**volatile(*)[]>("name") == "int**volatile(* name)[]");
	assert(namedecl<int(*(&&)[4])[5]>("name") == "int(*(&& name)[4])[5]");
	assert(namedecl<int(char)>("name") == "int name(char)");
	assert(namedecl<void(*)()>("name") == "void(* name)()");
	assert(namedecl<int(&&)(int)>("name") == "int(&& name)(int)");
	assert(namedecl<int(char, ...)>("name") == "int name(char, ...)");
	assert(namedecl<void(*)(...)>("name") == "void(* name)(...)");
	assert(namedecl<int&(&&)(int, ...)>("name") == "int&(&& name)(int, ...)");
}
