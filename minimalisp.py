import re
import traceback

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
 
class String(Atom):
    def __init__(self,value,**kwargs):
        super(String,self).__init__(value,**kwargs)

class Identifier(Atom):
    def __init__(self,value,**kwargs):
        super(Identifier,self).__init__(value,**kwargs)

token_regex = re.compile(r'''(?mx)
    \s*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number>\-?\d+\.\d+|\-?\d+)|
    (?P<string>"[^"]*")|
    (?P<identifier>[A-Za-z\?\-\+\*/]+)
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
                match.group('string'),
                start = match.start('string'),
                end = match.end('string')))

        elif match.group('identifier'):
            result.append(Identifier(
                match.group('identifier'),
                start = match.start('identifier'),
                end = match.end('identifier')))

        else:
            raise Exception()

    assert not stack, "Unmatched parenthese ("
    return result

class Nil(object):
    def __init__(self):
        pass

NIL = Nil()

class Boolean(object):
    def __init__(self, value):
        self.value = value

TRUE = Boolean(True)
FALSE = Boolean(False)

class SpecialForm(object):
    def __init__(self,function):
        self.function = function

    def __call__(self,pattern,environment):
        return self.function(pattern,environment)

def apply(function_or_special_form, pattern, environment):
    if isinstance(function_or_special_form, SpecialForm):
        return function_or_special_form(pattern, environment)

    if hasattr(function_or_special_form, '__call__'):
        return function_or_special_form(map(lambda arg : evaluate(arg, environment), pattern))

    assert False

def evaluate(expression, environment):
    if isinstance(expression, Number) or isinstance(expression, String):
        return expression

    if isinstance(expression, Identifier):
        return environment[expression.value]

    if isinstance(expression, SExpression):
        return apply(evaluate(expression.value[0],environment), expression.value[1:], environment)

    assert False

if __name__ == '__main__':

    environment = {
        'true'  : TRUE,
        'false' : FALSE,
        'nil'   : NIL,
    }

    while True:
        source = raw_input('>>> ')
        
        try:
            expressions = parse(source)

            for expression in expressions:
                result = evaluate(expression, environment)

            print result

        except:
            traceback.print_exc()
