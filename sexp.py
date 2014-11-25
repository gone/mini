import re
 
token_regex = r'''(?mx)
    \s*(?:
    (?P<brackl>\()|
    (?P<brackr>\))|
    (?P<num>\-?\d+\.\d+|\-?\d+)|
    (?P<sq>"[^""]*")|
    (?P<s>[^(^)\s]+)
    )'''
                                                      
def parse(source):
    stack = []
    out = []

    for termtypes in re.finditer(token_regex, source):
        term, value = [(t,v) for t,v in termtypes.groupdict().items() if v][0]

        if term == 'brackl':
            stack.append(out)
            out = []

        elif term == 'brackr':
            assert stack, "Trouble with nesting of brackets"
            tmpout, out = out, stack.pop(-1)
            out.append(tmpout)

        elif term == 'num':
            v = float(value)
            if v.is_integer(): v = int(v)
            out.append(v)

        elif term == 'sq':
            out.append(value[1:-1])

        elif term == 's':
            out.append(value)

        else:
            raise NotImplementedError("Error: %r" % (term, value))

    assert not stack, "Trouble with nesting of brackets"
    return out[0]
