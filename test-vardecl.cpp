#include <cassert>
#include "typedecl.hpp"

void testVarDecl() {
	assert(vardecl<int>("var") == "int var");
	assert(vardecl<int&>("var") == "int& var");
	assert(vardecl<const int>("var") == "const int var");
	assert(vardecl<int[3]>("var") == "int var[3]");
	assert(vardecl<int(*)[3][4]>("var") == "int(* var)[3][4]");
	assert(vardecl<int**volatile(*)[]>("var") == "int**volatile(* var)[]");
	assert(vardecl<int(*(&&)[4])[5]>("var") == "int(*(&& var)[4])[5]");
	assert(vardecl<int(char)>("var") == "int var(char)");
	assert(vardecl<void(*)()>("var") == "void(* var)()");
	assert(vardecl<int(&&)(int)>("var") == "int(&& var)(int)");
	assert(vardecl<int(char, ...)>("var") == "int var(char, ...)");
	assert(vardecl<void(*)(...)>("var") == "void(* var)(...)");
	assert(vardecl<int&(&&)(int, ...)>("var") == "int&(&& var)(int, ...)");
}
