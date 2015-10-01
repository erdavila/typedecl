#ifndef _TYPENAMES_HPP_
#define _TYPENAMES_HPP_

#include <string>

#ifdef __CYGWIN__
#include <sstream>
namespace std {
	inline string to_string(int val);
	inline string to_string(long val);
	inline string to_string(long long val);
	inline string to_string(unsigned val) { ostringstream os; os << val; return os.str(); }
	inline string to_string(unsigned long val);
	inline string to_string(unsigned long long val);
	inline string to_string(float val);
	inline string to_string(double val);
	inline string to_string(long double val);
}
#endif


template <typename...T> struct _type_name;

// Type list (at least 2 types)
template <typename T1, typename T2, typename...U> struct _type_name<T1, T2, U...> { static std::string value() { return _type_name<T1>::value() + ", " + _type_name<T2, U...>::value(); } };

// Basic types
template <> struct _type_name<void>                   { static std::string value() { return "void"; } };
template <> struct _type_name<bool>                   { static std::string value() { return "bool"; } };
template <> struct _type_name<char>                   { static std::string value() { return "char"; } };
template <> struct _type_name<signed char>            { static std::string value() { return "signed char"; } };
template <> struct _type_name<unsigned char>          { static std::string value() { return "unsigned char"; } };
template <> struct _type_name<wchar_t>                { static std::string value() { return "wchar_t"; } };
template <> struct _type_name<char16_t>               { static std::string value() { return "char16_t"; } };
template <> struct _type_name<char32_t>               { static std::string value() { return "char32_t"; } };
template <> struct _type_name<short int>              { static std::string value() { return "short int"; } };
template <> struct _type_name<unsigned short int>     { static std::string value() { return "unsigned short int"; } };
template <> struct _type_name<int>                    { static std::string value() { return "int"; } };
template <> struct _type_name<unsigned int>           { static std::string value() { return "unsigned int"; } };
template <> struct _type_name<long int>               { static std::string value() { return "long int"; } };
template <> struct _type_name<unsigned long int>      { static std::string value() { return "unsigned long int"; } };
template <> struct _type_name<long long int>          { static std::string value() { return "long long int"; } };
template <> struct _type_name<unsigned long long int> { static std::string value() { return "unsigned long long int"; } };
template <> struct _type_name<float>                  { static std::string value() { return "float"; } };
template <> struct _type_name<double>                 { static std::string value() { return "double"; } };
template <> struct _type_name<long double>            { static std::string value() { return "long double"; } };

// Modifiers
template <typename T> struct _type_name<const          T> { static std::string value() { return _type_name<T>::value() + " const"; } };
template <typename T> struct _type_name<      volatile T> { static std::string value() { return _type_name<T>::value() + " volatile"; } };
template <typename T> struct _type_name<const volatile T> { static std::string value() { return _type_name<T>::value() + " const volatile"; } };
template <typename T> struct _type_name<T*>               { static std::string value() { return _type_name<T>::value() + "*"; } };
template <typename T> struct _type_name<T&>               { static std::string value() { return _type_name<T>::value() + "&"; } };
template <typename T> struct _type_name<T&&>              { static std::string value() { return _type_name<T>::value() + "&&"; } };

// Arrays
template <typename T>           struct _array_details       { using scalar = T                                ; static std::string dimensions() { return {}; } };
template <typename T, size_t N> struct _array_details<T[N]> { using scalar = typename _array_details<T>::scalar; static std::string dimensions() { return "[" + std::to_string(N) + "]" + _array_details<T>::dimensions(); } };
template <typename T, size_t N, const char*const* M>
struct _array_type_name {
	static std::string value() {
		using ad = _array_details<T[N]>;
		return _type_name<typename ad::scalar>::value() + *M + ad::dimensions();
	}
};
static const char* const M1 = "";    template <typename T, size_t N> struct _type_name<T   [N]> : _array_type_name<T, N, &M1> {};
static const char* const M2 = "(&)"; template <typename T, size_t N> struct _type_name<T(&)[N]> : _array_type_name<T, N, &M2> {};
static const char* const M3 = "(*)"; template <typename T, size_t N> struct _type_name<T(*)[N]> : _array_type_name<T, N, &M3> {};

// Functions
template <typename R>                  struct _type_name<R   ()>        { static std::string value() { return _type_name<R>::value() +    "()"; } };
template <typename R, typename...Args> struct _type_name<R   (Args...)> { static std::string value() { return _type_name<R>::value() +    "(" + _type_name<Args...>::value() + ")"; } };
template <typename R>                  struct _type_name<R(&)()>        { static std::string value() { return _type_name<R>::value() + "(&)()"; } };
template <typename R, typename...Args> struct _type_name<R(&)(Args...)> { static std::string value() { return _type_name<R>::value() + "(&)(" + _type_name<Args...>::value() + ")"; } };
template <typename R>                  struct _type_name<R(*)()>        { static std::string value() { return _type_name<R>::value() + "(*)()"; } };
template <typename R, typename...Args> struct _type_name<R(*)(Args...)> { static std::string value() { return _type_name<R>::value() + "(*)(" + _type_name<Args...>::value() + ")"; } };

// Pointer to data member
template <typename T, typename C> struct _type_name<T C::*> { static std::string value() { return _type_name<T>::value() + " " + _type_name<C>::value() + "::*"; } };

// Pointer to methods
template <typename R, typename C>                  struct _type_name<R(C::*)()>                       { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)()"; } };
template <typename R, typename C, typename...Args> struct _type_name<R(C::*)(Args...)>                { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)(" + _type_name<Args...>::value() + ")"; } };
template <typename R, typename C>                  struct _type_name<R(C::*)()        const>          { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)() const"; } };
template <typename R, typename C, typename...Args> struct _type_name<R(C::*)(Args...) const>          { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)(" + _type_name<Args...>::value() + ") const"; } };
template <typename R, typename C>                  struct _type_name<R(C::*)()              volatile> { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)() volatile"; } };
template <typename R, typename C, typename...Args> struct _type_name<R(C::*)(Args...)       volatile> { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)(" + _type_name<Args...>::value() + ") volatile"; } };
template <typename R, typename C>                  struct _type_name<R(C::*)()        const volatile> { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)() const volatile"; } };
template <typename R, typename C, typename...Args> struct _type_name<R(C::*)(Args...) const volatile> { static std::string value() { return _type_name<R>::value() + "(" + _type_name<C>::value() + "::*)(" + _type_name<Args...>::value() + ") const volatile"; } };

// Templates
template <template <typename...> class Template> struct _tmpl_type_name;
template <template <typename...> class Template, typename... Args>
struct _type_name<Template<Args...>> { static std::string value() { return _tmpl_type_name<Template>::value() + "<" + _type_name<Args...>::value() + ">"; } };


#define DEFINE_TYPE_NAME(T)      template <> struct      _type_name<T> { static std::string value() { return #T; } };
#define DEFINE_TMPL_TYPE_NAME(T) template <> struct _tmpl_type_name<T> { static std::string value() { return #T; } };


template <typename T>
std::string type_name(T&&) {
	return _type_name<T>::value();
}

template <typename T>
std::string type_name() {
	return _type_name<T>::value();
}

template <template <typename...> class T>
std::string type_name() {
	return _tmpl_type_name<T>::value();
}


#endif
