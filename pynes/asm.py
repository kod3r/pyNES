# -*- coding: utf-8 -*-

from nesasm.c6502 import opcodes
from pynes.block import AsmBlock
from re import match

registers = ['A', 'X', 'Y']

__all__ = list(opcodes.keys()) + registers


class Register(object):

    def __init__(self, register):
        self.r = register


class AddMixin(object):

    def is_single(self):
        return 'sngl' in opcodes[self.name]

    def is_immediate(self):
        return 'imm' in opcodes[self.name]

    def is_zp_address(self, arg):
        return (isinstance(arg, basestring) and match(r'^\$\d{1,2}$', arg))

    def is_abs_address(self, arg):
        return (isinstance(arg, basestring) and match(r'^\$\d{4}$', arg))

    def __add__(self, other):
        if isinstance(other, int):
            return self(other)
        elif self.is_zp_address(other):
            return self(other)
        elif self.is_abs_address(other):
            return self(other)

        if isinstance(self, InstructionProxy) and self.is_single():
            left = Instruction(self.name, 'sngl')
        else:
            left = self

        if isinstance(other, InstructionProxy) and other.is_single():
            other = Instruction(other.name, 'sngl')

        if isinstance(other, Instruction):
            return AsmBlock(left, other)
        elif isinstance(other, InstructionProxy):
            return AsmBlock(left, other)
        elif isinstance(other, Register):
            return Instruction(self.name, 'acc', 'A')
        raise Exception('Invalid')



class Instruction(AddMixin):

    def __init__(self, name, address_mode, param=None):
        self.name = name
        self.address_mode = address_mode
        self.param = param

    def __str__(self):
        if 'sngl' == self.address_mode:
            return self.name
        elif 'imm' == self.address_mode:
            return '%s #%i' % (self.name, self.param)
        elif 'acc' == self.address_mode:
            return '%s A' % self.name
        else:
            raise Exception('Invalid Instruction')

    def __repr__(self):
        return '<Instruction %s>' % str(self)


class Param(object):
    pass


class InstructionProxy(AddMixin):

    def __init__(self, name):
        self.name = name
        self.address_mode = False

    def __call__(self, arg=None):
        if self.is_single():
            return Instruction(self.name, 'sngl')
        elif self.is_immediate() and isinstance(arg, int):
            return Instruction(self.name, 'imm', arg)
        elif self.is_zp_address(arg):
            return Instruction(self.name, 'zp', arg)
        elif self.is_abs_address(arg):
            return Instruction(self.name, 'abs', arg)
        raise Exception('Invalid Instruction')

    def __repr__(self):
        return '<InstructionProxy %s>' % self.name


class ModuleWrapper(object):

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        if name in opcodes.keys():
            return InstructionProxy(name)
        elif name in registers:
            return Register(name)
        elif hasattr(self.wrapped, name):
            return getattr(self.wrapped, name)
        else:
            raise AttributeError(name)

import sys
sys.modules[__name__] = ModuleWrapper(sys.modules[__name__])