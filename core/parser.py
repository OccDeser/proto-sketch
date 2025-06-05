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
    return t


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
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}, column {t.lexpos - t.lexer.line_start + 1}")
    t.lexer.skip(1)


lexer = lex.lex()
lexer.line_start = 0

##########################################################
# 2. 语法分析器
##########################################################

# precedence = (
#     ('nonassoc', 'NEWLINE'),  # NEWLINE 不参与结合，但用于优先 shift
# )

def p_ps(p):
    '''ps : PROTOCOL IDENTIFIER
          | PROTOCOL IDENTIFIER LPAREN parameters RPAREN
          | ps declcomment'''
    if p[1] == 'protocol':
        if len(p) == 3:
            p[0] = Protocol(p[2], Params())
        else:
            p[0] = Protocol(p[2], Params(p[4]))
    else:
        p[0] = p[1]
        if p[2] is not None:
            if isinstance(p[2], tuple):
                p[0].add(p[2][0])
                p[0].add(p[2][1])
            else:
                p[0].add(p[2])
        


def p_declcomment(p):
    '''declcomment : multicomment NEWLINE declaration COMMENT NEWLINE
                   | multicomment NEWLINE declaration
                   | declaration COMMENT NEWLINE
                   | declaration NEWLINE
                   | multicomment
                   | NEWLINE
                   '''
    if len(p) == 2:
        if isinstance(p[1], Comment):
            p[0] = p[1]
        else:
            p[0] = None
    elif len(p) == 3:
        p[0] = p[1]
    elif len(p) == 4:
        if isinstance(p[1], Comment):
            if len(p[2]) == 1:
                p[0] = p[3]
                p[0].prefix_comment = p[1]
            else:
                p[0] = (p[1], p[3])
        else:
            p[0] = p[1]
            p[0].suffix_comment = Comment(p[2])
    elif len(p) == 6:
        p[0] = p[3]
        p[0].prefix_comment = p[1]
        p[0].suffix_comment = Comment(p[4])


def p_multicomment(p):
    '''multicomment : multicomment NEWLINE COMMENT
                    | COMMENT'''
    if len(p) == 2:
        p[0] = Comment(p[1])
    else:
        p[0] = p[1]
        p[0].add(p[3])


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
    '''declaration_actor : ACTOR IDENTIFIER LPAREN parameters RPAREN
                         | ACTOR IDENTIFIER'''
    if len(p) == 3:
        p[0] = Actor(p[2], Params())
    else:
        p[0] = Actor(p[2], Params(p[4]))


def p_arrowpart(p):
    '''arrowpart : LANGLE
                 | RANGLE
                 | MINUS'''
    p[0] = p[1]

def p_colonnewline(p):
    '''colonnewline : COLON NEWLINE
                    | COLON'''
    p[0] = p[1]


def p_declaration_draw(p):
    '''declaration_draw : IDENTIFIER colonnewline TEXT
                        | IDENTIFIER LPAREN parameters RPAREN colonnewline TEXT
                        | IDENTIFIER arrowpart arrowpart IDENTIFIER colonnewline TEXT
                        | IDENTIFIER arrowpart arrowpart IDENTIFIER LPAREN parameters RPAREN colonnewline TEXT'''
    if p[2] == ':':
        p[0] = Draw(p[1], p[1], None, None, p[3], [])
    elif p[2] == '(':
        p[0] = Draw(p[1], p[1], None, None, p[6], p[3])
    elif len(p) == 7:
        p[0] = Draw(p[1], p[4], p[2], p[3], p[6], [])
    else:
        p[0] = Draw(p[1], p[4], p[2], p[3], p[9], p[6])


def p_declaration_picture(p):
    '''declaration_picture : PICTURE IDENTIFIER COLON TEXT
                           | PICTURE IDENTIFIER LPAREN parameters RPAREN COLON TEXT'''
    if len(p) == 5:
        p[0] = Picture(p[2], p[4], Params([]))
    else:
        p[0] = Picture(p[2], p[7], Params(p[4]))


def p_error(p):
    def get_error_context(p):
        last_cr = lexer.lexdata.rfind('\n', 0, p.lexpos)
        next_nl = lexer.lexdata.find('\n', p.lexpos)
        if next_nl < 0:
            next_nl = len(lexer.lexdata)
        return lexer.lexdata[last_cr+1:next_nl]
    
    if p:
        col = p.lexpos - lexer.line_start + 1
        print(f"Error in line {p.lineno}:")
        print(f"    {get_error_context(p)}")
        print(" " * (col + 3) + "^")
    else:
        print("Syntax error at EOF")

parser = yacc.yacc(debug=True)
