#ifndef __ARRAYS_HPP__
#define __ARRAYS_HPP__

#include <string>
#include <type_traits>
#include "../static-strings/static-strings.hpp"


namespace {
namespace __typedecl {


template <typename T, template <typename> class C1, template <typename> class C2>
struct or_conds
	: std::integral_constant<bool, C1<T>::value || C2<T>::value>
{};


using empty_ss = static_string::static_string<char>;
using space_ss = static_string::static_string<char, ' '>;
using open_parens_ss = static_string::static_string<char, '('>;
using close_parens_ss = static_string::static_string<char, ')'>;


template <typename... T> using ssconcat         = static_string::concat<empty_ss, T...>;
template <typename P>    using ss_from_provider = static_string::from_provider<P>;
template <char... chars> using static_string    = static_string::static_string<char, chars...>;


template <typename BeginSS, typename EndSS>
struct split_static_string {
	using begin = BeginSS;
	using end = EndSS;
};

using empty_sss = split_static_string<empty_ss, empty_ss>;


template <typename, typename...>
struct sssconcat_impl;

// split_static_string
template <typename BeginSS, typename EndSS>
struct sssconcat_impl<split_static_string<BeginSS, EndSS>> {
	using type = split_static_string<BeginSS, EndSS>;
};

// static_string + split_static_string + ...
template <char... chars, typename BeginSS, typename EndSS, typename... TT>
struct sssconcat_impl<
			static_string<chars...>,
			split_static_string<BeginSS, EndSS>,
			TT...
	>
{
	using _begin_ss = ssconcat<
	                   static_string<chars...>,
	                   BeginSS
	               >;
	using _left_sss = split_static_string<_begin_ss, EndSS>;
	using type = typename sssconcat_impl<_left_sss, TT...>::type;
};

// split_static_string + static_string + ...
template <typename BeginSS, typename EndSS, char... chars, typename... TT>
struct sssconcat_impl<
			split_static_string<BeginSS, EndSS>,
			static_string<chars...>,
			TT...
	>
{
	using _end_ss = ssconcat<
	                   EndSS,
	                   static_string<chars...>
	               >;
	using _left_sss = split_static_string<BeginSS, _end_ss>;
	using type = typename sssconcat_impl<_left_sss, TT...>::type;
};

// static_string + static_string + ? + ...
template <char... chars1, char... chars2, typename T, typename... TT>
struct sssconcat_impl<
			static_string<chars1...>,
			static_string<chars2...>,
			T, TT...
	>
{
	using _left_ss = ssconcat<
			static_string<chars1...>,
			static_string<chars2...>
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

template <typename T, typename CVQualSS, bool = is_basic_type<T>::value>
struct cvqualified_impl;

template <typename T, typename CVQualSS>
struct cvqualified_impl<T, CVQualSS, true> {
	template <typename SuffixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring_with_cv_qual<CVQualSS, SuffixSSS>;
};

template <typename T, typename CVQualSS>
struct cvqualified_impl<T, CVQualSS, false> {
	template <typename SuffixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring<sssconcat<CVQualSS, SuffixSSS>>;
};

using const_ss = static_string<'c','o','n','s','t'>;

template <typename T>
struct impl<const T> : cvqualified_impl<T, const_ss> {};

using volatile_ss = static_string<'v','o','l','a','t','i','l','e'>;

template <typename T>
struct impl<volatile T> : cvqualified_impl<T, volatile_ss> {};

// Required to disambiguate between <const T> and <volatile T>
template <typename T>
struct impl<const volatile T>
	: cvqualified_impl<T, ssconcat<const_ss, space_ss, volatile_ss>>
{};


template <typename T>
struct is_array_or_function : or_conds<T, std::is_array, std::is_function>
{};

template <typename T, typename TokenSS, bool = is_array_or_function<T>::value>
struct address_access_impl;

template <typename T, typename TokenSS>
struct address_access_impl<T, TokenSS, true> {
	template <typename SuffixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring<
			sssconcat<
				open_parens_ss,
				TokenSS,
				SuffixSSS,
				close_parens_ss
			>
	>;
};

template <typename T, typename TokenSS>
struct address_access_impl<T, TokenSS, false> {
	template <typename SuffixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring<
			sssconcat<
				TokenSS, SuffixSSS
			>
	>;
};

template <typename T>
struct impl<T*>
	: address_access_impl<T, static_string<'*'>>
{};

using lvalref_ss = static_string<'&'>;

template <typename T>
struct impl<T&>
	: address_access_impl<T, lvalref_ss>
{};

using rvalref_ss = static_string<'&','&'>;

template <typename T>
struct impl<T&&>
	: address_access_impl<T, rvalref_ss>
{};


template <typename T>
struct array_impl {
	template <typename PrefixSSS = empty_sss>
	using ssstring = typename impl<T>::template ssstring<sssconcat<PrefixSSS, static_string<'[',']'>>>;
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
	using sstring = static_string<'0' + N>;
};

template <size_t N>
struct size_to_sstring<N, false> {
	using sstring = ssconcat<
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
				static_string<'['>,
				typename size_to_sstring<N>::sstring,
				static_string<']'>
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
	using sstring = static_string<'.','.','.'>;
};

template <typename T>
struct type_list_impl<T> {
	using _t_sss = typename impl<T>::template ssstring<>;
	using sstring = ssconcat<typename _t_sss::begin, typename _t_sss::end>;
};

template <typename T1, typename T2, typename... U>
struct type_list_impl<T1, T2, U...> {
	using sstring = ssconcat<
				typename type_list_impl<T1>::sstring,
				static_string<',',' '>,
				typename type_list_impl<T2, U...>::sstring
			>;
};


template <typename T>
struct is_pointer_or_reference : or_conds<T, std::is_pointer, std::is_reference>
{};

template <typename T>
struct result_is_pointer_or_reference;

template <typename R, typename... A>
struct result_is_pointer_or_reference<R(A...)>
	: is_pointer_or_reference<typename std::remove_cv<R>::type>
{};

template <typename F, typename QualsSS, bool = result_is_pointer_or_reference<F>::value>
struct function_impl;

template <typename R, typename... A, typename QualsSS>
struct function_impl<R(A...), QualsSS, false> {
	using _r_sss = typename impl<R>::template ssstring<>;

	template <typename InfixSSS = empty_sss>
	using ssstring = sssconcat<
				typename _r_sss::begin,
				typename _r_sss::end,
				InfixSSS,
				open_parens_ss,
				typename type_list_impl<A...>::sstring,
				close_parens_ss,
				QualsSS
			>;
};

template <typename R, typename... A, typename QualsSS>
struct function_impl<R(A...), QualsSS, true> {
	template <typename PrefixSSS = empty_sss>
	using ssstring = typename impl<R>::template ssstring<
				sssconcat<
					PrefixSSS,
					open_parens_ss,
					typename type_list_impl<A...>::sstring,
					close_parens_ss,
					QualsSS
				>
			>;
};

#define __TYPEDECL_FUNCTION_IMPL(TOKENS, SSs...) \
	template <typename R, typename... A> struct impl<R(A...)      TOKENS> : function_impl<R(A...)         , ssconcat<SSs>> {}; \
	template <typename R, typename... A> struct impl<R(A..., ...) TOKENS> : function_impl<R(A..., varargs), ssconcat<SSs>> {}

#define __TYPEDECL_FUNCTION_CONSTNESS_IMPL(TOKENS, SSs...) \
	__TYPEDECL_FUNCTION_IMPL(      TOKENS,                     ##SSs); \
	__TYPEDECL_FUNCTION_IMPL(const TOKENS, space_ss, const_ss, ##SSs)

#define __TYPEDECL_FUNCTION_CONST_VOLATILENESS_IMPL(TOKENS, SSs...) \
	__TYPEDECL_FUNCTION_CONSTNESS_IMPL(         TOKENS,                        ##SSs); \
	__TYPEDECL_FUNCTION_CONSTNESS_IMPL(volatile TOKENS, space_ss, volatile_ss, ##SSs)

#define __TYPEDECL_FUNCTION_CONST_VOLATILE_REFNESS_IMPL() \
	__TYPEDECL_FUNCTION_CONST_VOLATILENESS_IMPL(); \
	__TYPEDECL_FUNCTION_CONST_VOLATILENESS_IMPL(&,  space_ss, lvalref_ss); \
	__TYPEDECL_FUNCTION_CONST_VOLATILENESS_IMPL(&&, space_ss, rvalref_ss)


__TYPEDECL_FUNCTION_CONST_VOLATILE_REFNESS_IMPL();


#undef __TYPEDECL_FUNCTION_CONST_VOLATILE_REFNESS_IMPL
#undef __TYPEDECL_FUNCTION_CONST_VOLATILENESS_IMPL
#undef __TYPEDECL_FUNCTION_CONSTNESS_IMPL
#undef __TYPEDECL_FUNCTION_IMPL


template <typename T>
struct str_provider;

template <typename T>
struct basic_type_impl {
	using _token_ss = ss_from_provider<str_provider<T>>;

	template <typename SuffixSSS = empty_sss>
	using ssstring = sssconcat<_token_ss, SuffixSSS>;

	template <typename CVQualSS, typename SuffixSSS>
	using ssstring_with_cv_qual = sssconcat<
			ssconcat<CVQualSS, space_ss, _token_ss>,
			SuffixSSS
		>;
};


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
	template <> struct str_provider<T> { static constexpr const char* str() { return #T; } }; \
	template <> struct impl<T> : basic_type_impl<T> {}; \
	} /* namespace __typedecl */ \
	} /* unnamed namespace */


DEFINE_TYPEDECL(void);
DEFINE_TYPEDECL(char);
DEFINE_TYPEDECL(int);


#endif
