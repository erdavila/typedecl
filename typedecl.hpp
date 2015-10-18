#ifndef __ARRAYS_HPP__
#define __ARRAYS_HPP__

#include <string>
#include <type_traits>
#include "../static-strings/static-strings.hpp"


namespace {
namespace __typedecl {


using empty_ss = static_string::static_string<char>;
using space_ss = static_string::static_string<char, ' '>;
using open_parens_ss = static_string::static_string<char, '('>;
using close_parens_ss = static_string::static_string<char, ')'>;

template <typename B, typename E>
struct sss {
	using begin = B;
	using end = E;
};

using empty_sss = sss<empty_ss, empty_ss>;

template <typename, typename...>
struct sssconcat_impl;

// sss
template <typename BeginSS, typename EndSS>
struct sssconcat_impl<sss<BeginSS, EndSS>> {
	using type = sss<BeginSS, EndSS>;
};

// ss + sss + ...
template <char... chars, typename BeginSS, typename EndSS, typename... TT>
struct sssconcat_impl<
			static_string::static_string<char, chars...>,
			sss<BeginSS, EndSS>,
			TT...
	>
{
	using _begin_ss = static_string::concat<
	                   static_string::static_string<char, chars...>,
	                   BeginSS
	               >;
	using _left_sss = sss<_begin_ss, EndSS>;
	using type = typename sssconcat_impl<_left_sss, TT...>::type;
};

// sss + ss + ...
template <typename BeginSS, typename EndSS, char... chars, typename... TT>
struct sssconcat_impl<
			sss<BeginSS, EndSS>,
			static_string::static_string<char, chars...>,
			TT...
	>
{
	using _end_ss = static_string::concat<
	                   EndSS,
	                   static_string::static_string<char, chars...>
	               >;
	using _left_sss = sss<BeginSS, _end_ss>;
	using type = typename sssconcat_impl<_left_sss, TT...>::type;
};

// ss + ss + ? + ...
template <char... chars1, char... chars2, typename T, typename... TT>
struct sssconcat_impl<
			static_string::static_string<char, chars1...>,
			static_string::static_string<char, chars2...>,
			T, TT...
	>
{
	using _left_ss = static_string::concat<
			static_string::static_string<char, chars1...>,
			static_string::static_string<char, chars2...>
		>;
	using type = typename sssconcat_impl<_left_ss, T, TT...>::type;
};

template <typename T1, typename T2, typename... TT>
using sssconcat = typename sssconcat_impl<T1, T2, TT...>::type;


template <typename T>
struct impl;


template <typename T>
struct is_basic_type {
	/*
	 * == SFINAE ==
	 * If impl<T> has a template member alias named "ssstring_with_cv_qual", then
	 * the test() overload below is defined, and the call with argument nullptr
	 * will prefer this overload over the other one that has varargs ("...").
	 * If impl<T> does not have such template member, then the varargs overload
	 * is the only option.
	 */
	template <typename I>
	static constexpr bool test(typename I::template ssstring_with_cv_qual<empty_ss, empty_sss> *) {
		return true;
	}

	template <typename I>
	static constexpr bool test(...) {
		return false;
	}

	enum { value = test<impl<T>>(nullptr) };
};

template <typename T, typename SuffixSSS, typename CVQualSS, bool = is_basic_type<T>::value>
struct prefix_cv_qual_if_basictype;

template <typename T, typename SuffixSSS, typename CVQualSS>
struct prefix_cv_qual_if_basictype<T, SuffixSSS, CVQualSS, true> {
	using ssstring = typename impl<T>::template ssstring_with_cv_qual<CVQualSS, SuffixSSS>;
};

template <typename T, typename SuffixSSS, typename CVQualSS>
struct prefix_cv_qual_if_basictype<T, SuffixSSS, CVQualSS, false> {
	using ssstring = typename impl<T>::template ssstring<sssconcat<CVQualSS, SuffixSSS>>;
};

template <typename T, typename CVQualSS>
struct cvqualified_impl {
	template <typename SuffixSSS = empty_sss>
	using ssstring = typename prefix_cv_qual_if_basictype<T, SuffixSSS, CVQualSS>::ssstring;
};

using const_ss = static_string::static_string<char, 'c','o','n','s','t'>;

template <typename T>
struct impl<const T> : cvqualified_impl<T, const_ss> {};

using volatile_ss = static_string::static_string<char, 'v','o','l','a','t','i','l','e'>;

template <typename T>
struct impl<volatile T> : cvqualified_impl<T, volatile_ss> {};

// Required to disambiguate between <const T> and <volatile T>
template <typename T>
struct impl<const volatile T>
	: cvqualified_impl<T, static_string::concat<const_ss, space_ss, volatile_ss>>
{};


template <typename T>
struct is_array_or_function : std::integral_constant<
	bool,
	std::is_array<T>::value || std::is_function<T>::value
> {};

template <typename T, bool = is_array_or_function<T>::value>
struct parenthesize_if_array_or_function;

template <typename T>
struct parenthesize_if_array_or_function<T, true> {
	template <typename ArgSSS>
	using ssstring = typename impl<T>::template ssstring<
			sssconcat<
				open_parens_ss,
				ArgSSS,
				close_parens_ss
			>
	>;
};

template <typename T>
struct parenthesize_if_array_or_function<T, false> {
	template <typename ArgSSS>
	using ssstring = typename impl<T>::template ssstring<ArgSSS>;
};

template <typename T, typename TokenSS>
struct address_access_impl {
	template <typename SuffixSSS = empty_sss>
	using ssstring = typename parenthesize_if_array_or_function<T>::template ssstring<sssconcat<TokenSS, SuffixSSS>>;
};

template <typename T>
struct impl<T*>
	: address_access_impl<T, static_string::static_string<char, '*'>>
{};

template <typename T>
struct impl<T&>
	: address_access_impl<T, static_string::static_string<char, '&'>>
{};

template <typename T>
struct impl<T&&>
	: address_access_impl<T, static_string::static_string<char, '&','&'>>
{};


template <typename T>
struct array_impl {
	template <typename PrefixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring<sssconcat<PrefixSSS, static_string::static_string<char, '[',']'>>>;
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


template <size_t N, bool = (N < 10)>
struct size_to_sstring;

template <size_t N>
struct size_to_sstring<N, true> {
	using sstring = static_string::static_string<char, '0' + N>;
};

template <size_t N>
struct size_to_sstring<N, false> {
	using sstring = static_string::concat<
			typename size_to_sstring<N / 10>::sstring,
			typename size_to_sstring<N % 10>::sstring
	>;
};

template <typename T, size_t N>
struct sized_array_impl {
	template <typename PrefixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring<
			sssconcat<
				PrefixSSS,
				static_string::static_string<char, '['>,
				typename size_to_sstring<N>::sstring,
				static_string::static_string<char, ']'>
			>
	>;
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
	using sstring = empty_ss;
};

struct varargs;

template <>
struct type_list_impl<varargs> {
	using sstring = static_string::static_string<char, '.','.','.'>;
};

template <typename T>
struct type_list_impl<T> {
	using _t_sss = typename impl<T>::template ssstring<>;
	using sstring = static_string::concat<typename _t_sss::begin, typename _t_sss::end>;
};

template <typename T1, typename T2, typename... U>
struct type_list_impl<T1, T2, U...> {
	using sstring = static_string::concat<
				typename type_list_impl<T1>::sstring,
				static_string::static_string<char, ',',' '>,
				typename type_list_impl<T2, U...>::sstring
			>;
};


template <typename F, bool RIsPtrOrRef>
struct function_impl;

template <typename R, typename... A>
struct function_impl<R(A...), false> {
	using _r_sss = typename impl<R>::template ssstring<>;

	template <typename InfixSSS = empty_sss>
	using ssstring = sssconcat<
				typename _r_sss::begin,
				typename _r_sss::end,
				InfixSSS,
				open_parens_ss,
				typename type_list_impl<A...>::sstring,
				close_parens_ss
			>;
};

template <typename R, typename... A>
struct function_impl<R(A...), true> {
	template <typename PrefixSSS = empty_sss>
	using ssstring = typename impl<R>::template ssstring<
				sssconcat<
					PrefixSSS,
					open_parens_ss,
					typename type_list_impl<A...>::sstring,
					close_parens_ss
				>
			>;
};

template <typename T>
struct is_pointer_or_reference : std::integral_constant<
	bool,
	std::is_pointer<T>::value || std::is_reference<T>::value
> {};

template <typename F>
struct function_args_impl;

template <typename R, typename... A>
struct function_args_impl<R(A...)>
	: function_impl<
			R(A...),
			is_pointer_or_reference<typename std::remove_cv<R>::type>::value
		>
{};

template <typename R, typename... A>
struct impl<R(A...)>      : function_args_impl<R(A...)> {};

template <typename R, typename... A>
struct impl<R(A..., ...)> : function_args_impl<R(A..., varargs)> {};


template <typename T>
struct str_provider;


} /* namespace __typedecl */
} /* unnamed namespace */


template <typename T>
inline std::string typedecl() {
	using i_sss = typename __typedecl::impl<T>::template ssstring<>;
	return i_sss::begin::string() + i_sss::end::string();
}

template <typename T>
inline std::string namedecl(const std::string& name) {
	using i_sss = typename __typedecl::impl<T>::template ssstring<>;
	return i_sss::begin::string() + ' ' + name + i_sss::end::string();
}


#define DEFINE_TYPEDECL(T) \
	namespace { \
	namespace __typedecl { \
	template <> \
	struct str_provider<T> { \
		static constexpr const char* str() { return #T; } \
	}; \
	template <> \
	struct impl<T> { \
		using _token_ss = static_string::from_provider<str_provider<T>>; \
		template <typename SuffixSSS = empty_sss> using ssstring = sssconcat<_token_ss, SuffixSSS>; \
		template <typename CVQualSS, typename SuffixSSS> \
		using ssstring_with_cv_qual = sssconcat< \
		                                  static_string::concat<CVQualSS, space_ss, _token_ss>, \
		                                  SuffixSSS \
		                              >; \
	}; \
	} /* namespace __typedecl */ \
	} /* unnamed namespace */


DEFINE_TYPEDECL(void);
DEFINE_TYPEDECL(char);
DEFINE_TYPEDECL(int);


#endif
