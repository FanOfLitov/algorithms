import ply.lex as lex


class XMLLexer:
    """Лексический анализатор для подмножества XML"""

    # Определение токенов
    tokens = (
        'TAG_OPEN',  # <
        'TAG_CLOSE',  # >
        'SLASH',  # /
        'EQUALS',  # =
        'IDENTIFIER',  # Имя тега или атрибута
        'STRING',  # Строковое значение в кавычках
        'TEXT',  # Текстовое содержимое
        'COMMENT',  # <!-- комментарий -->
        'CDATA',  # <![CDATA[ ... ]]>
        'PROCESSING_INSTR',  # <? ... ?>
        'DOCTYPE',  # <!DOCTYPE ... >
    )

    # Регулярные выражения для простых токенов
    t_TAG_OPEN = r'<'
    t_TAG_CLOSE = r'>'
    t_SLASH = r'/'
    t_EQUALS = r'='

    # Игнорируемые символы
    t_ignore = ' \t\r'

    # Состояния для обработки специальных конструкций
    states = (
        ('comment', 'exclusive'),
        ('cdata', 'exclusive'),
        ('pi', 'exclusive'),
        ('doctype', 'exclusive'),
    )

    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.lineno = 1
        self.errors = []

    # Правило для комментариев
    def t_comment(self, t):
        r'<!--'
        t.lexer.begin('comment')
        t.type = 'COMMENT'
        t.lexer.comment_start = t.lexer.lexpos - 4
        return t

    def t_comment_content(self, t):
        r'[^-]+'
        pass

    def t_comment_dash(self, t):
        r'-'
        pass

    def t_comment_end(self, t):
        r'-->'
        t.lexer.begin('INITIAL')
        t.value = t.lexer.lexdata[t.lexer.comment_start:t.lexer.lexpos]
        return t

    def t_comment_error(self, t):
        self.errors.append(f"Недопустимый символ в комментарии: '{t.value[0]}' на строке {t.lineno}")
        t.lexer.skip(1)

    # Правило для CDATA
    def t_CDATA(self, t):
        r'<!\[CDATA\['
        t.lexer.begin('cdata')
        t.lexer.cdata_start = t.lexer.lexpos - 9
        return t

    def t_cdata_content(self, t):
        r'[^\]]+'
        pass

    def t_cdata_end(self, t):
        r'\]\]>'
        t.lexer.begin('INITIAL')
        t.value = t.lexer.lexdata[t.lexer.cdata_start:t.lexer.lexpos]
        return t

    # Правило для обработки инструкций
    def t_PROCESSING_INSTR(self, t):
        r'<\?'
        t.lexer.begin('pi')
        t.lexer.pi_start = t.lexer.lexpos - 2
        return t

    def t_pi_content(self, t):
        r'[^?>]+'
        pass

    def t_pi_end(self, t):
        r'\?>'
        t.lexer.begin('INITIAL')
        t.value = t.lexer.lexdata[t.lexer.pi_start:t.lexer.lexpos]
        return t

    # Правило для DOCTYPE
    def t_DOCTYPE(self, t):
        r'<!DOCTYPE'
        t.lexer.begin('doctype')
        t.lexer.doctype_start = t.lexer.lexpos - 9
        return t

    def t_doctype_content(self, t):
        r'[^>]+'
        pass

    def t_doctype_end(self, t):
        r'>'
        t.lexer.begin('INITIAL')
        t.value = t.lexer.lexdata[t.lexer.doctype_start:t.lexer.lexpos]
        return t

    # Идентификаторы (имена тегов и атрибутов)
    def t_IDENTIFIER(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_\-:\.]*'
        return t

    # Строковые значения
    def t_STRING(self, t):
        r'\"([^\\\"]|\\.)*\"|\'([^\\\']|\\.)*\''
        # Убираем кавычки
        t.value = t.value[1:-1]
        return t

    # Текстовое содержимое
    def t_TEXT(self, t):
        r'[^<]+'
        # Пропускаем пустой текст (только пробелы и переводы строк)
        if t.value.strip():
            t.value = t.value.strip()
            return t

    # Отслеживание номеров строк
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Обработка ошибок
    def t_error(self, t):
        self.errors.append(f"Недопустимый символ: '{t.value[0]}' на строке {t.lineno}")
        t.lexer.skip(1)

    def tokenize(self, data):
        """Токенизация входных данных"""
        self.lexer.input(data)
        tokens = []
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens.append({
                'type': tok.type,
                'value': tok.value,
                'lineno': tok.lineno,
                'lexpos': tok.lexpos
            })
        return tokens

    def get_errors(self):
        """Получить список ошибок"""
        return self.errors

    def reset(self):
        """Сброс состояния лексера"""
        self.lexer.lineno = 1
        self.errors = []