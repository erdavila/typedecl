#ifndef __ARRAYS_HPP__
#define __ARRAYS_HPP__

#include <string>

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
struct impl<const T> {
	inline static std::string value(const std::string& suffix = "") {
		return impl<T>::value(" const" + suffix);
	}
};

template <typename T>
struct impl<T*> {
	inline static std::string value(const std::string& suffix = "") {
		return impl<T>::value("*" + suffix);
	}
};

template <typename T>
struct impl<T&> {
	inline static std::string value() {
		return impl<T>::value("&");
	}
};

template <typename T>
struct impl<T&&> {
	inline static std::string value() {
		return impl<T>::value("&&");
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

} /* namespace __typedecl */
} /* unnamed namespace */


template <typename T>
inline std::string typedecl() {
	return __typedecl::impl<T>::value();
}


#endif
