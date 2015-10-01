#ifndef __ARRAYS_HPP__
#define __ARRAYS_HPP__

#include <string>
#include <type_traits>

#ifdef __CYGWIN__
#include <sstream>
namespace std {
	inline std::string to_string(unsigned long val) { ostringstream os; os << val; return os.str(); }
}
#endif


namespace {
namespace __typedecl {


template <typename T>
struct impl;

template <>
struct impl<int> {
	inline static std::string value(const std::string& suffix = "") {
		return "int" + suffix;
	}
};


template <typename T>
struct const_impl {
	inline static std::string value(const std::string& suffix = "") {
		return impl<T>::value(" const" + suffix);
	}
};

template <typename T>
struct impl<const T> : const_impl<T> {};

template <typename T>
struct volatile_impl {
	inline static std::string value(const std::string& suffix = "") {
		return impl<T>::value(" volatile" + suffix);
	}
};

template <typename T>
struct impl<volatile T> : volatile_impl<T> {};

// Required to disambiguate between <const T> and <volatile T>
template <typename T>
struct impl<const volatile T> : const_impl<volatile T> {};


template <typename T, bool = std::is_array<T>::value>
struct parenthesize_if_array;

template <typename T>
struct parenthesize_if_array<T, false> {
	inline static std::string value(const std::string& arg) {
		return impl<T>::value(arg);
	}
};

template <typename T>
struct parenthesize_if_array<T, true> {
	inline static std::string value(const std::string& arg) {
		return impl<T>::value("(" + arg + ")");
	}
};


template <typename T>
struct impl<T*> {
	inline static std::string value(const std::string& suffix = "") {
		return parenthesize_if_array<T>::value("*" + suffix);
	}
};

template <typename T>
struct impl<T&> {
	inline static std::string value() {
		return parenthesize_if_array<T>::value("&");
	}
};

template <typename T>
struct impl<T&&> {
	inline static std::string value() {
		return parenthesize_if_array<T>::value("&&");
	}
};


template <typename T>
struct impl<T[]> {
	inline static std::string value(const std::string& prefix = "") {
		return impl<T>::value(prefix + "[]");
	}
};

template <typename T, size_t N>
struct impl<T[N]> {
	inline static std::string value(const std::string& prefix = "") {
		return impl<T>::value(prefix + "[" + std::to_string(N) + "]");
	}
};


// Required to disambiguate between <const T> and <T[]>
template <typename T>
struct impl<const T[]> : const_impl<T[]> {};

// Required to disambiguate between <const T> and <T[N]>
template <typename T, size_t N>
struct impl<const T[N]> : const_impl<T[N]> {};

// Required to disambiguate between <volatile T> and <T[]>
template <typename T>
struct impl<volatile T[]> : volatile_impl<T[]> {};

// Required to disambiguate between <volatile T> and <T[N]>
template <typename T, size_t N>
struct impl<volatile T[N]> : volatile_impl<T[N]> {};

// Required to disambiguate between <const T>, <volatile T>, <const volatile T>,  <T[]>, <const T[]> and <volatile T[]>
template <typename T>
struct impl<const volatile T[]> : const_impl<volatile T[]> {};

// Required to disambiguate between <const T>, <volatile T>, <const volatile T>,  <T[N]>, <const T[N]> and <volatile T[N]>
template <typename T, size_t N>
struct impl<const volatile T[N]> : const_impl<volatile T[N]> {};


} /* namespace __typedecl */
} /* unnamed namespace */


template <typename T>
inline std::string typedecl() {
	return __typedecl::impl<T>::value();
}


#endif
