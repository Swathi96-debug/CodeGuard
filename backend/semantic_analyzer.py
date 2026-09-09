from typing import List, Dict
from models import Token, SymbolEntry, SemanticIssue

class SemanticAnalyzer:
    def __init__(self, tokens: List[Token], symbol_table: List[SymbolEntry]):
        self.tokens = tokens
        self.symbol_table = symbol_table
        self.issues: List[SemanticIssue] = []

    def analyze(self) -> List[SemanticIssue]:
        self.issues = []
        declared_names = {entry.name for entry in self.symbol_table if entry.status == "Declared"}

        # 1. Check for redeclarations recorded in symbol table
        for entry in self.symbol_table:
            if "Redeclared" in entry.status:
                self.issues.append(SemanticIssue(
                    line=entry.line,
                    column=1,
                    message=f"Redeclaration of variable '{entry.name}' in scope '{entry.scope}'",
                    suggestion=f"Remove duplicate declaration of '{entry.name}' or rename it.",
                    issue_type="Redeclaration",
                    severity="error"
                ))

        # 2. Scan tokens for usages of identifiers that are undeclared
        # Ignore standard library functions (printf, scanf, malloc, calloc, realloc, free, main)
        BUILTINS = {"printf", "scanf", "malloc", "calloc", "realloc", "free", "main", "sizeof", "NULL", "exit"}

        for i, tok in enumerate(self.tokens):
            if tok.token_type == "IDENTIFIER" and tok.lexeme not in BUILTINS:
                # Check if this token is part of a declaration statement
                prev_tok = self.tokens[i-1] if i > 0 else None
                prev_prev_tok = self.tokens[i-2] if i > 1 else None

                is_declaration_site = False
                if prev_tok and prev_tok.token_type == "KEYWORD" and prev_tok.lexeme in ("int", "float", "double", "char", "void"):
                    is_declaration_site = True
                elif prev_tok and prev_tok.lexeme == "*" and prev_prev_tok and prev_prev_tok.lexeme in ("int", "float", "double", "char", "void"):
                    is_declaration_site = True

                if not is_declaration_site:
                    if tok.lexeme not in declared_names:
                        # Ensure we don't duplicate undeclared issue for exact same line & lexeme
                        already_reported = any(iss.line == tok.line and tok.lexeme in iss.message for iss.message in [i.message for i in self.issues])
                        if not already_reported:
                            self.issues.append(SemanticIssue(
                                line=tok.line,
                                column=tok.column,
                                message=f"Undeclared variable: '{tok.lexeme}'",
                                suggestion=f"Declare '{tok.lexeme}' (e.g., 'int {tok.lexeme};') before using it.",
                                issue_type="Undeclared Variable",
                                severity="error"
                            ))

        return self.issues
