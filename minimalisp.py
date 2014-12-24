from __future__ import print_function

import re
import traceback
import types

class Value(object):
    def __init__(self, **kwargs):
        for key in kwargs:
            if key == 'start':
                self.start = kwargs['start']
            elif key == 'end':
                self.end = kwargs['end']
            else:
                raise Exception('Unexpected keyword argument {}'.format(key))

    def __repr__(self):
        return unicode(self)

class SExpression(Value):
    def __init__(self,value,**kwargs):
        super(SExpression,self).__init__(**kwargs)
        self.value = tuple(value)

    def __unicode__(self):
        return u'({})'.format(u' '.join(map(unicode,self.value)))

    def __repr__(self):
        return unicode(self)

class Atom(Value):
    def __init__(self,value,**kwargs):
        super(Atom,self).__init__(**kwargs)
        self.value = value

    def __unicode__(self):
        return unicode(self.value)

class Number(Atom):
    def __init__(self,value,**kwargs):
        super(Number,self).__init__(value,**kwargs)

    def __eq__(self,other):
        return self.value == other.value
 
class String(Atom):
    def __init__(self,value,**kwargs):
        super(String,self).__init__(value,**kwargs)

    def __eq__(self,other):
        return self.value == other.value

class Identifier(Atom):
    def __init__(self,value,**kwargs):
        super(Identifier,self).__init__(value,**kwargs)

KEYWORDS = {}

class Keyword(Atom):
    def __init__(self,value,**kwargs):
        super(Keyword,self).__init__(object(),**kwargs)
        self.string = value

    def __eq__(self,other):
        return self is other

    def __repr__(self):
        return self.string

def create_keyword(value,**kwargs):
    if value in KEYWORDS:
        return KEYWORDS[value]

    k = Keyword(value,**kwargs)
    KEYWORDS[value] = k
    return k

token_regex = re.compile(r'''(?mx)
    (\s*|\#.*?\n)*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number>\-?\d+\.\d+|\-?\d+)|
    (?P<string>"[^"]*")|
    (?P<identifier>[A-Za-z\?\-\+\*/=]+)|
    (?P<keyword>\:[A-Za-z\?\-\+\*/=]*)
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

            result.append(SExpression(
                tmp,
                start = start,
                end = match.end('close_parenthese')))

        elif match.group('number'):
            v = float(match.group('number'))
            if v.is_integer(): v = int(v)

            result.append(Number(
                v,
                start = match.start('number'),
                end = match.end('number')))

        elif match.group('string'):
            result.append(String(
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

class Nil(Value):
    def __init__(self,**kwargs):
        super(Nil,self).__init__(**kwargs)

    def __unicode__(self):
        return 'nil'

NIL = Nil()

class Boolean(Value):
    def __init__(self, value, **kwargs):
        super(Boolean,self).__init__(**kwargs)
        self.value = value

    def __unicode__(self):
        return "true" if self.value else "false"

class Map(Value):
    def __init__(self, value, **kwargs):
        super(Map,self).__init__(**kwargs)
        self.value = value
        self.call = py_to_mini(lambda key : self.value[key])

    def __repr__(self):
        return repr(self.value)
    
    def __call__(self, pattern, environment):
        return self.call(pattern,environment)

TRUE = Boolean(True)
FALSE = Boolean(False)

def py_to_mini(py_object):
    if isinstance(py_object,types.FunctionType) or isinstance(py_object,types.BuiltinFunctionType):
        def wrapped(pattern, environment):
            result = py_object(*map(lambda arg : evaluate(arg,environment),pattern))

            return {
                True    : TRUE,
                False   : FALSE,
                None    : NIL,
            }.get(result, result)

        return wrapped

    assert False

def apply(function_or_special_form, pattern, environment):
    return function_or_special_form(pattern, environment)

def evaluate(expression, environment):
    if isinstance(expression, Number) or isinstance(expression, String) or isinstance(expression,Keyword):
        return expression

    if isinstance(expression, Identifier):
        if expression.value in environment:
            return environment[expression.value]

        raise Exception('UndefinedIdentifierError: Undefined identifier {}'.format(expression.value))

    if isinstance(expression, SExpression):
        return apply(evaluate(expression.value[0],environment), expression.value[1:], environment)

    assert False

def _assert(pattern, environment):
    def assert_internal(*arguments):
        if len(arguments) == 0:
            raise Exception("ArgumentError: assert expects 1 or more arguments, received none")
        
        if len(arguments) == 1:
            description = 'assertion failed'
            assertion = arguments
        
        else:
            description = arguments[0].value
            assertion = arguments[1:]
        
        if not isinstance(assertion[-1],Boolean):
            raise Exception("TypeError: `assert` expected Boolean assertion but received {}".format(type(assertion)))
        
        if assertion[-1] is TRUE:
            return None
        
        if assertion[-1] is FALSE:
            raise Exception("AssertionError: {}".format(description))
        
        assert False

    # Execute in nested scope
    return py_to_mini(assert_internal)(pattern, dict(environment))

def throws(pattern, environment):
    if len(pattern) != 2:
        raise Exception("throws? expects 2 argument, received {}".format(len(pattern)))

    expression = pattern[0]
    exception = evaluate(pattern[1], environment)

    if not isinstance(exception, String):
        raise Exception('throws? expects a string as the second argument')

    try:
        evaluate(expression, environment)
        return FALSE
    except Exception as e:
        exception_type, message = e.message.split(':',1)
        return TRUE if exception_type == exception.value else FALSE

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

def define(pattern, environment):
    if len(pattern) < 2:
        raise Exception('DefineError')

    head = pattern[0]
    body = pattern[1:]

    if isinstance(head, Identifier):
        identifier = head.value

        if identifier in environment:
            raise Exception('AlreadyDefinedError: the identifier {} is already defined'.format(identifier))

        environment[identifier] = evaluate_expressions(body, environment)

        return NIL

    if isinstance(head, SExpression):
        raise Exception('NotImplementedError: Defining patterns is not yet implemented')

    raise Exception('TypeError: `define` expected Identifier or SExpression, got {}'.format(type(head)))

def defined_p(pattern, environment):
    if len(pattern) != 1:
        raise Exception("ArgumentError: `defined?` expects 1 argument, received {}".format(len(pattern)))

    return TRUE if pattern[0].value in environment else FALSE

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

def _map(*arguments):
    if len(arguments) % 2 != 0:
        raise Exception("ArgumentError: `map` takes an even number of arguments")
    return Map(dict((arguments[i:i+2] for i in range(0, len(arguments), 2))))

# This is vau from John N. Shutt's seminal paper
# https://www.wpi.edu/Pubs/ETD/Available/etd-090110-124904/unrestricted/jshutt.pdf
# While Greek letters are appropriate for an academic, theoretical context, they make for
# poor variable names, so this is tentatively named `operative`
def operative(pattern, environment):
    if not isinstance(pattern[0],SExpression):
        raise Exception("ArgumentError: The first argument to `operative` should be an SExpression")

    if not all([isinstance(arg, SExpression) for arg in pattern[0].value]):
        raise Exception("ArgumentError: Unexpected {} {}".format(type(arg),arg))

    if not isinstance(pattern[1],Identifier):
        raise Exception("ArgumentError: The second argument to `operative` should be an identifer")

    argument_identifiers = [ai.value for ai in pattern[0].value]
    calling_environment_identifier = pattern[1].value

    existing = set()
    for ai in argument_identifiers:
        if ai in existing:
            raise Exception("ArgumentError: Argument `{}` already defined".format(ai))
        if calling_environment_identifier == ai:
            raise Exception("ArgumentError: Argument `{}` may not be the same as calling environment identifier".format(ai))
        existing.add(ai)

    local_environment = dict(environment)
    
    def result(calling_pattern,calling_environment):
        if not len(calling_pattern) == len(argument_identifiers):
            raise Exception("ArgumentError: operative expected {} arguments, received {}".format(len(argument_identifiers),len(calling_pattern)))

        for i in range(len(argument_identifiers)):
            local_environment[argument_identifiers[i]] = calling_pattern[i]

        local_environment[calling_environment_identifier] = Map(calling_environment)

        return evaluate_expressions(pattern[2:], local_environment)

    return result

builtins = {
    # Builtin constants
    'true'      : TRUE,
    'false'     : FALSE,
    'nil'       : NIL,

    # Builtin functions
    '='         : py_to_mini(lambda l,r : l == r),
    'not'       : py_to_mini(_not),
    'print'     : py_to_mini(print),
    'map'       : py_to_mini(_map),

    # Builtin special forms
    'assert'    : _assert,
    'define'    : define,
    'defined?'  : defined_p,
    'if'        : _if,
    'operative' : operative,
    'throws?'   : throws,
}

if __name__ == '__main__':
    import sys

    arguments = sys.argv[1:]

    if len(arguments) == 0:
        environment = dict(builtins.items())
        
        while True:
            source = raw_input('>>> ')
            
            try:
                print(evaluate_expressions(parse(source), environment))
        
            except:
                traceback.print_exc()

    else:
        for filename in arguments:
            environment = dict(builtins.items())
            
            with open(filename,'r') as f:
                source = f.read()

            try:
                print(evaluate_expressions(parse(source), environment))

            except:
                traceback.print_exc()
