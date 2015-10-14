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


struct split_string {
	std::string begin;
	std::string end;
	explicit operator std::string() const {
		return begin + end;
	}
};

inline split_string operator+(const std::string& s, const split_string& ss) {
	return { s + ss.begin, ss.end };
}

inline split_string operator+(const split_string& ss, const std::string& s) {
	return { ss.begin, ss.end + s };
}


template <typename T>
struct impl;


template <typename T>
struct prefix_cv_qual_if_basictype {
	/*
	 * == SFINAE ==
	 * If impl<T> has a static member function named "value_with_cv_qual", then
	 * the forward() overload below is defined, and the call for forward() will
	 * prefer this overload over the other one that has varargs ("...").
	 * If impl<T> does not have such member, then the varargs overload is the
	 * only option.
	 */
	template <typename I>
	inline static split_string forward(const std::string& cv_qual, const split_string& suffix, decltype(I::value_with_cv_qual)*) {
		return I::value_with_cv_qual(cv_qual, suffix);
	}

	template <typename I>
	inline static split_string forward(const std::string& cv_qual, const split_string& suffix, ...) {
		return I::value(cv_qual + suffix);
	}

	inline static split_string value(const std::string& cv_qual, const split_string& suffix) {
		return forward<impl<T>>(cv_qual, suffix, nullptr);
	}
};


template <typename T>
struct impl<const T> {
	inline static split_string value(const split_string& suffix = {}) {
		return prefix_cv_qual_if_basictype<T>::value("const", suffix);
	}
};

template <typename T>
struct impl<volatile T> {
	inline static split_string value(const split_string& suffix = {}) {
		return prefix_cv_qual_if_basictype<T>::value("volatile", suffix);
	}
};

// Required to disambiguate between <const T> and <volatile T>
template <typename T>
struct impl<const volatile T> {
	inline static split_string value(const split_string& suffix = {}) {
		return prefix_cv_qual_if_basictype<T>::value("const volatile", suffix);
	}
};


template <typename T>
struct is_array_or_function : std::integral_constant<
	bool,
	std::is_array<T>::value || std::is_function<T>::value
> {};

template <typename T, bool = is_array_or_function<T>::value>
struct parenthesize_if_array_or_function;

template <typename T>
struct parenthesize_if_array_or_function<T, false> {
	inline static split_string value(const split_string& arg) {
		return impl<T>::value(arg);
	}
};

template <typename T>
struct parenthesize_if_array_or_function<T, true> {
	inline static split_string value(const split_string& arg) {
		return impl<T>::value("(" + arg + ")");
	}
};


template <typename T>
struct impl<T*> {
	inline static split_string value(const split_string& suffix = {}) {
		return parenthesize_if_array_or_function<T>::value("*" + suffix);
	}
};

template <typename T>
struct impl<T&> {
	inline static split_string value(const split_string& suffix = {}) {
		return parenthesize_if_array_or_function<T>::value("&" + suffix);
	}
};

template <typename T>
struct impl<T&&> {
	inline static split_string value(const split_string& suffix = {}) {
		return parenthesize_if_array_or_function<T>::value("&&" + suffix);
	}
};


template <typename T>
struct array_impl {
	inline static split_string value(const split_string& prefix = {}) {
		return impl<T>::value(prefix + "[]");
	}
};

template <typename T>
struct impl<T[]> : array_impl<T> {};

// Required to disambiguate between <const T> and <T[]>
template <typename T>
struct impl<const T[]> : array_impl<const T> {};

// Required to disambiguate between <volatile T> and <T[]>
template <typename T>
struct impl<volatile T[]> : array_impl<volatile T> {};

// Required to disambiguate between <const T>, <volatile T>, <const volatile T>,  <T[]>, <const T[]> and <volatile T[]>
template <typename T>
struct impl<const volatile T[]> : array_impl<const volatile T> {};


template <typename T, size_t N>
struct sized_array_impl {
	inline static split_string value(const split_string& prefix = {}) {
		return impl<T>::value(prefix + ("[" + std::to_string(N) + "]"));
	}
};

template <typename T, size_t N>
struct impl<T[N]> : sized_array_impl<T, N> {};

// Required to disambiguate between <const T> and <T[N]>
template <typename T, size_t N>
struct impl<const T[N]> : sized_array_impl<const T, N> {};

// Required to disambiguate between <volatile T> and <T[N]>
template <typename T, size_t N>
struct impl<volatile T[N]> : sized_array_impl<volatile T, N> {};

// Required to disambiguate between <const T>, <volatile T>, <const volatile T>,  <T[N]>, <const T[N]> and <volatile T[N]>
template <typename T, size_t N>
struct impl<const volatile T[N]> : sized_array_impl<const volatile T, N> {};


template <typename... T>
struct type_list_impl;

template <>
struct type_list_impl<> {
	inline static std::string value() {
		return "";
	}
};

struct varargs;

template <>
struct type_list_impl<varargs> {
	inline static std::string value() {
		return "...";
	}
};

template <typename T>
struct type_list_impl<T> {
	inline static std::string value() {
		return static_cast<std::string>(impl<T>::value());
	}
};

template <typename T1, typename T2, typename... U>
struct type_list_impl<T1, T2, U...> {
	inline static std::string value() {
		return type_list_impl<T1>::value() + ", " + type_list_impl<T2, U...>::value();
	}
};


template <bool RIsPtrOrRef, typename R, typename... A>
struct function_impl;

template <typename R, typename... A>
struct function_impl<false, R, A...> {
	inline static split_string value(const split_string& infix = {}) {
		return static_cast<std::string>(impl<R>::value()) + infix + "(" + type_list_impl<A...>::value() + ")";
	}
};

template <typename R, typename... A>
struct function_impl<true, R, A...> {
	inline static split_string value(const split_string& prefix = {}) {
		return impl<R>::value(prefix + "(" + type_list_impl<A...>::value() + ")");
	}
};

template <typename T>
struct is_pointer_or_reference : std::integral_constant<
	bool,
	std::is_pointer<T>::value || std::is_reference<T>::value
> {};

template <typename R, typename... A>
struct function_args_impl : function_impl<is_pointer_or_reference<typename std::remove_cv<R>::type>::value, R, A...> {};

template <typename R, typename... A>
struct impl<R(A...)>      : function_args_impl<R, A...> {};

template <typename R, typename... A>
struct impl<R(A..., ...)> : function_args_impl<R, A..., varargs> {};


} /* namespace __typedecl */
} /* unnamed namespace */


template <typename T>
inline std::string typedecl() {
	__typedecl::split_string ss = __typedecl::impl<T>::value();
	return ss.begin + ss.end;
}

template <typename T>
inline std::string namedecl(const std::string& name) {
	__typedecl::split_string ss = __typedecl::impl<T>::value();
	return ss.begin + " " + name + ss.end;
}


#define DEFINE_TYPEDECL(T) \
	namespace { \
	namespace __typedecl { \
	template <> \
	struct impl<T> { \
		inline static split_string value(const split_string& suffix = {}) { \
			return #T + suffix; \
		} \
		inline static split_string value_with_cv_qual(const std::string& cv_qual, const split_string& suffix) { \
			return (cv_qual + " " #T) + suffix; \
		} \
	}; \
	} /* namespace __typedecl */ \
	} /* unnamed namespace */


DEFINE_TYPEDECL(void);
DEFINE_TYPEDECL(char);
DEFINE_TYPEDECL(int);


#endif
