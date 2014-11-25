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

class Symbol(Atom):
    def __init__(self,value,**kwargs):
        super(Symbol,self).__init__(value,**kwargs)

