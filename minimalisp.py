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

class NumberLiteral(Atom):
    def __init__(self,value,**kwargs):
        super(NumberLiteral,self).__init__(value,**kwargs)
 
class StringLiteral(Atom):
    def __init__(self,value,**kwargs):
        super(StringLiteral,self).__init__(value,**kwargs)

class Identifier(Atom):
    def __init__(self,value,**kwargs):
        super(Identifier,self).__init__(value,**kwargs)

token_regex = re.compile(r'''(?mx)
    \s*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number_literal>\-?\d+\.\d+|\-?\d+)|
    (?P<string_literal>"[^"]*")|
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

        elif match.group('number_literal'):
            v = float(match.group('number_literal'))
            if v.is_integer(): v = int(v)

            result.append(NumberLiteral(
                v,
                start = match.start('number_literal'),
                end = match.end('number_literal')))

        elif match.group('string_literal'):
            result.append(StringLiteral(
                match.group('string_literal'),
                start = match.start('string_literal'),
                end = match.end('string_literal')))

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

    if len(pattern) == 0:
        return function_or_special_form

    assert False

def evaluate(expression, environment):
    if isinstance(expression, NumberLiteral) or isinstance(expression, StringLiteral):
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
