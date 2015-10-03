#!/usr/bin/env python3
import sys

MAX_LEVELS = 7
MAX_GUESSED_DECLARATIONS = 7200
MAX_TYPEDECLS = 7200


def printerr(*args, **kwargs):
	print(*args, file=sys.stderr, **kwargs)


total_types = 0
guessed_declarations = 0
typedecls = 0


class Type:
	def __init__(self, level):
		self.level = level
		self.alias = 'A%d' % self.level

	@classmethod
	def generate(cls, type):
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

		print(indent + '{')
		print(indent_more + '// %r' % type)
		print(indent_more + 'using %s = %s; // %s' % (type.alias, type.definition, type.description()))
		print(indent_more + commented_declaration_assertion + 'assert((std::is_same<%s, %s>::value));' % (type.alias, declaration))
		print(indent_more + commented_typedecl_assertion + 'assert(typedecl<%s>() == "%s");' % (type.alias, declaration))

		global total_types
		total_types += 1

		if type.level < MAX_LEVELS:
			Const.generate_with_operand(type)
			Volatile.generate_with_operand(type)
			Pointer.generate_with_operand(type)
			LValueReference.generate_with_operand(type)
			RValueReference.generate_with_operand(type)
			UnsizedArray.generate_with_operand(type)
			SizedArray.generate_with_operand(type)

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

	def declaration(self, suffix=''):
		return self.token + suffix

	@property
	def array_operations(self):
		return []

	def normalized(self):
		return self

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.token)


class Operation(Type):
	pluralize_operand_description = False
	description_prefix_plural = None

	def __init__(self, operand):
		super().__init__(level=operand.level+1)
		self.operand = operand

	@classmethod
	def generate_with_operand(cls, operand):
		if isinstance(operand, Reference):
			return
		type = cls(operand)
		cls.generate(type)

	@property
	def definition(self):
		return self.operand.alias + self.definition_token

	def description(self, plural=False):
		pluralize_operand_description = self.pluralize_operand_description

		if plural:
			if self.description_prefix_plural is None:
				prefix = self.description_prefix
				pluralize_operand_description = True
			else:
				prefix = self.description_prefix_plural
		else:
			prefix = self.description_prefix

		return prefix + ' '  + self.operand.description(pluralize_operand_description);

	@property
	def array_operations(self):
		return self.operand.array_operations

	def normalized(self):
		normalized_operand = self.operand.normalized()
		if normalized_operand is self.operand:
			return self
		else:
			return self.__class__(normalized_operand)

	def __repr__(self):
		return '%s(%r)' % (self.__class__.__name__, self.operand)


class CVQualified(Operation):
	classes_by_qualifications = {}

	@classmethod
	def generate_with_operand(cls, operand):
		if isinstance(operand, CVQualified) and \
			  (cls.qualifications).intersection(operand.collected_qualifications()) != set():
			return
		super(CVQualified, cls).generate_with_operand(operand)

	def declaration(self, suffix=''):
		return self.operand.declaration(self.definition_token + suffix)

	def normalized(self):
		if isinstance(self.operand, CVQualified):
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

		return super().normalized()

	def collected_qualifications(self):
		op = self
		quals = set()
		while isinstance(op, CVQualified):
			quals.update(op.qualifications)
			op = op.operand
		return quals

	@staticmethod
	def without_qualifications(operand):
		while isinstance(operand, CVQualified):
			operand = operand.operand
		return operand


class Const(CVQualified):
	definition_token = ' const'
	description_prefix = 'const'
	qualifications = frozenset(['const'])
CVQualified.classes_by_qualifications[Const.qualifications] = Const


class Volatile(CVQualified):
	definition_token = ' volatile'
	description_prefix = 'volatile'
	qualifications = frozenset(['volatile'])
CVQualified.classes_by_qualifications[Volatile.qualifications] = Volatile


class ConstVolatile(Const, Volatile):
	definition_token = ' volatile const'
	description_prefix = 'volatile const'
	qualifications = frozenset(['const', 'volatile'])
CVQualified.classes_by_qualifications[ConstVolatile.qualifications] = ConstVolatile


class ParenthesizedOperationForArray(Operation):
	def declaration(self, argument):
		if isinstance(self.operand, Array):
			argument = '(' + argument + ')'
		return self.operand.declaration(argument)


class Pointer(ParenthesizedOperationForArray):
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


class Reference(ParenthesizedOperationForArray):
	def declaration(self):
		return super().declaration(self.definition_token)


class LValueReference(Reference):
	definition_token = '&'
	description_prefix = 'lvalue reference to'


class RValueReference(Reference):
	definition_token = '&&'
	description_prefix = 'rvalue reference to'


class Array(Operation):
	definition_token = '[]'
	description_prefix = 'array of'
	description_prefix_plural = 'arrays of'
	pluralize_operand_description = True

	@classmethod
	def generate_with_operand(cls, operand):
		operand_array_operations = operand.array_operations
		if len(operand_array_operations) > 0:
			if len(operand_array_operations) >= 3:
				return
			last_array_operation = operand_array_operations[-1]
			if isinstance(last_array_operation, UnsizedArray):
				return
		super(Array, cls).generate_with_operand(operand)

	def declaration(self, prefix=''):
		return self.operand.declaration(prefix + self.definition_token)

	@property
	def array_operations(self):
		return self.operand.array_operations + [self]


class UnsizedArray(Array):
	pass


class SizedArray(Array):
	def __init__(self, operand):
		super().__init__(operand)
		operand_array_operations = operand.array_operations
		if len(operand_array_operations) == 0:
			self.size = 5
		else:
			last_array_operation = operand_array_operations[-1]
			self.size = last_array_operation.size - 1

	@property
	def definition_token(self):
		return '[%d]' % self.size

	@property
	def description_prefix(self):
		return super().description_prefix + ' %d' % self.size

	@property
	def description_prefix_plural(self):
		return super().description_prefix_plural + ' %d' % self.size


def main():
	#return debug()
	print('#include <cassert>')
	print('#include <type_traits>')
	print('#include "typedecl.hpp"')
	print('')
	print('int main() {')
	BasicType.generate('int')
	print('}')

	printerr()
	printerr('Total types:', total_types)
	printerr('Guessed declarations:', guessed_declarations)
	printerr('Typedecls:', typedecls)

def debug():
	type = Volatile(Const(BasicType('int')))
	printerr(type.description())
	printerr(type)
	normalized = type.normalized()
	printerr(normalized)
	printerr(type is normalized)
	printerr(normalized.declaration())
	printerr('int volatile const', '# Expected')
	sys.exit(1)


if __name__ == '__main__':
	main()
