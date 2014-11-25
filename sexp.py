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
        if match.group('open_parenthese'):
            stack.append(result)
            result = []

        elif match.group('close_parenthese'):
            assert stack, "Unmatched parenthese )"
            tmp, result = result, stack.pop()
            result.append(tuple(tmp))

        elif match.group('number_literal'):
            v = float(match.group('number_literal'))
            if v.is_integer(): v = int(v)
            result.append(v)

        elif match.group('string_literal'):
            result.append(match.group('string_literal'))

        elif match.group('name'):
            result.append(match.group('name'))

        else:
            raise Exception()

    assert not stack, "Unmatched parenthese ("
    return tuple(result)
