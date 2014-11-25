import re
 
token_regex = re.compile(r'''(?mx)
    \s*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number_literal>\-?\d+\.\d+|\-?\d+)|
    (?P<string_literal>"[^"]*")|
    (?P<name>[A-Za-z\?\-\+\*/]+)
    )''')

def parse(source):
    stack = []
    result = []

    for match in token_regex.finditer(source):
        term, value = [(t,v) for t,v in match.groupdict().items() if v][0]

        if match.group('open_parenthese'):
            stack.append(result)
            result = []

        elif match.group('close_parenthese'):
            assert stack, "Unmatched parenthese )"
            tmp, result = result, stack.pop()
            result.append(tuple(tmp))

        elif match.group('number_literal'):
            v = float(value)
            if v.is_integer(): v = int(v)
            result.append(v)

        elif match.group('string_literal'):
            result.append(value)

        elif match.group('name'):
            result.append(value)

        else:
            raise NotImplementedError("Error: term %s value %s" % (term, value))

    assert not stack, "Trouble with nesting of brackets"
    return tuple(result)
