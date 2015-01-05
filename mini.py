from __future__ import print_function

import re
import traceback
import types

class MiniObject(object):
    def __init__(self, py_object, **meta):
        (   "The following python types map to the following mini types:\n"
            "   bool -> boolean\n"
            "   str -> string\n"
            "   int -> integer\n"
            "   float -> float\n"
            "   tuple -> list (may contain different types)\n"
            "   list -> vector (may only contain one type)\n"
            "   dict -> map\n"
            "   MiniKeyword -> keyword\n"
            "mini vectors and maps should be treated as though immutable"
            "s-expressions should be parsed as tuples"
        )
        self.py_object = py_object
        self.meta = meta

class Identifier(object):
    def __init__(self,value,**kwargs):
        self.value = value

        self.start = kwargs.get('start')
        self.end = kwargs.get('end')

    def __repr__(self):
        return '<identifier {}>'.format(self.value)

KEYWORDS = {}

class MiniKeyword(object):
    def __init__(self,string):
        self.string = string

    def __eq__(self,other):
        return self is other

    def __repr__(self):
        return '<keyword {}>'.format(self.string)

def create_keyword(value,**kwargs):
    if value in KEYWORDS:
        return KEYWORDS[value]

    k = MiniObject(MiniKeyword(value), **kwargs)
    KEYWORDS[value] = k
    return k

token_regex = re.compile(r'''(?mx)
    (\s*|\#.*?\n)*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number>\-?\d+\.\d+|\-?\d+)|
    (?P<string>"[^"]*")|
    (?P<identifier>[_A-Za-z\?\-\+\*/=]+)|
    (?P<keyword>\:[_A-Za-z\?\-\+\*/=]*)
    )''')

def parse(source):
    stack = []
    result = []

    for match in token_regex.finditer(source):
        if match.group('open_parenthese'):
            stack.append((match.start('open_parenthese'),result))
            result = []

        elif match.group('close_parenthese'):
            assert stack, "Unmatched parenthese )"
            tmp, result = result, stack.pop()
            start, result = result

            result.append(MiniObject(
                tuple(tmp),
                start = start,
                end = match.end('close_parenthese')))

        elif match.group('number'):
            v = float(match.group('number'))
            if v.is_integer(): v = int(v)

            result.append(MiniObject(
                v,
                start = match.start('number'),
                end = match.end('number')))

        elif match.group('string'):
            result.append(MiniObject(
                match.group('string')[1:-1],
                start = match.start('string'),
                end = match.end('string')))

        elif match.group('identifier'):
            result.append(Identifier(
                match.group('identifier'),
                start = match.start('identifier'),
                end = match.end('identifier')))

        elif match.group('keyword'):
            result.append(create_keyword(
                match.group('keyword'),
                start = match.start('keyword'),
                end = match.end('keyword')))

        else:
            raise Exception()

    assert not stack, "Unmatched parenthese ("
    return result

class Nil(MiniObject):
    def __init__(self,**kwargs):
        super(Nil,self).__init__(None,**kwargs)

    def __repr__(self):
        return 'nil'

NIL = Nil()

class Boolean(MiniObject):
    def __init__(self, py_object, **kwargs):
        super(Boolean,self).__init__(py_object, **kwargs)

    def __unicode__(self):
        return "true" if self.value else "false"

TRUE = Boolean(True)
FALSE = Boolean(False)

def is_number(arg):
    if isinstance(arg, float):
        return True

    # isinstance(True, int) returns True
    return isinstance(arg, int) and not isinstance(arg, bool)

def py_to_mini(py_object):
    if isinstance(py_object,types.FunctionType) or isinstance(py_object,types.BuiltinFunctionType):
        def wrapped(pattern, environment):
            result = py_object(*map(lambda arg : evaluate(arg,environment),pattern))

            if is_number(result):
                return MiniObject(result)

            return {
                True    : TRUE,
                False   : FALSE,
                None    : NIL,
            }.get(result, result)

        return wrapped

    assert False

def apply(applicative, pattern, environment):
    if isinstance(applicative,dict):
        applicative = py_to_mini(lambda key : applicative[key])

    return applicative(pattern, environment)

def evaluate(expression, environment):
    if isinstance(expression, MiniObject):
        if isinstance(expression.py_object, str) or is_number(expression.py_object):
            return expression

        if isinstance(expression.py_object, MiniKeyword):
            return expression

        if isinstance(expression.py_object, tuple):
            return apply(evaluate(expression.py_object[0],environment), expression.py_object[1:], environment)

    if isinstance(expression, Identifier):
        while environment != None:
            if expression.value in environment:
                return environment[expression.value]

            environment = environment.get('__parent__')

        raise Exception('UndefinedIdentifierError: Undefined identifier {}'.format(expression.value))

    assert False

def length(collection):
    if isinstance(collection.value, str):
        return len(collection.value)

    raise Exception("TypeError")

def concatenate(l,r):
    # TODO Implement ropes: http://citeseer.ist.psu.edu/viewdoc/download?doi=10.1.1.14.9450&rep=rep1&type=pdf
    # TODO Apply this to other collection types
    if isinstance(l.py_object,str) and isinstance(r.py_object, str):
        return MiniObject(l.py_object + r.py_object)

    raise Exception('TypeError')

def is_integer(arg):
    return isinstance(arg, int) and not isinstance(arg, bool)

def slice(collection, start, end):
    if isinstance(start,MiniObject) and isinstance(end, MiniObject) and is_integer(start.py_object) and is_integer(end.py_object):
        start = start.py_object
        end = end.py_object

        if isinstance(collection.py_object, str):
            return MiniObject(collection.py_object[start:end])

        raise Exception("TypeError")

    if isinstance(start,MiniObject) and is_integer(start.py_object) and end is NIL:
        start = start.py_object

        if isinstance(collection.py_object, str):
            return MiniObject(collection.py_object[start:])

    if start is NIL and isinstance(end, MiniObject) and is_integer(end.py_object):
        end = end.py_object

        if isinstance(collection.py_object, str):
            return MiniObject(collection.py_object[:end])

    raise Exception('TypeError')

def _assert(pattern, environment):
    def assert_internal(*arguments):
        if len(arguments) == 0:
            raise Exception("ArgumentError: assert expects 1 or more arguments, received none")
        
        if len(arguments) == 1:
            description = 'assertion failed'
            assertion = arguments
        
        else:
            description = arguments[0].py_object
            assertion = arguments[1:]
        
        if not isinstance(assertion[-1],Boolean):
            raise Exception("TypeError: `assert` expected Boolean assertion but received {}".format(type(assertion)))
        
        if assertion[-1] is TRUE:
            return None
        
        if assertion[-1] is FALSE:
            raise Exception("AssertionError: {}".format(description))
        
        assert False

    # Execute in nested scope
    return py_to_mini(assert_internal)(pattern, nest(environment))

def throws(pattern, environment):
    if len(pattern) != 2:
        raise Exception("throws? expects 2 argument, received {}".format(len(pattern)))

    expression = pattern[0]
    exception = evaluate(pattern[1], environment)

    if not isinstance(exception.py_object, str):
        raise Exception('throws? expects a string as the second argument')

    try:
        evaluate(expression, environment)
        return FALSE
    except Exception as e:
        exception_type, message = e.message.split(':',1)
        return TRUE if exception_type == exception.py_object else FALSE

def _not(argument):
    if not isinstance(argument, Boolean):
        raise Exception('TypeError: Expected Boolean but received {}'.format(type(argument)))

    if argument == TRUE:
        return FALSE

    if argument == FALSE:
        return TRUE

    assert False

def evaluate_expressions(expressions, environment):
    result = NIL

    for expression in expressions:
        result = evaluate(expression, environment)

    return result

def is_defined(identifier,environment):
    while not environment == None:
        if identifier in environment:
            return True

        environment = environment.get('__parent__')

    return False

def define(pattern, environment):
    if len(pattern) < 2:
        raise Exception('DefineError: `define` expected two arguments, received {}'.format(len(pattern)))

    head = pattern[0]
    body = pattern[1:]

    if isinstance(head, Identifier):
        identifier = head.value

        if is_defined(identifier, environment):
            raise Exception('AlreadyDefinedError: the identifier {} is already defined'.format(identifier))

        environment[identifier] = evaluate_expressions(body, environment)

        return NIL

    if isinstance(head.py_object, tuple):
        raise Exception('NotImplementedError: Defining patterns is not yet implemented')

    raise Exception('TypeError: `define` expected Identifier or list, got {}'.format(type(head)))

def defined_p(pattern, environment):
    if len(pattern) != 1:
        raise Exception("ArgumentError: `defined?` expects 1 argument, received {}".format(len(pattern)))

    if not isinstance(pattern[0], Identifier):
        raise Exception("TypeError")

    return TRUE if is_defined(pattern[0].value, environment) else FALSE

def _if(pattern, environment):
    if not len(pattern) in [2,3]:
        raise Exception("ArgumentError")

    condition = pattern[0]
    if_result_true = pattern[1]
    if_result_false = pattern[2]

    result = evaluate(condition, environment)

    if result is TRUE:
        return evaluate(if_result_true, environment)
    if result is FALSE:
        return evaluate(if_result_false, environment)

    raise Exception("TypeError: `if` expects boolean, received {}".format(type(result)))

def construct(head,tail):
    return (head, tail)

def first(arg):
    if isinstance(arg, tuple):
        return arg[0]

    if isinstance(arg.py_object, tuple):
        return arg.py_object[0]

    raise Exception("TypeError")

def empty_p(collection):
    if isinstance(collection.py_object, tuple):
        return len(collection.value) == 0
    
    assert False

def rest(arg):
    if isinstance(arg, tuple):
        return arg[:1]

    if isinstance(arg.py_object, tuple):
        return MiniObject(arg.py_object[1:])

    raise Exception("TypeError")

def _list(*args):
    return tuple(args)

def nest(environment):
    return {
        '__parent__'    : environment,
    }

# This is vau from John N. Shutt's seminal paper
# https://www.wpi.edu/Pubs/ETD/Available/etd-090110-124904/unrestricted/jshutt.pdf
# While Greek letters are appropriate for an academic, theoretical context, they make for
# poor variable names, so this is tentatively named `operative`
def operative(pattern, environment):
    if not isinstance(pattern[0].py_object,tuple):
        raise Exception("ArgumentError: The first argument to `operative` should be an s-expression")

    if not all([isinstance(arg, Identifier) for arg in pattern[0].py_object]):
        raise Exception("ArgumentError: Unexpected {} {}".format(type(arg),arg))

    if not isinstance(pattern[1],Identifier):
        raise Exception("ArgumentError: The second argument to `operative` should be an identifer")

    argument_identifiers = [ai.value for ai in pattern[0].py_object]
    calling_environment_identifier = pattern[1].value

    existing = set()
    for ai in argument_identifiers:
        if ai in existing:
            raise Exception("ArgumentError: Argument `{}` already defined".format(ai))
        if calling_environment_identifier == ai:
            raise Exception("ArgumentError: Argument `{}` may not be the same as calling environment identifier".format(ai))
        existing.add(ai)

    local_environment = nest(environment)
    
    def result(calling_pattern,calling_environment):
        if not len(calling_pattern) == len(argument_identifiers):
            raise Exception("ArgumentError: operative expected {} arguments, received {}".format(len(argument_identifiers),len(calling_pattern)))

        for i in range(len(argument_identifiers)):
            local_environment[argument_identifiers[i]] = calling_pattern[i]

        local_environment[calling_environment_identifier] = calling_environment

        return evaluate_expressions(pattern[2:], local_environment)

    return result

# This is lambda, but called function
def function(pattern, environment):
    if not isinstance(pattern[0].py_object,tuple):
        raise Exception("ArgumentError: The first argument to `operative` should be an s-expression")

    argument_identifiers = [ai.value for ai in pattern[0].value]

    existing = set()
    for ai in argument_identifiers:
        if ai in existing:
            raise Exception("ArgumentError: Argument `{}` already defined".format(ai))
        existing.add(ai)

    local_environment = nest(environment)
    
    def result(calling_pattern, calling_environment):
        if not len(calling_pattern) == len(argument_identifiers):
            raise Exception("ArgumentError: operative expected {} arguments, received {}".format(len(argument_identifiers),len(calling_pattern)))

        for i in range(len(argument_identifiers)):
            local_environment[argument_identifiers[i]] = evaluate(calling_pattern[i], calling_environment)

        return evaluate_expressions(pattern[1:], local_environment)

    return result

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, string):
    with open(filename, 'w') as f:
        f.write(string)

def is_empty(collection):
    return len(collection) == 0

def throw(exception):
    raise Exception(exception.value)

def add(l,r):
    if isinstance(l, MiniObject) and isinstance(r, MiniObject):
        l = l.py_object
        r = r.py_object

        if is_number(l) and is_number(r):
            return l + r

    raise Excepion('TypeError')

def subtract(l,r):
    if isinstance(l, MiniObject) and isinstance(r, MiniObject):
        l = l.py_object
        r = r.py_object

        if is_number(l) and is_number(r):
            return l - r

    raise Excepion('TypeError')

def multiply(l,r):
    if isinstance(l, MiniObject) and isinstance(r, MiniObject):
        l = l.py_object
        r = r.py_object

        if is_number(l) and is_number(r):
            return l * r

    raise Excepion('TypeError')

def divide(l,r):
    if isinstance(l, MiniObject) and isinstance(r, MiniObject):
        l = l.py_object
        r = r.py_object

        if is_number(l) and is_number(r):
            if isinstance(l,int) and isinstance(r,int) and l % r != 0:
                l = float(l)

            return l / r

    raise Excepion('TypeError')

def idivide(l,r):
    if isinstance(l, MiniObject) and isinstance(r, MiniObject):
        l = l.py_object
        r = r.py_object

        if is_number(l) and is_number(r):
            return l // r

    raise Excepion('TypeError')

def mod(l,r):
    if isinstance(l, MiniObject) and isinstance(r, MiniObject):
        l = l.py_object
        r = r.py_object

        if is_number(l) and is_number(r):
            return l % r

    raise Excepion('TypeError')

def eq(l,r):
    if isinstance(l,MiniObject) and isinstance(r,MiniObject):
        return l.py_object == r.py_object

    return l == r

def lt(l,r):
    if is_number(l.py_object) and is_number(r.py_object):
        return l.py_object < r.py_object

    if isinstance(l.py_object,str) and isinstance(r.py_object,str):
        return l.py_object < r.py_object

    raise TypeError()

def gt(l,r):
    if is_number(l.py_object) and is_number(r.py_object):
        return l.py_object > r.py_object

    if isinstance(l.py_object,str) and isinstance(r.py_object,str):
        return l.py_object > r.py_object

    raise TypeError()

def le(l,r):
    return lt(l,r) or eq(l,r)

def ge(l,r):
    return gt(l,r) or eq(l,r)

builtins = {
    # Builtin constants
    'true'      : TRUE,
    'false'     : FALSE,
    'nil'       : NIL,

    # Builtin general functions
    '='             : py_to_mini(eq),
    '<'             : py_to_mini(lt),
    '>'             : py_to_mini(gt),
    '<='            : py_to_mini(le),
    '>='            : py_to_mini(ge),
    'evaluate'      : py_to_mini(evaluate),
    'print'         : py_to_mini(print),
    'prompt'        : py_to_mini(raw_input),
    'read-file'     : py_to_mini(read_file),
    'throw'         : py_to_mini(throw),
    'write-file'    : py_to_mini(write_file),

    # Builtin number functions
    '+'             : py_to_mini(add),
    '-'             : py_to_mini(subtract),
    '*'             : py_to_mini(multiply),
    '/'             : py_to_mini(divide),
    '//'            : py_to_mini(idivide),
    'mod'           : py_to_mini(mod),

    # Builtin collection (string, list, vector) functions
    'concatenate'   : py_to_mini(concatenate),
    'empty?'        : py_to_mini(is_empty),
    'first'         : py_to_mini(first),
    'length'        : py_to_mini(length),
    'list'          : py_to_mini(_list),
    'rest'          : py_to_mini(rest),
    'slice'         : py_to_mini(slice),

    # Builtin boolean functions
    'not'           : py_to_mini(_not),

    # Builtin special forms
    'assert'    : _assert,
    'define'    : define,
    'defined?'  : defined_p,
    'function'  : function,
    'if'        : _if,
    'operative' : operative,
    'throws?'   : throws,
}

if __name__ == '__main__':
    import os.path
    import sys

    arguments = sys.argv[1:]

    predefineds = nest(dict(builtins))
    predefineds_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'predefineds.mini')

    with open(predefineds_filename, 'r') as predefineds_file:
        predefineds_source = predefineds_file.read()

        try:
            evaluate_expressions(parse(predefineds_source), predefineds)

        except:
            traceback.print_exc()

    if len(arguments) == 0:
        environment = nest(dict(predefineds))
        
        while True:
            source = raw_input('>>> ')
            
            try:
                print(evaluate_expressions(parse(source), environment))
        
            except:
                traceback.print_exc()

    else:
        filename = arguments[0]
        arguments = arguments[1:]

        environment = nest(dict(predefineds))
        environment['__file__'] = os.path.join(os.path.realpath(filename))
        environment['__arguments__'] = tuple(arguments)
        
        with open(filename,'r') as f:
            source = f.read()

        try:
            print(evaluate_expressions(parse(source), environment))

        except:
            traceback.print_exc()
