#!/usr/bin/env python3
import sys
from itertools import repeat

MAX_LEVELS = 5
MAX_TYPES = 7000


def printerr(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)


'''
	Type¹
	 ├──BasicType
	 └──Operation¹
	     ├──Modifier¹
	     │   ├──CVQualified¹
	     │   │   ├──Const
	     │   │   │   └────────┐
	     │   │   └──Volatile  │
	     │   │       └────────┴──ConstVolatile
	     │   ├──ParenthesizedModifierForArrayAndFunction¹
	     │   │   ├──Pointer
	     │   │   │   └───────────────────╥──PointerActingAsSizedArray
	     │   │   └──Reference¹           ║
	     │   │       ├──LValueReference  ║
	     │   │       └──RValueReference  ║
	     │   ├──Array¹                   ║
	     │   │   ├──UnsizedArray         ║
	     │   │   └───────────────────────╥──SizedArray
	     │   └──ArraySizeInitializer²════╝
	     └──Function¹
	         ├──FunctionRet¹
	         │   ├──Function0Ret
	         │   │   └─────────────╥──FunctionVA0Ret
	         │   ├──Function1Ret   ║
	         │   │   └─────────────╥──FunctionVA1Ret
	         │   └──Function2Ret   ║
	         │       └─────────────╥──FunctionVA2Ret
	         ├──FunctionArg¹       ║
	         │   ├──Function1Arg   ║
	         │   │   └─────────────╥──FunctionVA1Arg
	         │   ├──Function2Arg1  ║
	         │   │   └─────────────╥──FunctionVA2Arg1
	         │   └──Function2Arg2  ║
	         │       └─────────────╥──FunctionVA2Arg2
	         └──FunctionVA²════════╝

	¹: Abstract base class
	²: Mixin
'''


class Type:
	def __init__(self, level):
		self.level = level
		self.alias = 'A%d' % self.level


class BasicType(Type):
	def __init__(self, token):
		super().__init__(level=1)
		self.token = token

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
	def accept_operand(cls, operand):
		pass

	def normalized(self):
		normalized_operand = self.operand.normalized()
		if normalized_operand is self.operand:
			return self
		else:
			return self.__class__(normalized_operand)

	@property
	def array_operations(self):
		return self.operand.array_operations

	def __eq__(self, other):
		return self.__class__ is other.__class__ and \
		       self.operand == other.operand

	def __hash__(self):
		return hash(self.__class__) ^ hash(self.operand)

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.operand)


class Modifier(Operation):
	description_prefix_plural = None

	@classmethod
	def accept_operand(cls, operand):
		if isinstance(operand, Reference):
			# modifier(reference(x))
			raise Generator.OperationDisallowed('Cannot apply modifier to reference')
		super().accept_operand(operand)

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
	def accept_operand(cls, operand):
		if isinstance(operand, CVQualified) and \
			  (cls.qualifications).intersection(operand.collected_qualifications()) != set():
			# cvQualified1(cvQualified2(x))  &&  cvQualified1 and cvQualified2 have qualifications in common
			raise Generator.OperationDisallowed('cv-qualification in common')
		super(CVQualified, cls).accept_operand(operand)

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
	def accept_operand(cls, operand):
		op1 = CVQualified.without_qualifications(operand)
		if isinstance(op1, Pointer):
			op2 = CVQualified.without_qualifications(op1.operand)
			if isinstance(op2, Pointer):
				# Pointer(Pointer(x))
				raise Generator.GenerationPruned('At most 2 levels of pointers')
		super(Pointer, cls).accept_operand(operand)

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
	def accept_operand(cls, operand):
		unqualified_operand = CVQualified.without_qualifications(operand)
		if isinstance(unqualified_operand, Function):
			# array(function(x))
			raise Generator.OperationDisallowed('Cannot make array of functions')

		operand_array_operations = operand.array_operations
		if len(operand_array_operations) > 0:
			if len(operand_array_operations) >= 3:
				raise Generator.GenerationPruned('At most 3 dimensions')
			last_array_operation = operand_array_operations[-1]
			if isinstance(last_array_operation, UnsizedArray):
				# array(UnsizedArray(x))
				raise Generator.OperationDisallowed('Cannot make array of unsized arrays')
		super(Array, cls).accept_operand(operand)

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
	def accept_operand(cls, operand):
		unqualified_operand = CVQualified.without_qualifications(operand)
		if isinstance(unqualified_operand, (Array, Function)):
			# functionRet(array(x))  or  functionRet(function(x))
			raise Generator.OperationDisallowed('Cannot return array or function')

		super(FunctionRet, cls).accept_operand(operand)

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
	def accept_operand(cls, operand):
		if isinstance(operand, Reference):
			reference = operand
			unqualified_reference_operand = CVQualified.without_qualifications(reference.operand)
			if isinstance(unqualified_reference_operand, UnsizedArray):
				# functionArg(reference(UnsizedArray(x)))
				raise Generator.OperationDisallowed('Function parameter cannot be reference to unsized array')

			nonreference_operand = operand.operand
		else:
			nonreference_operand = operand

		unqualified_operand = CVQualified.without_qualifications(nonreference_operand)
		while isinstance(unqualified_operand, Pointer):
			pointer = unqualified_operand
			unqualified_pointer_operand = CVQualified.without_qualifications(pointer.operand)
			if isinstance(unqualified_pointer_operand, UnsizedArray):
				# functionArg(Pointer(UnsizedArray(x)))
				raise Generator.OperationDisallowed('Function parameter cannot be pointer to unsized array')
			unqualified_operand = unqualified_pointer_operand

		super().accept_operand(operand)

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


ALL_OPERATIONS = [
	Const,
	Volatile,
	Pointer,
	LValueReference,
	RValueReference,
	UnsizedArray,
	SizedArray,
	Function0Ret,
	#Function1Ret,
	#Function1Arg,
	Function2Ret,
	#Function2Arg1,
	Function2Arg2,
	FunctionVA0Ret,
	FunctionVA1Ret,
	FunctionVA1Arg,
	#FunctionVA2Ret,
	#FunctionVA2Arg1,
	#FunctionVA2Arg2,
]


class FileWriter:
	def __init__(self, name):
		self.name = name
		self.identation_level = 0

	def __enter__(self):
		self.f = open(self.name, 'wt')
		self.print('#include <cassert>')
		self.print('#include <type_traits>')
		self.print('#include "typedecl.hpp"')
		self.print('')
		self.print('template<typename>void avoid_unused_type_warning(){}')
		self.print('')
		self.print('void testTypeDecl() {')
		self.ident()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.deident()
		self.print('}')
		self.f.close()
		return False

	def print(self, line):
		self.f.write(self._identation() + line + '\n')

	def _identation(self):
		return '\t' * self.identation_level

	def ident(self):
		self.identation_level += 1

	def deident(self):
		self.identation_level -= 1


class Generator:
	class GenerationSkipped(Exception): pass
	class GenerationPruned(GenerationSkipped): pass
	class OperationDisallowed(GenerationSkipped): pass

	total_types = 0
	types_skipped = 0
	normalizations = {}

	def __init__(self, file):
		self.f = file;

	def generate(self, type):
		if Generator.total_types >= MAX_TYPES:
			return
		Generator.total_types += 1
		type_number = Generator.total_types

		normalized = type.normalized()
		declaration = normalized.declaration()
		printerr('%d %r: %s ## %s' % (type_number, type, type.description(), declaration))

		self.f.print('{\t// Type %d' % type_number)
		self.f.ident()
		self.f.print('// Constructed: %r - %s' % (type, type.description()))
		self.f.print('// Normalized:  %r - %s' % (normalized, normalized.description()))

		definition_line = 'using %s = %s;' % (type.alias, type.definition)

		skipped = False
		if normalized in self.normalizations:
			same_types = self.normalizations[normalized]
			same_types.append(type_number)

			self.f.print('// Same normalized form as type %d' % same_types[0])

			skipped = True
			Generator.types_skipped += 1
		else:
			self.normalizations[normalized] = [type_number]

			self.f.print(definition_line)
			self.f.print('assert((std::is_same<%s, %s>::value));' % (type.alias, declaration))
			self.f.print('assert(typedecl<%s>() == "%s");' % (type.alias, declaration))

		if type.level < MAX_LEVELS:
			if skipped:
				self.f.print(definition_line)
				self.f.print('avoid_unused_type_warning<%s>();' % type.alias)
			for operation in ALL_OPERATIONS:
				self.generate_with(operation, operand=type)

		self.f.deident()
		self.f.print('}')

	def generate_with(self, operation, operand):
		try:
			operation.accept_operand(operand)
		except self.GenerationSkipped:
			pass
		else:
			type = operation(operand)
			self.generate(type)


def main():
	#return debug()

	file_name = sys.argv[1]
	with FileWriter(file_name) as f:
		type = BasicType('int')
		generator = Generator(f)
		generator.generate(type)

	printerr()
	printerr('Levels:', MAX_LEVELS)
	printerr('Total types: %d (%d tested + %d skipped)' % (Generator.total_types,
	                                                       Generator.total_types -Generator.types_skipped,
	                                                       Generator.types_skipped))


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
