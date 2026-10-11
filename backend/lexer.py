import re
from typing import List
from models import Token, TokenStats

KEYWORDS = {
    "int", "float", "double", "char", "void",
    "if", "else", "while", "for", "do", "return",
    "break", "continue", "struct", "typedef", "sizeof",
    "switch", "case", "default", "const", "static", "unsigned", "signed", "long", "short"
}

OPERATORS = {
    "==", "!=", "<=", ">=", "&&", "||", "->", "++", "--",
    "+=", "-=", "*=", "/=", "%=",
    "+", "-", "*", "/", "%", "=", "<", ">", "!", "&", "|", "."
}

SEPARATORS = {
    ";", ",", "{", "}", "(", ")", "[", "]"
}

class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.length = len(code)
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.token_id = 1
        self.stats = TokenStats()

    def tokenize(self) -> List[Token]:
        self.tokens = []
        self.token_id = 1
        self.pos = 0
        self.line = 1
        self.col = 1
        self.stats = TokenStats()

        while self.pos < self.length:
            ch = self.code[self.pos]

            # Whitespace handling
            if ch == '\n':
                self.line += 1
                self.col = 1
                self.pos += 1
                continue
            elif ch.isspace():
                self.col += 1
                self.pos += 1
                continue

            start_line = self.line
            start_col = self.col

            # Multi-character operators checking first
            two_char = self.code[self.pos:self.pos+2]
            if len(two_char) == 2 and two_char in OPERATORS:
                self.add_token(two_char, "OPERATOR", start_line, start_col)
                self.pos += 2
                self.col += 2
                self.stats.operators += 1
                continue

            if ch in OPERATORS:
                self.add_token(ch, "OPERATOR", start_line, start_col)
                self.pos += 1
                self.col += 1
                self.stats.operators += 1
                continue

            if ch in SEPARATORS:
                self.add_token(ch, "SEPARATOR", start_line, start_col)
                self.pos += 1
                self.col += 1
                self.stats.separators += 1
                continue

            # String literal
            if ch == '"':
                string_val = self.read_string()
                self.add_token(string_val, "STRING_LITERAL", start_line, start_col)
                self.stats.strings += 1
                continue

            # Character literal
            if ch == "'":
                char_val = self.read_char()
                self.add_token(char_val, "CHAR_LITERAL", start_line, start_col)
                self.stats.constants += 1
                continue

            # Numbers (Integer or Float)
            if ch.isdigit():
                num_val, is_float = self.read_number()
                token_type = "FLOAT_CONSTANT" if is_float else "INT_CONSTANT"
                self.add_token(num_val, token_type, start_line, start_col)
                self.stats.constants += 1
                continue

            # Identifiers or Keywords
            if ch.isalpha() or ch == '_':
                ident_val = self.read_identifier()
                if ident_val in KEYWORDS:
                    self.add_token(ident_val, "KEYWORD", start_line, start_col)
                    self.stats.keywords += 1
                else:
                    self.add_token(ident_val, "IDENTIFIER", start_line, start_col)
                    self.stats.identifiers += 1
                continue

            # Preprocessor directives e.g. #include <stdio.h>
            if ch == '#':
                prep_val = self.read_until_newline()
                self.add_token(prep_val, "PREPROCESSOR", start_line, start_col)
                continue

            # Unknown/Unrecognized character
            self.add_token(ch, "UNKNOWN", start_line, start_col)
            self.pos += 1
            self.col += 1

        self.stats.total = len(self.tokens)
        return self.tokens

    def add_token(self, lexeme: str, token_type: str, line: int, col: int):
        token = Token(
            id=self.token_id,
            lexeme=lexeme,
            token_type=token_type,
            line=line,
            column=col
        )
        self.tokens.append(token)
        self.token_id += 1

    def read_string(self) -> str:
        start_pos = self.pos
        self.pos += 1  # Skip opening quote
        self.col += 1
        val = ['"']

        while self.pos < self.length:
            c = self.code[self.pos]
            val.append(c)
            if c == '\\' and self.pos + 1 < self.length:
                val.append(self.code[self.pos+1])
                self.pos += 2
                self.col += 2
                continue
            self.pos += 1
            self.col += 1
            if c == '"':
                break
        return "".join(val)

    def read_char(self) -> str:
        start_pos = self.pos
        self.pos += 1
        self.col += 1
        val = ["'"]
        while self.pos < self.length:
            c = self.code[self.pos]
            val.append(c)
            if c == '\\' and self.pos + 1 < self.length:
                val.append(self.code[self.pos+1])
                self.pos += 2
                self.col += 2
                continue
            self.pos += 1
            self.col += 1
            if c == "'":
                break
        return "".join(val)

    def read_number(self):
        val = []
        is_float = False
        while self.pos < self.length:
            c = self.code[self.pos]
            if c.isdigit():
                val.append(c)
                self.pos += 1
                self.col += 1
            elif c == '.' and not is_float:
                is_float = True
                val.append(c)
                self.pos += 1
                self.col += 1
            else:
                break
        return "".join(val), is_float

    def read_identifier(self) -> str:
        val = []
        while self.pos < self.length:
            c = self.code[self.pos]
            if c.isalnum() or c == '_':
                val.append(c)
                self.pos += 1
                self.col += 1
            else:
                break
        return "".join(val)

    def read_until_newline(self) -> str:
        val = []
        while self.pos < self.length and self.code[self.pos] != '\n':
            val.append(self.code[self.pos])
            self.pos += 1
            self.col += 1
        return "".join(val)
