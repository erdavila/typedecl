#include <iostream>
#include <string>
#include <typeinfo>
#include "type-names.hpp"

DEFINE_TMPL_TYPE_NAME(std::basic_string);
DEFINE_TMPL_TYPE_NAME(std::allocator);
DEFINE_TMPL_TYPE_NAME(std::char_traits);

#define SHOW(X)   std::cout << typeid(X).name() << '\t' << type_name(X)   << '\t' << #X << std::endl;
#define SHOWT(X)  std::cout << typeid(X).name() << '\t' << type_name<X>() << '\t' << #X << std::endl;
#define SHOWT2(X) std::cout <<                     '\t' << type_name<X>() << '\t' << #X << std::endl;

int f(char, double) { return {}; }
float g() { return {}; }


// Custom types
struct Struct {
	int dataMember;
	void method(unsigned int, signed char) {}
	long constMethod(long double, unsigned char, signed short) const { return {}; }
	long volatileMethod(wchar_t) volatile { return {}; }
	long constVolatileMethod(char16_t, char32_t) const volatile { return {}; }
};

template <typename, typename>
struct Template {};

// Specializations for custom types
DEFINE_TYPE_NAME(Struct);
DEFINE_TMPL_TYPE_NAME(Template);


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
	
	int i = 7;
	SHOW(i);
	SHOW(&i);

	const int ci = 7;
	SHOW(ci);
	SHOW(&ci);

	volatile int vi = 7;
	SHOW(vi);
	SHOW(&vi);

	const int volatile cvi = 7;
	SHOW(cvi);
	SHOW(&cvi);

	SHOW(0);
	SHOW(0L);
	SHOW(0LL);
	SHOW(0.0);
	SHOW(0.0f);
	SHOW(0.0d);
	SHOW(0.0L);

	      int*       pointer             = nullptr;
	const int*       pointerToConst      = nullptr;
	      int* const constPointer        = nullptr;
	const int* const constPointerToConst = nullptr;
	SHOW(pointer);
	SHOW(pointerToConst);
	SHOW(constPointer);
	SHOW(constPointerToConst);
	SHOW(*pointer);
	SHOW(*pointerToConst);
	SHOW(*constPointer);
	SHOW(*constPointerToConst);
	
	const int* volatile volatilePointerToConst = nullptr;
	volatile int* const constPointerToVolatile = nullptr;
	SHOW(volatilePointerToConst);
	SHOW(constPointerToVolatile);
	SHOW(*volatilePointerToConst);
	SHOW(*constPointerToVolatile);

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
	SHOW(&Struct::volatileMethod);
	SHOW(&Struct::constVolatileMethod);

	using Tmpl = Template<int, bool>;
	Tmpl tmpl;
	SHOW(tmpl);
	SHOWT(Tmpl);
	SHOWT2(Template);

	SHOWT(std::string);
	SHOWT2(std::basic_string);
}
