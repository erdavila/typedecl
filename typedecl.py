#!/usr/bin/env python3
import sys
from itertools import repeat
from collections import namedtuple

MAX_LEVELS = 5
MAX_TYPES = 1800
MAX_TESTED_TYPES = 1500

SKIP_NULL_CONSTRUCTIONS = True
ONLY_ESSENTIAL_CONSTRUCTIONS_VARIATIONS = True


def printerr(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)


'''
	Type¹
	 ├──BasicType
	 └──Operation¹
	     ├──Modifier¹
	     │   ├──CVQualifier¹
	     │   │   ├──Const
	     │   │   │   └────────┐
	     │   │   └──Volatile  │
	     │   │       └────────┴──ConstVolatile
	     │   ├──ParenthesizedModifierForArrayAndFunction¹
	     │   │   ├──Pointer
	     │   │   │   └───────────────────╥──PointerWithArraySize
	     │   │   └──Reference¹           ║
	     │   │       ├──LValueReference  ║
	     │   │       └──RValueReference  ║
	     │   ├──Array¹                   ║
	     │   │   ├──UnsizedArray         ║
	     │   │   └───────────────────────╥──SizedArray
	     │   ├──ArraySizeInitializer²════╝
	     │   └──PointerToMember
	     ├──Function¹
	     │   ├──FunctionRet¹
	     │   │   ├──Function0Ret
	     │   │   │   └─────────────╥──FunctionVA0Ret
	     │   │   ├──Function1Ret   ║
	     │   │   │   └─────────────╥──FunctionVA1Ret
	     │   │   └──Function2Ret   ║
	     │   │       └─────────────╥──FunctionVA2Ret
	     │   ├──FunctionArg¹       ║
	     │   │   ├──Function1Arg   ║
	     │   │   │   └─────────────╥──FunctionVA1Arg
	     │   │   ├──Function2Arg1  ║
	     │   │   │   └─────────────╥──FunctionVA2Arg1
	     │   │   └──Function2Arg2  ║
	     │   │       └─────────────╥──FunctionVA2Arg2
	     │   └──FunctionVA²════════╝
	     ├──FunctionQualifier¹
	     │   └──FunctionCVQualifier¹
	     │       ├──FunctionConst
	     │       └──FunctionVolatile
	     └──FunctionRefQualifier¹
	         ├──FunctionLValRef
	         └──FunctionRValRef

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
	@classmethod
	def accept_operand(cls, operand):
		if isinstance(operand, Reference):
			# modifier(reference(x))
			raise Generator.OperationDisallowed('Cannot apply %s to reference' % cls.__name__)
		super().accept_operand(operand)

	@property
	def definition(self):
		return self.operand.alias + self.definition_token

	def description(self, plural=False, pluralize_operand_description=False):
		if plural:
			prefix = self.description_prefix_plural
		else:
			prefix = self.description_prefix
		return prefix + ' ' + self.operand.description(plural=pluralize_operand_description)


class CVQualifier(Modifier):
	classes_by_qualifications = {}

	@classmethod
	def accept_operand(cls, operand):
		if isinstance(operand, CVQualifier) and isinstance(operand.operand, CVQualifier):
			raise Generator.GenerationPruned('At most 2 levels of cv-qualifiers')

		if SKIP_NULL_CONSTRUCTIONS and isinstance(operand, (Function, FunctionQualifier)):
			# <cv-qualified>(function(x))
			raise Generator.GenerationPruned('cv-qualifier applied to function is ignored')

		super().accept_operand(operand)

	@property
	def definition(self):
		return self.definition_token + ' ' + self.operand.alias

	def description(self, plural=False):
		# Forwards pluralization to the operand
		return self.description_prefix + ' ' + self.operand.description(plural=plural)

	def declaration(self, suffix=''):
		if isinstance(self.operand, BasicType):
			prefix = self.definition_token + ' '
			return self.operand.declaration(suffix, prefix=prefix)
		else:
			return self.operand.declaration(self.definition_token + suffix)

	def normalized(self):
		if isinstance(self.operand, CVQualifier):
			# <cv-qualifier1>(<cv-qualifier2>(x)) -> <cv-qualifier1 + cv-qualifier2>(x)
			qualifications = (self.qualifications).union(self.operand.qualifications)
			cls = self.classes_by_qualifications[qualifications]
			return cls(self.operand.operand).normalized()

		if isinstance(self.operand, Array):
			# <cv-qualifier>(array(x)) -> array(<cv-qualifier>(x))
			array = self.operand
			cv_class = self.__class__
			qualified_array_operand = cv_class(array.operand)
			array_class = array.__class__
			new_array = array_class(qualified_array_operand)
			return new_array.normalized()

		if isinstance(self.operand, (Function, FunctionQualifier)):
			# <cv-qualifier>(function(x)) -> function(x)
			return self.operand.normalized()

		return super().normalized()

	Analysis = namedtuple('Analysis', ['original', 'qualifications', 'without_qualifications'])

	@classmethod
	def analyze(cls, operand):
		op = operand
		quals = set()
		while isinstance(op, CVQualifier):
			quals.update(op.qualifications)
			op = op.operand
		quals = frozenset(quals)
		return cls.Analysis(operand, quals, op)


class Const(CVQualifier):
	definition_token = 'const'
	description_prefix = 'const'
	qualifications = frozenset(['const'])
CVQualifier.classes_by_qualifications[Const.qualifications] = Const


class Volatile(CVQualifier):
	definition_token = 'volatile'
	description_prefix = 'volatile'
	qualifications = frozenset(['volatile'])
CVQualifier.classes_by_qualifications[Volatile.qualifications] = Volatile


class ConstVolatile(Const, Volatile):
	definition_token = 'const volatile'
	description_prefix = 'const volatile'
	qualifications = frozenset(['const', 'volatile'])
CVQualifier.classes_by_qualifications[ConstVolatile.qualifications] = ConstVolatile


class ParenthesizedModifierForArrayAndFunction(Modifier):
	def declaration(self, suffix=''):
		argument = self.definition_token + suffix
		if isinstance(self.operand, (Array, Function)):
			argument = '(' + argument + ')'
		return self.operand.declaration(argument)


class Pointer(ParenthesizedModifierForArrayAndFunction):
	definition_token = '*'
	description_prefix = 'pointer to'
	description_prefix_plural = 'pointers to'

	@classmethod
	def accept_operand(cls, operand):
		unqualified_operand = CVQualifier.analyze(operand).without_qualifications
		if isinstance(unqualified_operand, Pointer):
			unqualified_operand_operand = CVQualifier.analyze(unqualified_operand.operand).without_qualifications
			if isinstance(unqualified_operand_operand, Pointer):
				# Pointer(Pointer(x))
				raise Generator.GenerationPruned('At most 2 levels of pointers')

		if isinstance(unqualified_operand, FunctionQualifier):
			raise Generator.OperationDisallowed('Cannot point to qualified function')

		super().accept_operand(operand)


class ArraySizeInitializer(Modifier):
	def __init__(self, operand):
		super().__init__(operand)
		operand_array_operations = operand.array_operations
		if len(operand_array_operations) == 0:
			self.size = 5
		else:
			last_array_operation = operand_array_operations[-1]
			self.size = last_array_operation.size - 1


class PointerWithArraySize(Pointer, ArraySizeInitializer):
	@property
	def array_operations(self):
		return self.operand.array_operations + [self]


class Reference(ParenthesizedModifierForArrayAndFunction):
	@classmethod
	def accept_operand(cls, operand):
		unqualified_operand = CVQualifier.analyze(operand).without_qualifications
		if isinstance(unqualified_operand, FunctionQualifier):
			raise Generator.OperationDisallowed('Cannot reference qualified function')
		super().accept_operand(operand)


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
		unqualified_operand = CVQualifier.analyze(operand).without_qualifications
		if isinstance(unqualified_operand, (Function, FunctionQualifier)):
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
		super().accept_operand(operand)

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

	def description(self, plural=False, qualifiers=''):
		assert plural is False
		(return_description, arguments_descriptions) = self._return_and_arguments(self.operand.description())
		return 'function%s with arguments (%s) returning %s' % (qualifiers, arguments_descriptions, return_description)

	def declaration(self, infix='', qualifiers=''):
		return self._signature(self.operand.declaration(), infix=infix) + qualifiers

	def _signature(self, operand_value, infix=''):
		result, args_list = self._return_and_arguments(operand_value)
		return '%s%s(%s)' % (result, infix, args_list)

	@classmethod
	def _raw_args_list(cls):
		return list(repeat('char', cls.num_args))


class FunctionRet(Function):
	@classmethod
	def accept_operand(cls, operand):
		unqualified_operand = CVQualifier.analyze(operand).without_qualifications
		if isinstance(unqualified_operand, (Array, Function, FunctionQualifier)):
			# functionRet(array(x))  or  functionRet(function(x))
			raise Generator.OperationDisallowed('Cannot return array or function')

		super().accept_operand(operand)

	def declaration(self, prefix='', qualifiers=''):
		unqualified_operand = CVQualifier.analyze(self.operand).without_qualifications
		if isinstance(unqualified_operand, (Pointer, PointerToMember, Reference)):
			_, arguments = self._return_and_arguments(None)
			return self.operand.declaration(prefix + '(' + arguments + ')' + qualifiers)

		return super().declaration(prefix) + qualifiers

	def _return_and_arguments(self, result):
		args_list = ', '.join(self._raw_args_list())
		return (result, args_list)


class FunctionArg(Function):
	@classmethod
	def accept_operand(cls, operand):
		if isinstance(operand, Reference):
			reference = operand
			unqualified_reference_operand = CVQualifier.analyze(reference.operand).without_qualifications
			if isinstance(unqualified_reference_operand, UnsizedArray):
				# functionArg(reference(UnsizedArray(x)))
				raise Generator.OperationDisallowed('Function parameter cannot be reference to unsized array')

			nonreference_operand = operand.operand
		else:
			nonreference_operand = operand

		unqualified_operand = CVQualifier.analyze(nonreference_operand).without_qualifications
		while isinstance(unqualified_operand, Pointer):
			pointer = unqualified_operand
			unqualified_pointer_operand = CVQualifier.analyze(pointer.operand).without_qualifications
			if isinstance(unqualified_pointer_operand, UnsizedArray):
				# functionArg(Pointer(UnsizedArray(x)))
				# functionArg(reference(Pointer(UnsizedArray(x))))
				raise Generator.OperationDisallowed('Function parameter cannot be [reference to] pointer to unsized array')
			unqualified_operand = unqualified_pointer_operand

		if isinstance(unqualified_operand, FunctionQualifier):
			raise Generator.OperationDisallowed('Function parameter cannot be qualified function')

		if SKIP_NULL_CONSTRUCTIONS and isinstance(operand, CVQualifier) \
				and not isinstance(unqualified_operand, Array):
			# functionArg(<cv-qualified>(x)) -> functionArg(x)
			raise Generator.GenerationPruned('Argument cv-qualifier is ignored')

		super().accept_operand(operand)

	def normalized(self):
		operand_analysis = CVQualifier.analyze(self.operand)
		if operand_analysis.qualifications:
			assert isinstance(self.operand, CVQualifier)
			unqualified_operand = operand_analysis.without_qualifications
			function_class = self.__class__
			if isinstance(unqualified_operand, Array):
				# functionArg(<cv-qualifier>(array(x))) -> functionArg(PointerWithArraySize(<cv-qualifier>(x)))
				cv_class = CVQualifier.classes_by_qualifications[operand_analysis.qualifications]
				array_operand = unqualified_operand.operand
				qualified_array_operand = cv_class(array_operand)
				pointer = PointerWithArraySize(qualified_array_operand)
				return function_class(pointer).normalized()
			else:
				# functionArg(<cv-qualifier>(x)) -> functionArg(x)
				return function_class(unqualified_operand.normalized()).normalized()

		if isinstance(self.operand, Array):
			# functionArg(array(x)) -> functionArg(PointerWithArraySize(x))
			array = self.operand
			new_operand = PointerWithArraySize(array.operand)
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


class FunctionQualifier(Operation):
	def description(self, plural=False, qualifiers=''):
		assert plural is False
		quals = ' ' + self.definition_token + qualifiers
		return self.operand.description(qualifiers=quals)

	@property
	def definition(self):
		return self.operand.definition + ' ' + self.definition_token

	def declaration(self, arg='', qualifiers=''):
		qual = ' ' + self.definition_token + qualifiers
		return self.operand.declaration(arg, qualifiers=qual)


class FunctionCVQualifier(FunctionQualifier):
	pass


class FunctionConst(FunctionCVQualifier):
	definition_token = 'const'

	@classmethod
	def accept_operand(cls, operand):
		if not isinstance(operand, Function):
			raise Generator.OperationDisallowed('Function const-qualifier can only be applied to a function')
		super().accept_operand(operand)


class FunctionVolatile(FunctionCVQualifier):
	definition_token = 'volatile'

	@classmethod
	def accept_operand(cls, operand):
		if not isinstance(operand, (Function, FunctionConst)):
			raise Generator.OperationDisallowed('Function volatile-qualifier can only be applied to a [const-qualified] function')
		super().accept_operand(operand)


class FunctionRefQualifier(FunctionQualifier):
	@classmethod
	def accept_operand(cls, operand):
		if not isinstance(operand, (Function, FunctionCVQualifier)):
			raise Generator.OperationDisallowed('Function ref-qualifier can only be applied to a [cv-qualified] function')
		super().accept_operand(operand)


class FunctionLValRef(FunctionRefQualifier):
	definition_token = '&'


class FunctionRValRef(FunctionRefQualifier):
	definition_token = '&&'


class PointerToMember(Modifier):
	definition_token = ' C::*'
	description_prefix = 'pointer to member'
	description_prefix_plural = 'pointers to member'

	@classmethod
	def accept_operand(cls, operand):
		if SKIP_NULL_CONSTRUCTIONS and isinstance(operand, FunctionRefQualifier):
			# PointerToMember(functionRefQualifier(x))
			raise Generator.GenerationPruned('ref-qualification of a pointed-to member function is ignored')
		super().accept_operand(operand)

	def normalized(self):
		unqualified_operand = CVQualifier.analyze(self.operand).without_qualifications
		if isinstance(unqualified_operand, FunctionRefQualifier):
			# PointerToMember(functionRefQualifier(x)) -> PointerToMember(x)
			return PointerToMember(unqualified_operand.operand).normalized()
		return super().normalized()

	def declaration(self, suffix=''):
		arg = 'C::*' + suffix
		if isinstance(self.operand, (Array, Function, FunctionCVQualifier)):
			arg = '(' + arg + ')'
		else:
			arg = ' ' + arg
		return self.operand.declaration(arg)


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
	FunctionConst,
	FunctionVolatile,
	FunctionLValRef,
	FunctionRValRef,
	PointerToMember,
]

if ONLY_ESSENTIAL_CONSTRUCTIONS_VARIATIONS:
	def remove_non_essential_operations(operations):
		operations_to_remove = set([
			Volatile,  # Const and Volatile have the same relationship with other operations and with one another
			RValueReference,  # LValueReference and RValueReference have the same relationship with other operations and with one another
			FunctionVolatile,  # FunctionConst and FunctionVolatile have the same relationship with other operations and with one another
			FunctionRValRef,  # FunctionLValRef and FunctionRValRef have the same relationship with other operations and with one another
		])

		functions_ret = set()
		functions_arg = set()
		for op in operations:
			if issubclass(op, FunctionRet):
				functions_ret.add(op)
			elif issubclass(op, FunctionArg):
				functions_arg.add(op)

		def func_key(func):
			# Prefer vararg version
			# Prefer more arguments
			return (issubclass(func, FunctionVA), func.num_args)

		for group in (functions_ret, functions_arg):
			to_keep = max(group, key=func_key, default=None)
			group.discard(to_keep)
			operations_to_remove |= group

		operations[:] = filter(lambda op: op not in operations_to_remove, operations)

	remove_non_essential_operations(ALL_OPERATIONS)
	del remove_non_essential_operations


class FileWriter:
	def __init__(self, name):
		self.name = name
		self.identation_level = 0

	def __enter__(self):
		self.f = open(self.name, 'wt')
		self.print('#include "typedecl.hpp"')
		self.print('#include <cassert>')
		self.print('#include <type_traits>')
		self.print('')
		self.print('template<typename>void avoid_unused_type_warning(){}')
		self.print('')
		self.print('struct C {};')
		self.print('DEFINE_TYPEDECL(C);')
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
	same_cases = 0
	normalizations = {}

	@classmethod
	def tested_types(cls):
		return cls.total_types - cls.same_cases

	def __init__(self, file):
		self.f = file

	def generate(self, type):
		if Generator.total_types >= MAX_TYPES or \
		   Generator.tested_types() >= MAX_TESTED_TYPES:
			return
		Generator.total_types += 1
		type_number = Generator.total_types

		normalized = type.normalized()

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
			Generator.same_cases += 1
		else:
			self.normalizations[normalized] = [type_number]
			declaration = normalized.declaration()

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
	printerr('Total types: %d (%d tested + %d same cases)' % (Generator.total_types,
	                                                          Generator.tested_types(),
	                                                          Generator.same_cases))


def debug():
	type = FunctionConst(Function2Ret(Const(BasicType('int'))))
	printerr(type.description())
	printerr(type)
	normalized = type.normalized()
	printerr(normalized)
	printerr(type is normalized)
	printerr(normalized.declaration())
	printerr('const int(char, char) const', '# Expected')
	sys.exit(1)


if __name__ == '__main__':
	main()
