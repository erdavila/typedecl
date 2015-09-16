#include "type-names.hpp"
#include <iostream>
#include <string>
#include <typeinfo>
using namespace std;

#define SHOW(X) cout << typeid(X).name() << '\t' << type_name(X) << '\t' << #X << endl;

int f(char, double) { return {}; }
float g() { return {}; }


// Custom types
struct Struct {
	int dataMember;
	void method(unsigned int, signed char) {}
	long constMethod(long double, unsigned char, signed short) const { return {}; }
};

template <typename, typename>
struct Template {};

// Specializations for custom types
template <> struct          type_name_impl<Struct>   { static std::string value() { return "Struct"; } };
template <> struct template_type_name_impl<Template> { static std::string value() { return "Template"; } };


int main() {
	SHOW('a');
	SHOW(u'a');
	SHOW(U'a');
	SHOW(L'a');

	SHOW("abc");
	SHOW(u8"abc");
	SHOW(u"abc");
	SHOW(U"abc");
	SHOW(L"abc");
	
	bool b = false;
	SHOW(true);
	SHOW(b);
	SHOW(0 < 1);
	
	int x = 7;
	SHOW(x);
	SHOW(&x);
	
	SHOW(0);
	SHOW(0L);
	SHOW(0LL);
	SHOW(0.0);
	SHOW(0.0f);
	SHOW(0.0d);
	SHOW(0.0L);

	int* pointer = nullptr;
	const int* pointerToConst = nullptr;
	int* const constPointer = nullptr;
	const int* const constPointerToConst = nullptr;
	SHOW(pointer);
	SHOW(pointerToConst);
	SHOW(constPointer);
	SHOW(constPointerToConst);
	SHOW(*pointer);
	SHOW(*pointerToConst);
	SHOW(*constPointer);
	SHOW(*constPointerToConst);
	
	int   array[3][4][5];
	SHOW(&array);
	SHOW( array);
	SHOW(&array[0]);
	SHOW( array[0]);
	SHOW(&array[0][1]);
	SHOW( array[0][1]);
	SHOW(&array[0][1][2]);
	SHOW( array[0][1][2]);
	
	SHOW(f);
	SHOW(&f);

	SHOW(g);
	SHOW(&g);
	
	SHOW(&Struct::dataMember);
	SHOW(&Struct::method);
	SHOW(&Struct::constMethod);

	Template<int, bool> templ;
	SHOW(templ);
}
