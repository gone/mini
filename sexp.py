import re
 
token_regex = re.compile(r'''(?mx)
    \s*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number_literal>\-?\d+\.\d+|\-?\d+)|
    (?P<string_literal>"[^"]*")|
    (?P<name>[A-Za-z\?\-]+)
    )''')

def parse(source):
    stack = []
    out = []

    for match in token_regex.finditer(source):
        term, value = [(t,v) for t,v in match.groupdict().items() if v][0]

        if term == 'open_parenthese':
            stack.append(out)
            out = []

        elif term == 'close_parenthese':
            assert stack, "Unmatched parenthese )"
            tmpout, out = out, stack.pop()
            out.append(tmpout)

        elif term == 'number_literal':
            v = float(value)
            if v.is_integer(): v = int(v)
            out.append(v)

        elif term == 'string_literal':
            out.append(value)

        elif term == 'name':
            out.append(value)

        else:
            raise NotImplementedError("Error: term %s value %s" % (term, value))

    assert not stack, "Trouble with nesting of brackets"
    return out
