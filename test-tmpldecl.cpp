#include <cassert>
#include <utility>
#include <vector>
#include "typedecl.hpp"


using MyPair = std::pair<bool, bool>;

DEFINE_TEMPLATE_TYPEDECL(std::pair);
DEFINE_TYPEDECL(MyPair);

DEFINE_TEMPLATE_TYPEDECL(std::vector);
DEFINE_TEMPLATE_TYPEDECL(std::allocator);


void testTmplDecl() {
	assert((typedecl<std::pair<bool, int>>() == "std::pair<bool, int>"));
	assert((typedecl<std::pair<bool, bool>>() == "MyPair"));

	assert((typedecl<const std::pair<bool, int>>() == "const std::pair<bool, int>"));
	assert((typedecl<const std::pair<bool, bool>>() == "const MyPair"));

	assert((namedecl<std::pair<bool, int>>("name") == "std::pair<bool, int> name"));
	assert((namedecl<std::pair<bool, bool>>("name") == "MyPair name"));

	assert((typedecl<std::vector<int>>() == "std::vector<int, std::allocator<int>>"));
}
