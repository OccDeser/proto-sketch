from ply import lex, yacc
from .proto import Params, Actor, Draw, Picture, Protocol

# 1. 词法分析器
reserved = {'if': 'IF', 'while': 'WHILE',
            'actor': 'ACTOR', 'arrow': 'ARROW', 'line': 'LINE',
            'picture': "PICTURE", 'protocol': "PROTOCOL",
            'gridx': 'PARAM_GRIDX', 'gridy': 'PARAM_GRIDY',
            'width': 'PARAM_WIDTH', 'height': 'PARAM_HEIGHT',
            'line_style': 'PARAM_LINE', 'arrowl_style': 'PARAM_ARROWL',
            'arrowr_style': 'PARAM_ARROWR', 'arrow_style': 'PARAM_ARROW'}
tokens = ['COLON', 'MINUS', 'LANGLE', 'RANGLE', 'LPAREN', 
          'RPAREN', 'EQUAL', 'COMMA', 'NUMBER', 'TEXT', 'IDENTIFIER']
tokens += list(reserved.values())

t_COMMA = r','
t_COLON = r':'
t_MINUS = r'-'
t_EQUAL = r'='
t_LANGLE = r'<'
t_RANGLE = r'>'
t_LPAREN = r'\('
t_RPAREN = r'\)'


def t_TEXT(t):
    r'\"(\\.|[^\"\\])*\"'  # 匹配双引号包围的字符串，支持转义字符
    t.value = t.value.strip().strip('"')
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


t_ignore = ' \t\n'  # 忽略空格和制表符


def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)


lexer = lex.lex()

# 2. 语法分析器


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
        p[0].add(p[2])


def p_declaration(p):
    '''declaration : declaration_actor
                   | declaration_picture
                   | declaration_draw'''
    p[0] = p[1]


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
    '''declaration_actor : ACTOR IDENTIFIER 
                    | ACTOR IDENTIFIER LPAREN parameters RPAREN'''
    if len(p) == 3:
        p[0] = Actor(p[2], Params())
    else:
        p[0] = Actor(p[2], Params(p[4]))


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


def p_declaration_pickture(p):
    '''declaration_picture : PICTURE IDENTIFIER COLON TEXT
                           | PICTURE IDENTIFIER LPAREN parameters RPAREN COLON TEXT'''
    if len(p) == 5:
        p[0] = Picture(p[2], p[4], Params([]))
    else:
        p[0] = Picture(p[2], p[7], Params(p[4]))


def p_error(p):
    print("Syntax error!")


parser = yacc.yacc(debug=True)
