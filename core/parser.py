from ply import lex, yacc
from .proto import Params, Actor, Draw, Picture, Protocol, Comment

##########################################################
# 1. 词法分析器
##########################################################
reserved = {'if': 'IF', 'while': 'WHILE',
            'actor': 'ACTOR', 'arrow': 'ARROW', 'line': 'LINE',
            'picture': "PICTURE", 'protocol': "PROTOCOL",
            'gridx': 'PARAM_GRIDX', 'gridy': 'PARAM_GRIDY',
            'width': 'PARAM_WIDTH', 'height': 'PARAM_HEIGHT',
            'line_style': 'PARAM_LINE', 'arrowl_style': 'PARAM_ARROWL',
            'arrowr_style': 'PARAM_ARROWR', 'arrow_style': 'PARAM_ARROW'}
tokens = ['COLON', 'MINUS', 'LANGLE', 'RANGLE', 'LPAREN', 'RPAREN', 'EQUAL', 'COMMA',
          'NEWLINE', 'TEXT', 'COMMENT', 'NUMBER', 'IDENTIFIER']
tokens += list(reserved.values())

t_COMMA = r','
t_COLON = r':'
t_MINUS = r'-'
t_EQUAL = r'='
t_LANGLE = r'<'
t_RANGLE = r'>'
t_LPAREN = r'\('
t_RPAREN = r'\)'


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.lexer.line_start = t.lexpos + len(t.value)


def t_TEXT(t):  # 匹配双引号包围的字符串，支持转义字符
    r'\"(\\.|[^\"\\])*\"'
    t.value = t.value.strip().strip('"')
    return t


def t_COMMENT(t):
    r'\#[^\n]*'
    t.value = t.value.strip().strip('#').strip()
    return t


def t_NUMBER(t):
    r'(?:-?\d+|auto)'
    if t.value != 'auto':
        t.value = int(t.value)
    return t


def t_IDENTIFIER(t):
    r'[a-zA-Z_\u4e00-\u9fa5][a-zA-Z_0-9\u4e00-\u9fa5]*'
    # 检查是否为保留字
    t.type = reserved.get(t.value, 'IDENTIFIER')
    return t


t_ignore = ' \t'  # 忽略空格和制表符


def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}, "
          f"column {t.lexpos - t.lexer.line_start + 1}")
    t.lexer.skip(1)


lexer = lex.lex()
lexer.line_start = 0

##########################################################
# 2. 语法分析器
##########################################################

precedence = (
    ('nonassoc', 'NEWLINE'),
)

comments = []
last_item = None
last_line = None


def p_finish(p):
    '''finish : ps'''
    global comments
    p[0] = p[1]
    for c in comments:
        p[0].add(c)


def p_ps(p):
    '''ps : PROTOCOL IDENTIFIER
          | PROTOCOL IDENTIFIER LPAREN parameters RPAREN
          | ps declaration'''
    if p[1] == 'protocol':
        if len(p) == 3:
            p[0] = Protocol(p[2], Params())
        else:
            p[0] = Protocol(p[2], Params(p[4]))
    else:
        p[0] = p[1]
        global comments
        if p[2] is not None:
            for i in comments:
                p[0].add(i)
            p[0].add(p[2])
            comments = []


def p_declaration(p):
    '''declaration : declaration_actor
                   | declaration_picture
                   | declaration_draw
                   | COMMENT'''

    if isinstance(p[1], str):
        item = Comment(p[1].strip())
        line = p.lineno(1)
    else:
        item = p[1]
        line = item.lineno

    global last_item, last_line, comments

    if last_item is None:
        last_item = item
        last_line = line
        if isinstance(item, Comment):
            comments.append(item)
            p[0] = None
        else:
            p[0] = item
    else:
        # 上一个是Comment，当前也是Comment，连续
        if isinstance(last_item, Comment) and isinstance(item, Comment) and last_line + 1 == line:
            last_item.add(item)
            last_line = line
            p[0] = None
        # 上一个是Comment，当前也是Comment，不连续
        elif isinstance(last_item, Comment) and isinstance(item, Comment) and last_line + 1 != line:
            last_item = item
            last_line = line
            comments.append(item)
            p[0] = None
        # 上一个是Comment，当前不是Comment，连续
        elif isinstance(last_item, Comment) and not isinstance(item, Comment) and last_line + 1 == line:
            assert comments.pop() is last_item
            item.prefix_comment = last_item
            last_item = item
            last_line = line
            p[0] = item
        # 上一个是Comment，当前不是Comment，不连续
        elif isinstance(last_item, Comment) and not isinstance(item, Comment) and last_line + 1 != line:
            last_item = item
            last_line = line
            p[0] = item
        # 上一个不是Comment，当前是Comment，同行
        elif not isinstance(last_item, Comment) and isinstance(item, Comment) and last_line == line:
            last_item.suffix_comment = item
            p[0] = None
        # 上一个不是Comment，当前是Comment，不同行
        elif not isinstance(last_item, Comment) and isinstance(item, Comment) and last_line != line:
            last_item = item
            last_line = line
            comments.append(item)
            p[0] = None
        # 上一个不是Comment，当前也不是Comment
        elif not isinstance(last_item, Comment) and not isinstance(item, Comment):
            last_item = item
            last_line = line
            p[0] = item


def p_parameter(p):
    '''parameter : PARAM_GRIDX EQUAL NUMBER
                 | PARAM_GRIDY EQUAL NUMBER
                 | PARAM_WIDTH EQUAL NUMBER
                 | PARAM_HEIGHT EQUAL NUMBER
                 | PARAM_LINE EQUAL IDENTIFIER
                 | PARAM_ARROW EQUAL IDENTIFIER
                 | PARAM_ARROWL EQUAL IDENTIFIER
                 | PARAM_ARROWR EQUAL IDENTIFIER'''
    p[0] = (p[1], p[3])


def p_parameters(p):
    '''parameters : parameter
                  | parameters COMMA parameter'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]


def p_declaration_actor(p):
    '''declaration_actor : ACTOR IDENTIFIER LPAREN parameters RPAREN
                         | ACTOR IDENTIFIER'''
    if len(p) == 3:
        p[0] = Actor(p[2], Params())
    else:
        p[0] = Actor(p[2], Params(p[4]))
    p[0].lineno = p.lineno(1)


def p_arrowpart(p):
    '''arrowpart : LANGLE
                 | RANGLE
                 | MINUS'''
    p[0] = p[1]


def p_declaration_draw(p):
    '''declaration_draw : IDENTIFIER COLON TEXT
                        | IDENTIFIER LPAREN parameters RPAREN COLON TEXT
                        | IDENTIFIER arrowpart arrowpart IDENTIFIER COLON TEXT
                        | IDENTIFIER arrowpart arrowpart IDENTIFIER LPAREN parameters RPAREN COLON TEXT'''
    if p[2] == ':':
        p[0] = Draw(p[1], p[1], None, None, p[3], [])
    elif p[2] == '(':
        p[0] = Draw(p[1], p[1], None, None, p[6], p[3])
    elif len(p) == 7:
        p[0] = Draw(p[1], p[4], p[2], p[3], p[6], [])
    else:
        p[0] = Draw(p[1], p[4], p[2], p[3], p[9], p[6])
    p[0].lineno = p.lineno(1)


def p_declaration_picture(p):
    '''declaration_picture : PICTURE IDENTIFIER COLON TEXT
                           | PICTURE IDENTIFIER LPAREN parameters RPAREN COLON TEXT'''
    if len(p) == 5:
        p[0] = Picture(p[2], p[4], Params([]))
    else:
        p[0] = Picture(p[2], p[7], Params(p[4]))
    p[0].lineno = p.lineno(1)


def p_error(p):
    def get_error_context(p):
        last_cr = lexer.lexdata.rfind('\n', 0, p.lexpos)
        next_nl = lexer.lexdata.find('\n', p.lexpos)
        if next_nl < 0:
            next_nl = len(lexer.lexdata)
        return lexer.lexdata[last_cr+1:next_nl]

    if p:
        col = p.lexpos - lexer.line_start + 1
        print(f"Syntax error in line {p.lineno}:")
        print(f"    {get_error_context(p)}")
        print(" " * (col + 3) + "^")
    else:
        print("Syntax error at EOF")


parser = yacc.yacc(debug=True)
