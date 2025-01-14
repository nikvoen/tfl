class Token:
    def __init__(self, kind, value=None):
        self.kind = kind
        self.value = value

    def __repr__(self):
        return f"Token({self.kind}, {self.value})"


def tokenize(regex_str):
    tokens = []
    i = 0
    n = len(regex_str)

    while i < n:
        c = regex_str[i]

        if c.isspace():
            i += 1
            continue

        if c == '(':
            if i + 1 < n and regex_str[i + 1] == '?':
                if i + 2 < n and regex_str[i + 2] == ':':
                    tokens.append(Token('LPAREN', '('))
                    tokens.append(Token('QMARK', '?'))
                    tokens.append(Token('NON_CAPT_GROUP', ':'))
                    i += 3
                else:
                    tokens.append(Token('LPAREN', '('))
                    tokens.append(Token('QMARK', '?'))
                    i += 2
            else:
                tokens.append(Token('LPAREN', '('))
                i += 1

        elif c == ')':
            tokens.append(Token('RPAREN', ')'))
            i += 1

        elif c == '|':
            tokens.append(Token('ALT', '|'))
            i += 1

        elif c == '*':
            tokens.append(Token('STAR', '*'))
            i += 1

        elif c == '\\':
            if i + 1 < n and regex_str[i + 1].isdigit():
                tokens.append(Token('BACKSLASH_DIGIT', regex_str[i + 1]))
                i += 2
            else:
                tokens.append(Token('BACKSLASH', '\\'))
                i += 1

        elif c.isdigit():
            tokens.append(Token('DIGIT', c))
            i += 1

        elif c.isalpha():
            tokens.append(Token('CHAR', c))
            i += 1

        else:
            tokens.append(Token('UNKNOWN', c))
            i += 1

    tokens.append(Token('END'))
    return tokens


class Node:
    pass

class CharNode(Node):
    def __init__(self, ch):
        self.ch = ch

    def __repr__(self):
        return f"CharNode({self.ch!r})"

class ConcatNode(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"ConcatNode({self.left}, {self.right})"

class AltNode(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"AltNode({self.left}, {self.right})"

class StarNode(Node):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"StarNode({self.expr})"

class CaptureGroupNode(Node):
    def __init__(self, group_id, expr):
        self.group_id = group_id
        self.expr = expr

    def __repr__(self):
        return f"CaptureGroupNode(id={self.group_id}, expr={self.expr})"

class NonCaptureGroupNode(Node):
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f"NonCaptureGroupNode({self.expr})"

class BackRefStringNode(Node):
    def __init__(self, group_id):
        self.group_id = group_id

    def __repr__(self):
        return f"BackRefStringNode({self.group_id})"

class RecursiveRefNode(Node):
    def __init__(self, group_id):
        self.group_id = group_id

    def __repr__(self):
        return f"RecursiveRefNode({self.group_id})"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_group_id = 0

    def current_token(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('END')

    def eat(self, kind=None):
        t = self.current_token()
        if kind is not None and t.kind != kind:
            raise ValueError(f"Ожидался токен {kind}, встретился {t}")
        self.pos += 1
        return t

    def parse(self):
        node = self.parse_alt()
        if self.current_token().kind != 'END':
            raise ValueError(
                f"Лишние символы после окончания парсинга: {self.current_token()}"
            )
        return node

    def parse_alt(self):
        left = self.parse_concat()
        while self.current_token().kind == 'ALT':
            self.eat('ALT')
            right = self.parse_concat()
            left = AltNode(left, right)
        return left

    def parse_concat(self):
        left = self.parse_star()
        while True:
            tk = self.current_token().kind
            if tk in ('END', 'RPAREN', 'ALT'):
                break
            right = self.parse_star()
            left = ConcatNode(left, right)
        return left

    def parse_star(self):
        node = self.parse_base()
        while self.current_token().kind == 'STAR':
            self.eat('STAR')
            node = StarNode(node)
        return node

    def parse_base(self):
        t = self.current_token()

        if t.kind == 'LPAREN':
            self.eat('LPAREN')
            if self.current_token().kind == 'QMARK':
                self.eat('QMARK')
                if self.current_token().kind == 'NON_CAPT_GROUP':
                    self.eat('NON_CAPT_GROUP')
                    expr = self.parse_alt()
                    self.eat('RPAREN')
                    return NonCaptureGroupNode(expr)
                else:
                    digit_token = self.eat('DIGIT')
                    group_id = int(digit_token.value)
                    self.eat('RPAREN')
                    return RecursiveRefNode(group_id)
            else:
                self.current_group_id += 1
                group_id = self.current_group_id
                expr = self.parse_alt()
                self.eat('RPAREN')
                return CaptureGroupNode(group_id, expr)

        elif t.kind == 'BACKSLASH_DIGIT':
            self.eat('BACKSLASH_DIGIT')
            group_id = int(t.value)
            return BackRefStringNode(group_id)

        elif t.kind == 'DIGIT':
            val = t.value
            self.eat('DIGIT')
            return CharNode(val)

        elif t.kind == 'CHAR':
            self.eat('CHAR')
            return CharNode(t.value)

        else:
            raise ValueError(f"Неожиданный токен parse_base(): {t}")


def build_group_map(root):
    group_ast = {}

    def dfs(node):
        if isinstance(node, CaptureGroupNode):
            group_ast[node.group_id] = node.expr
            dfs(node.expr)
        elif isinstance(node, ConcatNode):
            dfs(node.left)
            dfs(node.right)
        elif isinstance(node, AltNode):
            dfs(node.left)
            dfs(node.right)
        elif isinstance(node, StarNode):
            dfs(node.expr)
        elif isinstance(node, NonCaptureGroupNode):
            dfs(node.expr)

    dfs(root)
    return group_ast


def analyze_correctness(root):
    group_ast = build_group_map(root)
    memo = {}
    context = set()

    def compute_out_set(node, in_set):
        key = (id(node), frozenset(in_set))
        if key in memo:
            return memo[key]

        if key in context:
            return in_set

        context.add(key)

        if isinstance(node, CharNode):
            res = set(in_set)

        elif isinstance(node, BackRefStringNode):
            if node.group_id not in in_set:
                raise ValueError(
                    f"Ссылка на неинициализированную группу \\{node.group_id}"
                )
            res = set(in_set)

        elif isinstance(node, ConcatNode):
            left_out = compute_out_set(node.left, in_set)
            right_out = compute_out_set(node.right, left_out)
            res = right_out

        elif isinstance(node, AltNode):
            left_out = compute_out_set(node.left, in_set)
            right_out = compute_out_set(node.right, in_set)
            res = left_out.intersection(right_out)

        elif isinstance(node, StarNode):
            _ = compute_out_set(node.expr, in_set)
            res = set(in_set)

        elif isinstance(node, CaptureGroupNode):
            expr_out = compute_out_set(node.expr, in_set)
            new_out = set(expr_out)
            new_out.add(node.group_id)
            res = new_out

        elif isinstance(node, NonCaptureGroupNode):
            res = compute_out_set(node.expr, in_set)

        elif isinstance(node, RecursiveRefNode):
            if node.group_id not in group_ast:
                raise ValueError(
                    f"Рекурсивная ссылка (?{node.group_id}), но группа не объявлена."
                )
            expr_for_k = group_ast[node.group_id]
            sub_out = compute_out_set(expr_for_k, in_set)
            res = sub_out

        else:
            res = set(in_set)

        memo[key] = res
        context.remove(key)
        return res

    try:
        compute_out_set(root, frozenset())
    except ValueError as e:
        raise e


def check_regex_correctness(regex_str):
    tokens = tokenize(regex_str)
    parser = Parser(tokens)

    try:
        ast_root = parser.parse()
    except ValueError as e:
        return f"Синтаксическая ошибка: {e}", None

    try:
        analyze_correctness(ast_root)
    except ValueError as e:
        return f"Семантическая ошибка: {e}", None

    return "OK", ast_root


if __name__ == "__main__":
    while True:
        reg = input("Введите регэкс (пустая строка => выход): ")
        if not reg.strip():
            break
        verdict, tree = check_regex_correctness(reg)
        print("Regex:", reg)
        print("Verdict:", verdict)
        if tree is not None:
            print("AST:", tree)
        print("-" * 40)
