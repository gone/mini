import re

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

            result.append(value.SExpression(
                tmp,
                start = start,
                end = match.end('close_parenthese')))

        elif match.group('number_literal'):
            v = float(match.group('number_literal'))
            if v.is_integer(): v = int(v)

            result.append(value.NumberLiteral(
                v,
                start = match.start('number_literal'),
                end = match.end('number_literal')))

        elif match.group('string_literal'):
            result.append(value.StringLiteral(
                match.group('string_literal'),
                start = match.start('string_literal'),
                end = match.end('string_literal')))

        elif match.group('identifier'):
            result.append(value.Identifier(
                match.group('identifier'),
                start = match.start('identifier'),
                end = match.end('identifier')))

        else:
            raise Exception()

    assert not stack, "Unmatched parenthese ("
    return value.SExpression(result)
