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


template <typename...T> struct type_name_impl;

// Type list (at least 2 types)
template <typename T1, typename T2, typename...U> struct type_name_impl<T1, T2, U...> { static std::string value() { return type_name_impl<T1>::value() + ", " + type_name_impl<T2, U...>::value(); } };

// Basic types
template <> struct type_name_impl<void>                   { static std::string value() { return "void"; } };
template <> struct type_name_impl<bool>                   { static std::string value() { return "bool"; } };
template <> struct type_name_impl<char>                   { static std::string value() { return "char"; } };
template <> struct type_name_impl<signed char>            { static std::string value() { return "signed char"; } };
template <> struct type_name_impl<unsigned char>          { static std::string value() { return "unsigned char"; } };
template <> struct type_name_impl<wchar_t>                { static std::string value() { return "wchar_t"; } };
template <> struct type_name_impl<char16_t>               { static std::string value() { return "char16_t"; } };
template <> struct type_name_impl<char32_t>               { static std::string value() { return "char32_t"; } };
template <> struct type_name_impl<short int>              { static std::string value() { return "short int"; } };
template <> struct type_name_impl<unsigned short int>     { static std::string value() { return "unsigned short int"; } };
template <> struct type_name_impl<int>                    { static std::string value() { return "int"; } };
template <> struct type_name_impl<unsigned int>           { static std::string value() { return "unsigned int"; } };
template <> struct type_name_impl<long int>               { static std::string value() { return "long int"; } };
template <> struct type_name_impl<unsigned long int>      { static std::string value() { return "unsigned long int"; } };
template <> struct type_name_impl<long long int>          { static std::string value() { return "long long int"; } };
template <> struct type_name_impl<unsigned long long int> { static std::string value() { return "unsigned long long int"; } };
template <> struct type_name_impl<float>                  { static std::string value() { return "float"; } };
template <> struct type_name_impl<double>                 { static std::string value() { return "double"; } };
template <> struct type_name_impl<long double>            { static std::string value() { return "long double"; } };

// Modifiers
template <typename T> struct type_name_impl<const T> { static std::string value() { return type_name_impl<T>::value() + " const"; } };
template <typename T> struct type_name_impl<T*>      { static std::string value() { return type_name_impl<T>::value() + "*"; } };
template <typename T> struct type_name_impl<T&>      { static std::string value() { return type_name_impl<T>::value() + "&"; } };
template <typename T> struct type_name_impl<T&&>     { static std::string value() { return type_name_impl<T>::value() + "&&"; } };

// Arrays
template <typename T>           struct array_details       { typedef                        T          scalar; static std::string dimensions() { return {}; } };
template <typename T, size_t N> struct array_details<T[N]> { typedef typename array_details<T>::scalar scalar; static std::string dimensions() { return "[" + std::to_string(N) + "]" + array_details<T>::dimensions(); } };
template <typename T, size_t N, const char*const* M>
struct array_type_name {
	static std::string value() {
		typedef array_details<T[N]> ad;
		return type_name_impl<typename array_details<T[N]>::scalar>::value() + *M + ad::dimensions();
	}
};
const char* const M1 = "";    template <typename T, size_t N> struct type_name_impl<T   [N]> : array_type_name<T, N, &M1> {};
const char* const M2 = "(&)"; template <typename T, size_t N> struct type_name_impl<T(&)[N]> : array_type_name<T, N, &M2> {};
const char* const M3 = "(*)"; template <typename T, size_t N> struct type_name_impl<T(*)[N]> : array_type_name<T, N, &M3> {};

// Functions
template <typename R>                  struct type_name_impl<R   ()>        { static std::string value() { return type_name_impl<R>::value() +    "()"; } };
template <typename R, typename...Args> struct type_name_impl<R   (Args...)> { static std::string value() { return type_name_impl<R>::value() +    "(" + type_name_impl<Args...>::value() + ")"; } };
template <typename R>                  struct type_name_impl<R(&)()>        { static std::string value() { return type_name_impl<R>::value() + "(&)()"; } };
template <typename R, typename...Args> struct type_name_impl<R(&)(Args...)> { static std::string value() { return type_name_impl<R>::value() + "(&)(" + type_name_impl<Args...>::value() + ")"; } };
template <typename R>                  struct type_name_impl<R(*)()>        { static std::string value() { return type_name_impl<R>::value() + "(*)()"; } };
template <typename R, typename...Args> struct type_name_impl<R(*)(Args...)> { static std::string value() { return type_name_impl<R>::value() + "(*)(" + type_name_impl<Args...>::value() + ")"; } };

// Pointer to data member
template <typename T, typename C> struct type_name_impl<T C::*> { static std::string value() { return type_name_impl<T>::value() + " " + type_name_impl<C>::value() + "::*"; } };

// Pointer to methods
template <typename R, typename C>                  struct type_name_impl<R(C::*)()>              { static std::string value() { return type_name_impl<R>::value() + "(" + type_name_impl<C>::value() + "::*)()"; } };
template <typename R, typename C, typename...Args> struct type_name_impl<R(C::*)(Args...) >      { static std::string value() { return type_name_impl<R>::value() + "(" + type_name_impl<C>::value() + "::*)(" + type_name_impl<Args...>::value() + ")"; } };
template <typename R, typename C>                  struct type_name_impl<R(C::*)()        const> { static std::string value() { return type_name_impl<R>::value() + "(" + type_name_impl<C>::value() + "::*)() const"; } };
template <typename R, typename C, typename...Args> struct type_name_impl<R(C::*)(Args...) const> { static std::string value() { return type_name_impl<R>::value() + "(" + type_name_impl<C>::value() + "::*)(" + type_name_impl<Args...>::value() + ") const"; } };

// Non-basic/specific types
template <> struct type_name_impl<std::string> { static std::string value() { return "std::string"; } };


template <typename T>
std::string type_name() {
	return type_name_impl<T>::value();
}

template <typename T>
std::string type_name(T&&) {
	return type_name<T>();
}


#endif