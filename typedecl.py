#!/usr/bin/env python3
import sys
from itertools import repeat

MAX_LEVELS = 5
MAX_TYPES = 7000
MAX_GUESSED_DECLARATIONS = 7000
MAX_TYPEDECLS = 7000


def printerr(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)


'''
	Type
	 ├──BasicType
	 └──Operation
	     ├──Modifier
	     │   ├──CVQualified
	     │   │   ├──Const
	     │   │   │   └────────┐
	     │   │   └──Volatile  │
	     │   │       └────────┴──ConstVolatile
	     │   ├──ParenthesizedModifierForArrayAndFunction
	     │   │   ├──Pointer
	     │   │   │   └───────────────────╥──PointerActingAsSizedArray
	     │   │   └──Reference            ║
	     │   │       ├──LValueReference  ║
	     │   │       └──RValueReference  ║
	     │   ├──Array                    ║
	     │   │   ├──UnsizedArray         ║
	     │   │   └───────────────────────╥──SizedArray
	     │   └──ArraySizeInitializer═════╝
	     └──Function
	         ├──FunctionRet
	         │   ├──Function0Ret
	         │   │   └─────────────╥──FunctionVA0Ret
	         │   ├──Function1Ret   ║
	         │   │   └─────────────╥──FunctionVA1Ret
	         │   └──Function2Ret   ║
	         │       └─────────────╥──FunctionVA2Ret
	         ├──FunctionArg        ║
	         │   ├──Function1Arg   ║
	         │   │   └─────────────╥──FunctionVA1Arg
	         │   ├──Function2Arg1  ║
	         │   │   └─────────────╥──FunctionVA2Arg1
	         │   └──Function2Arg2  ║
	         │       └─────────────╥──FunctionVA2Arg2
	         └──FunctionVA═════════╝
'''


total_types = 0
guessed_declarations = 0
typedecls = 0


class Type:
	def __init__(self, level):
		self.level = level
		self.alias = 'A%d' % self.level

	@classmethod
	def generate(cls, type):
		global total_types
		if total_types >= MAX_TYPES:
			return

		indent = cls._indentation(type.level)
		indent_more = cls._indentation(type.level+1)

		printerr('%r: %s ##' % (type, type.description()), end=' ')

		global guessed_declarations
		if guessed_declarations < MAX_GUESSED_DECLARATIONS:
			declaration = type.normalized().declaration()
			commented_declaration_assertion = ''
			guessed_declarations += 1
		else:
			declaration = '?'
			commented_declaration_assertion = '//'

		global typedecls
		if typedecls < MAX_TYPEDECLS and declaration != '?':
			commented_typedecl_assertion = ''
			typedecls += 1
		else:
			commented_typedecl_assertion = '//'


		printerr(declaration)
		total_types += 1

		print(indent + '{')
		print(indent_more + '// %d: %r' % (total_types, type))
		print(indent_more + 'using %s = %s; // %s' % (type.alias, type.definition, type.description()))
		print(indent_more + commented_declaration_assertion + 'assert((std::is_same<%s, %s>::value));' % (type.alias, declaration))
		print(indent_more + commented_typedecl_assertion + 'assert(typedecl<%s>() == "%s");' % (type.alias, declaration))

		if type.level < MAX_LEVELS:
			Const.generate_with_operand(type)
			Volatile.generate_with_operand(type)
			Pointer.generate_with_operand(type)
			LValueReference.generate_with_operand(type)
			RValueReference.generate_with_operand(type)
			UnsizedArray.generate_with_operand(type)
			SizedArray.generate_with_operand(type)
			Function0Ret.generate_with_operand(type)
			#Function1Ret.generate_with_operand(type)
			#Function1Arg.generate_with_operand(type)
			Function2Ret.generate_with_operand(type)
			#Function2Arg1.generate_with_operand(type)
			Function2Arg2.generate_with_operand(type)
			FunctionVA0Ret.generate_with_operand(type)
			FunctionVA1Ret.generate_with_operand(type)
			FunctionVA1Arg.generate_with_operand(type)
			#FunctionVA2Ret.generate_with_operand(type)
			#FunctionVA2Arg1.generate_with_operand(type)
			#FunctionVA2Arg2.generate_with_operand(type)

		print(indent + '}')

	@staticmethod
	def _indentation(level):
		return '\t' * level


class BasicType(Type):
	def __init__(self, token):
		super().__init__(level=1)
		self.token = token

	@classmethod
	def generate(cls, token):
		type = BasicType(token)
		super(BasicType, cls).generate(type)

	@property
	def definition(self):
		return self.token

	def description(self, plural=False):
		descr = self.token
		if plural:
			descr += 's'
		return descr

	def declaration(self, suffix='', prefix=''):
		return prefix + self.token + suffix

	@property
	def array_operations(self):
		return []

	def normalized(self):
		return self

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.token)


class Operation(Type):
	def __init__(self, operand):
		super().__init__(level=operand.level+1)
		self.operand = operand

	@classmethod
	def generate_with_operand(cls, operand):
		type = cls(operand)
		cls.generate(type)

	def normalized(self):
		normalized_operand = self.operand.normalized()
		if normalized_operand is self.operand:
			return self
		else:
			return self.__class__(normalized_operand)

	@property
	def array_operations(self):
		return self.operand.array_operations

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.operand)


class Modifier(Operation):
	description_prefix_plural = None

	@classmethod
	def generate_with_operand(cls, operand):
		if isinstance(operand, Reference):
			# modifier(reference(x))
			return
		super().generate_with_operand(operand)

	@property
	def definition(self):
		return self.operand.alias + self.definition_token

	def description(self, plural=False, pluralize_operand_description=False):
		if plural:
			prefix = self.description_prefix_plural
		else:
			prefix = self.description_prefix
		return prefix + ' ' + self.operand.description(plural=pluralize_operand_description);


class CVQualified(Modifier):
	classes_by_qualifications = {}

	@classmethod
	def generate_with_operand(cls, operand):
		if isinstance(operand, CVQualified) and \
			  (cls.qualifications).intersection(operand.collected_qualifications()) != set():
			return
		super(CVQualified, cls).generate_with_operand(operand)

	@property
	def definition(self):
		return self.definition_token + ' ' + self.operand.alias

	def description(self, plural=False):
		# Forwards pluralization to the operand
		return self.description_prefix + ' ' + self.operand.description(plural=plural);

	def declaration(self, suffix=''):
		if isinstance(self.operand, BasicType):
			prefix = self.definition_token + ' '
			return self.operand.declaration(suffix, prefix=prefix)
		else:
			return self.operand.declaration(self.definition_token + suffix)

	def normalized(self):
		if isinstance(self.operand, CVQualified):
			# <cv-qualified1>(<cv-qualified2>(x)) -> <cv-qualified1 + cv-qualified2>(x)
			qualifications = (self.qualifications).union(self.operand.qualifications)
			cls = self.classes_by_qualifications[qualifications]
			return cls(self.operand.operand).normalized()

		if isinstance(self.operand, Array):
			# <cv-qualified>(array(x)) -> array(<cv-qualified>(x))
			array = self.operand
			cv_class = self.__class__
			new_array_operand = cv_class(array.operand)
			array_class = array.__class__
			new_array = array_class(new_array_operand)
			return new_array.normalized()

		if isinstance(self.operand, Function):
			# <cv-qualified>(function(x)) -> function(x)
			return self.operand.normalized()

		return super().normalized()

	def collected_qualifications(self):
		op = self
		quals = set()
		while isinstance(op, CVQualified):
			quals.update(op.qualifications)
			op = op.operand
		return frozenset(quals)

	@staticmethod
	def without_qualifications(operand):
		while isinstance(operand, CVQualified):
			operand = operand.operand
		return operand


class Const(CVQualified):
	definition_token = 'const'
	description_prefix = 'const'
	qualifications = frozenset(['const'])
CVQualified.classes_by_qualifications[Const.qualifications] = Const


class Volatile(CVQualified):
	definition_token = 'volatile'
	description_prefix = 'volatile'
	qualifications = frozenset(['volatile'])
CVQualified.classes_by_qualifications[Volatile.qualifications] = Volatile


class ConstVolatile(Const, Volatile):
	definition_token = 'const volatile'
	description_prefix = 'const volatile'
	qualifications = frozenset(['const', 'volatile'])
CVQualified.classes_by_qualifications[ConstVolatile.qualifications] = ConstVolatile


class ParenthesizedModifierForArrayAndFunction(Modifier):
	def declaration(self, argument):
		if isinstance(self.operand, (Array, Function)):
			argument = '(' + argument + ')'
		return self.operand.declaration(argument)


class Pointer(ParenthesizedModifierForArrayAndFunction):
	definition_token = '*'
	description_prefix = 'pointer to'
	description_prefix_plural = 'pointers to'

	@classmethod
	def generate_with_operand(cls, operand):
		op1 = CVQualified.without_qualifications(operand)
		if isinstance(op1, Pointer):
			op2 = CVQualified.without_qualifications(op1.operand)
			if isinstance(op2, Pointer):
				return
		super(Pointer, cls).generate_with_operand(operand)

	def declaration(self, suffix=''):
		return super().declaration(self.definition_token + suffix)


class ArraySizeInitializer(Modifier):
	def __init__(self, operand):
		super().__init__(operand)
		operand_array_operations = operand.array_operations
		if len(operand_array_operations) == 0:
			self.size = 5
		else:
			last_array_operation = operand_array_operations[-1]
			self.size = last_array_operation.size - 1


class PointerActingAsSizedArray(Pointer, ArraySizeInitializer):
	@property
	def array_operations(self):
		return self.operand.array_operations + [self]


class Reference(ParenthesizedModifierForArrayAndFunction):
	def declaration(self, suffix=''):
		return super().declaration(self.definition_token + suffix)


class LValueReference(Reference):
	definition_token = '&'
	description_prefix = 'l-value reference to'


class RValueReference(Reference):
	definition_token = '&&'
	description_prefix = 'r-value reference to'


class Array(Modifier):
	description_prefix = 'array of'
	description_prefix_plural = 'arrays of'

	@classmethod
	def generate_with_operand(cls, operand):
		unqualified_operand = CVQualified.without_qualifications(operand)
		if isinstance(unqualified_operand, Function):
			return

		operand_array_operations = operand.array_operations
		if len(operand_array_operations) > 0:
			if len(operand_array_operations) >= 3:
				return
			last_array_operation = operand_array_operations[-1]
			if isinstance(last_array_operation, UnsizedArray):
				return
		super(Array, cls).generate_with_operand(operand)

	def description(self, plural=False):
		return super().description(plural=plural, pluralize_operand_description=True)

	def declaration(self, prefix=''):
		return self.operand.declaration(prefix + self.definition_token)

	@property
	def array_operations(self):
		return self.operand.array_operations + [self]


class UnsizedArray(Array):
	definition_token = '[]'


class SizedArray(Array, ArraySizeInitializer):
	@property
	def definition_token(self):
		return '[%d]' % self.size

	@property
	def description_prefix(self):
		return super().description_prefix + ' %d' % self.size

	@property
	def description_prefix_plural(self):
		return super().description_prefix_plural + ' %d' % self.size


class Function(Operation):
	@property
	def definition(self):
		return self._signature(self.operand.alias)

	def description(self, plural=False):
		assert plural is False
		(return_description, arguments_descriptions) = self._return_and_arguments(self.operand.description())
		return 'function with arguments (%s) returning %s' % (arguments_descriptions, return_description)

	def declaration(self, infix=''):
		return self._signature(self.operand.declaration(), infix=infix)

	def _signature(self, operand_value, infix=''):
		result, args_list = self._return_and_arguments(operand_value)
		return '%s%s(%s)' % (result, infix, args_list)

	@classmethod
	def _raw_args_list(cls):
		return list(repeat('char', cls.num_args))


class FunctionRet(Function):
	@classmethod
	def generate_with_operand(cls, operand):
		unqualified_operand = CVQualified.without_qualifications(operand)
		if isinstance(unqualified_operand, (Array, Function)):
			return

		super(FunctionRet, cls).generate_with_operand(operand)

	def declaration(self, prefix=''):
		unqualified_operand = CVQualified.without_qualifications(self.operand)
		if isinstance(unqualified_operand, (Pointer, Reference)):
			_, arguments = self._return_and_arguments(None)
			return self.operand.declaration(prefix + '(' + arguments + ')')

		return super().declaration(prefix)

	def _return_and_arguments(self, result):
		args_list = ', '.join(self._raw_args_list())
		return (result, args_list)


class FunctionArg(Function):
	@classmethod
	def generate_with_operand(cls, operand):
		if isinstance(operand, Reference):
			reference = operand
			unqualified_reference_operand = CVQualified.without_qualifications(reference.operand)
			if isinstance(unqualified_reference_operand, UnsizedArray):
				# functionArg(reference(<cv-qualified>(UnsizedArray(x))))
				return

			nonreference_operand = operand.operand
		else:
			nonreference_operand = operand

		unqualified_operand = CVQualified.without_qualifications(nonreference_operand)
		while isinstance(unqualified_operand, Pointer):
			pointer = unqualified_operand
			unqualified_pointer_operand = CVQualified.without_qualifications(pointer.operand)
			if isinstance(unqualified_pointer_operand, UnsizedArray):
				# functionArg(cv-Pointer+(cv-UnsizedArray(x)))
				return
			unqualified_operand = unqualified_pointer_operand

		return super().generate_with_operand(operand)

	def normalized(self):
		unqualified_operand = CVQualified.without_qualifications(self.operand)

		if unqualified_operand is not self.operand:
			assert isinstance(self.operand, CVQualified)
			function_class = self.__class__
			if isinstance(unqualified_operand, Array):
				# functionArg(<cv-qualified>(array(x))) -> functionArg(Pointer(<cv-qualified>(x)))
				cv_quals = self.operand.collected_qualifications()
				cv_class = CVQualified.classes_by_qualifications[cv_quals]
				array_operand = unqualified_operand.operand
				pointer = PointerActingAsSizedArray(cv_class(array_operand))
				return function_class(pointer).normalized()
			else:
				# functionArg(<cv-qualified>(x)) -> functionArg(x)
				return function_class(unqualified_operand.normalized()).normalized()

		if isinstance(self.operand, Array):
			# functionArg(array(x)) -> functionArg(Pointer(x))
			array = self.operand
			new_operand = PointerActingAsSizedArray(array.operand)
			function_class = self.__class__
			return function_class(new_operand).normalized()

		if isinstance(self.operand, Function):
			# functionArg(function(x)) -> functionArg(Pointer(function(x)))
			function = self.operand
			pointer = Pointer(function)
			function_class = self.__class__
			return function_class(pointer).normalized()

		return super().normalized()

	def _return_and_arguments(self, operand_value):
		args = self._raw_args_list()
		args[self.operand_arg_index] = operand_value
		args_list = ', '.join(args)

		return ('char', args_list)


class Function0Ret(FunctionRet):
	num_args = 0


class Function1Ret(FunctionRet):
	num_args = 1


class Function1Arg(FunctionArg):
	num_args = 1
	operand_arg_index = 0


class Function2Ret(FunctionRet):
	num_args = 2


class Function2Arg1(FunctionArg):
	num_args = 2
	operand_arg_index = 0


class Function2Arg2(FunctionArg):
	num_args = 2
	operand_arg_index = 1


class FunctionVA(Function):
	@classmethod
	def _raw_args_list(cls):
		return super()._raw_args_list() + ['...']


class FunctionVA0Ret(Function0Ret, FunctionVA):
	pass


class FunctionVA1Ret(Function1Ret, FunctionVA):
	pass


class FunctionVA1Arg(Function1Arg, FunctionVA):
	pass


class FunctionVA2Ret(Function2Ret, FunctionVA):
	pass


class FunctionVA2Arg1(Function2Arg1, FunctionVA):
	pass


class FunctionVA2Arg2(Function2Arg2, FunctionVA):
	pass



def main():
	#return debug()
	print('#include <cassert>')
	print('#include <type_traits>')
	print('#include "typedecl.hpp"')
	print('')
	print('void testTypeDecl() {')
	BasicType.generate('int')
	print('}')

	printerr()
	printerr('Levels:', MAX_LEVELS)
	printerr('Total types:', total_types)
	printerr('Guessed declarations:', guessed_declarations)
	printerr('Typedecls:', typedecls)

def debug():
	type = Function0Ret(LValueReference(UnsizedArray(BasicType('int'))))
	printerr(type.description())
	printerr(type)
	normalized = type.normalized()
	printerr(normalized)
	printerr(type is normalized)
	printerr(normalized.declaration())
	printerr('int(&())[]', '# Expected')
	sys.exit(1)


if __name__ == '__main__':
	main()
