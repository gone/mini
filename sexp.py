import re
import value

token_regex = re.compile(r'''(?mx)
    \s*(?:
    (?P<open_parenthese>\()|
    (?P<close_parenthese>\))|
    (?P<number_literal>\-?\d+\.\d+|\-?\d+)|
    (?P<string_literal>"[^"]*")|
    (?P<symbol>[A-Za-z\?\-\+\*/]+)
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

        elif match.group('symbol'):
            result.append(value.Symbol(
                match.group('symbol'),
                start = match.start('symbol'),
                end = match.end('symbol')))

        else:
            raise Exception()

    assert not stack, "Unmatched parenthese ("
    return value.SExpression(result)
