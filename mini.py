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
            "   MiniSymbol -> symbol\n"
            "   Pair -> pair"
            "mini vectors and maps should be treated as though immutable"
            "s-expressions should be parsed as tuples"
        )
        self.py_object = py_object
        self.meta = meta

    def __repr__(self):
        return repr(self.py_object)

class Identifier(object):
    def __init__(self,symbol,**kwargs):
        self.symbol = symbol

        self.start = kwargs.get('start')
        self.end = kwargs.get('end')

    def __repr__(self):
        return '<identifier {}>'.format(self.symbol)

SYMBOLS = {}

class MiniSymbol(object):
    def __init__(self,string):
        self.string = string

    def __eq__(self,other):
        return self is other

    def __repr__(self):
        return '<symbol :{}>'.format(self.string)

class MiniPair(object):
    def __init__(self, car, cdr):
        assert isinstance(car, MiniObject)
        assert isinstance(cdr, MiniObject)

        self.car = car
        self.cdr = cdr

def create_symbol(string,**kwargs):
    if string in SYMBOLS:
        return SYMBOLS[string]

    k = MiniObject(MiniSymbol(string), **kwargs)
    SYMBOLS[string] = k
    return k

def create_cons_collection(py_collection):
    result = NIL

    for item in reversed(py_collection):
        result = MiniObject(MiniPair(item, result))

    return result

def cons_collection_to_py_collection(cons_collection):
    while cons_collection != NIL:
        yield car(cons_collection)
        cons_collection = cdr(cons_collection)

token_regex = re.compile(r'''(?mx)
    (\s*|\#.*?\n)*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number>\-?\d+\.\d+|\-?\d+)|
    (?P<string>"[^"]*")|
    (?P<identifier>[_A-Za-z\?\-\+\*/=\>\<]+)|
    (?P<symbol>\:[_A-Za-z\?\-\+\*/=\>\<]*)
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

            tmp = create_cons_collection(tmp)

            tmp.meta['start'] = start
            tmp.meta['end'] = match.end('close_parenthese')

            result.append(tmp)

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
            result.append(MiniObject(Identifier(
                match.group('identifier'),
                start = match.start('identifier'),
                end = match.end('identifier'))))

        elif match.group('symbol'):
            result.append(create_symbol(
                match.group('symbol')[1:],
                start = match.start('symbol'),
                end = match.end('symbol')))

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
            result = py_object(*map(lambda arg : evaluate(arg,environment),cons_collection_to_py_collection(pattern)))

            if is_number(result) or isinstance(result,MiniPair):
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
        raise Exception("TODO Is this used any more?")

    return applicative(pattern, environment)

def evaluate(expression, environment):
    if isinstance(expression, MiniObject):
        if isinstance(expression.py_object, str) or is_number(expression.py_object):
            return expression

        if isinstance(expression.py_object, MiniSymbol):
            return expression

        if isinstance(expression.py_object, MiniPair):
            return apply(evaluate(car(expression),environment), cdr(expression), environment)

        if isinstance(expression.py_object, Identifier):
            while environment != None:
                if expression.py_object.symbol in environment:
                    return environment[expression.py_object.symbol]
        
                environment = environment.get('__parent__')
        
            raise Exception('UndefinedIdentifierError: Undefined identifier {}'.format(expression.py_object.symbol))

    assert False

def length(string):
    if isinstance(string.py_object, str):
        return len(string.py_object)

    raise Exception("TypeError")

def concatenate(l,r):
    # TODO Implement ropes: http://citeseer.ist.psu.edu/viewdoc/download?doi=10.1.1.14.9450&rep=rep1&type=pdf
    # TODO Apply this to other collection types
    if isinstance(l.py_object,str) and isinstance(r.py_object, str):
        return MiniObject(l.py_object + r.py_object)

    raise Exception('TypeError')

def is_integer(arg):
    return isinstance(arg, int) and not isinstance(arg, bool)

def slice(string, start, end):
    if not isinstance(string.py_object, str):
        raise Exception('TypeError')

    py_string = string.py_object

    if is_integer(start.py_object):
        py_start = start.py_object

    elif start.py_object == None:
        py_start = 0

    else:
        raise Exception('TypeError')

    if is_integer(end.py_object):
        py_end = end.py_object

    elif end.py_object == None:
        py_end = len(py_string)

    else:
        raise Exception('TypeError')

    return MiniObject(py_string[py_start:py_end])

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
    if cons_collection_len(pattern) != 2:
        raise Exception("throws? expects 2 argument, received {}".format(len(pattern)))

    expression = car(pattern)
    exception = evaluate(car(cdr(pattern)), environment)

    if not isinstance(exception.py_object, str):
        raise Exception('throws? expects a string as the second argument')

    try:
        evaluate(expression, environment)
        return FALSE

    except Exception as e:
        if ':' in e.message:
            exception_type, message = e.message.split(':',1)
        else:
            exception_type = e.message

        if exception_type == exception.py_object:
            return TRUE

        raise

def _not(argument):
    if not isinstance(argument, Boolean):
        raise Exception('TypeError: Expected Boolean but received {}'.format(type(argument)))

    if argument == TRUE:
        return FALSE

    if argument == FALSE:
        return TRUE

    assert False

def evaluate_cons_collection_of_expressions(expressions, environment):
    result = NIL

    while expressions != NIL:
        result = evaluate(car(expressions), environment)
        expressions = cdr(expressions)

    return result

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

def cons_collection_len(cons_collection):
    result = 0

    while cons_collection != NIL:
        result += 1
        cons_collection = cdr(cons_collection)

    return result

def define(pattern, environment):
    if cons_collection_len(pattern) < 2:
        raise Exception('DefineError: `define` expected two arguments, received {}'.format(len(pattern)))

    head = car(pattern)
    body = cdr(pattern)

    if isinstance(head, MiniObject):
        if isinstance(head.py_object, Identifier):
            identifier = head.py_object.symbol
        
            if is_defined(identifier, environment):
                raise Exception('AlreadyDefinedError: the identifier {} is already defined'.format(identifier))
        
            environment[identifier] = evaluate_cons_collection_of_expressions(body, environment)
        
            return NIL
        
        elif isinstance(head.py_object, MiniPair):
            raise Exception('NotImplementedError: Defining patterns is not yet implemented')

    raise Exception('TypeError: `define` expected Identifier or list, got {}'.format(type(head)))

def defined_p(pattern, environment):
    if cons_collection_len(pattern) != 1:
        raise Exception("ArgumentError: `defined?` expects 1 argument, received {}".format(len(pattern)))

    if not isinstance(car(pattern).py_object, Identifier):
        raise Exception("TypeError: Expected Identifier but got {}".format(type(car(pattern).py_object)))

    return TRUE if is_defined(car(pattern).py_object.symbol, environment) else FALSE

def _if(pattern, environment):
    if not cons_collection_len(pattern) in [2,3]:
        raise Exception("ArgumentError")

    condition = car(pattern)
    if_result_true = car(cdr(pattern))
    if_result_false = car(cdr(cdr(pattern)))

    result = evaluate(condition, environment)

    if result is TRUE:
        return evaluate(if_result_true, environment)
    if result is FALSE:
        return evaluate(if_result_false, environment)

    raise Exception("TypeError: `if` expects boolean, received {}".format(type(result)))

def nest(environment):
    return {
        '__parent__'    : environment,
    }

# This is vau from John N. Shutt's seminal paper
# https://www.wpi.edu/Pubs/ETD/Available/etd-090110-124904/unrestricted/jshutt.pdf
# While Greek letters are appropriate for an academic, theoretical context, they make for
# poor variable names, so this is tentatively named `operative`
def operative(pattern, environment):
    argument_list_identifier = None
    argument_identifiers = None

    calling_environment_identifier = car(cdr(pattern)).py_object.symbol

    if isinstance(car(pattern).py_object, Identifier):
        argument_list_identifier = car(pattern).py_object.symbol

        if calling_environment_identifier == argument_list_identifier:
            raise Exception("ArgumentError: Argument list identifier `{}` may not be the same as calling environment identifier".format(ai))

    elif car(pattern).py_object == None or isinstance(car(pattern).py_object, MiniPair):
        if not all([isinstance(arg.py_object, Identifier) for arg in cons_collection_to_py_collection(car(pattern))]):
            raise Exception("ArgumentError: Unexpected {} {}".format(type(arg),arg))

        argument_identifiers = [ai.py_object.symbol for ai in cons_collection_to_py_collection(car(pattern))]
        
        existing = set()
        for ai in argument_identifiers:
            if ai in existing:
                raise Exception("ArgumentError: Argument `{}` already defined".format(ai))

            if calling_environment_identifier == ai:
                raise Exception("ArgumentError: Argument `{}` may not be the same as calling environment identifier".format(ai))

            existing.add(ai)

    else:
        raise Exception("ArgumentError: `operative` expected identifier or cons-list as first argument, received {}".format(type(car(pattern).py_object)))

    if not isinstance(car(cdr(pattern)).py_object,Identifier):
        raise Exception("ArgumentError: The second argument to `operative` should be an identifer")

    local_environment = nest(environment)
    
    def result(calling_pattern, calling_environment):
        assert (argument_list_identifier == None) != (argument_identifiers == None)
        if argument_list_identifier != None:
            local_environment[argument_list_identifier] = calling_pattern

        if argument_identifiers != None:
            if not cons_collection_len(calling_pattern) == len(argument_identifiers):
                raise Exception("ArgumentError: operative expected {} arguments, received {}".format(len(argument_identifiers),len(calling_pattern)))

            calling_pattern = list(cons_collection_to_py_collection(calling_pattern))

            for i in range(len(argument_identifiers)):
                local_environment[argument_identifiers[i]] = calling_pattern[i]

        local_environment[calling_environment_identifier] = calling_environment

        return evaluate_cons_collection_of_expressions(cdr(cdr(pattern)), local_environment)

    return result

def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()

def write_file(filename, string):
    with open(filename, 'w') as f:
        f.write(string)

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

def cons(l,r):
    return MiniPair(l,r)

def car(p):
    return p.py_object.car

def cdr(p):
    return p.py_object.cdr

def identifier_to_symbol(identifier):
    if not isinstance(identifier.py_object, Identifier):
        raise Exception('`identifier->symbol` expected identifier, received {}'.format(type(identifier.py_object)))

    return create_symbol(identifier.py_object.symbol)

builtins = {
    # Builtin constants
    'true'      : TRUE,
    'false'     : FALSE,
    'nil'       : NIL,

    # Builtin comparison functions
    '='             : py_to_mini(eq),
    '<'             : py_to_mini(lt),
    '>'             : py_to_mini(gt),
    '<='            : py_to_mini(le),
    '>='            : py_to_mini(ge),

    # Builtin conversion functions
    'identifier->symbol'    : py_to_mini(identifier_to_symbol),

    # Builtin general functions
    'evaluate'      : py_to_mini(evaluate),
    'print'         : py_to_mini(print),
    'prompt'        : py_to_mini(raw_input),
    'read-file'     : py_to_mini(read_file),
    'write-file'    : py_to_mini(write_file),

    # Builtin number functions
    '+'             : py_to_mini(add),
    '-'             : py_to_mini(subtract),
    '*'             : py_to_mini(multiply),
    '/'             : py_to_mini(divide),
    '//'            : py_to_mini(idivide),
    'mod'           : py_to_mini(mod),

    # Builtin pair functions
    'cons'          : py_to_mini(cons),
    'car'           : py_to_mini(car),
    'cdr'           : py_to_mini(cdr),

    # Builtin string functions
    'concatenate'   : py_to_mini(concatenate),
    'length'        : py_to_mini(length),
    'slice'         : py_to_mini(slice),

    # Builtin boolean functions
    'not'           : py_to_mini(_not),

    # Builtin special forms
    'assert'    : _assert,
    'define'    : define,
    'defined?'  : defined_p,
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
