from typing import List, Dict, Optional, Any
from models import Token, SymbolEntry, SemanticIssue

TYPES = {"int", "float", "double", "char", "void", "long", "short", "unsigned", "signed"}

BUILTIN_FUNCTIONS = {
    "printf", "scanf", "malloc", "calloc", "realloc", "free", "main", "exit",
    "puts", "gets", "getchar", "putchar", "strlen", "strcpy", "strcmp"
}
BUILTIN_CONSTANTS = {"NULL", "sizeof"}

class SemanticAnalyzer:
    def __init__(self, tokens: List[Token], symbol_table: List[SymbolEntry], ast: Optional[Dict[str, Any]] = None):
        self.tokens = tokens
        self.symbol_table = symbol_table
        self.ast = ast or {}
        self.issues: List[SemanticIssue] = []

    def analyze(self) -> List[SemanticIssue]:
        self.issues = []

        # 1. Track function definitions and declarations separately from variables
        declared_functions = set(BUILTIN_FUNCTIONS)
        declared_variables = set()

        # Extract functions from AST if available
        if self.ast and "statements" in self.ast:
            for stmt in self.ast.get("statements", []):
                if isinstance(stmt, dict) and stmt.get("type") == "FunctionDeclarationNode":
                    fn_name = stmt.get("name")
                    if fn_name:
                        declared_functions.add(fn_name)

        # Extract functions and variables from symbol table
        for entry in self.symbol_table:
            if "Redeclared" not in entry.status:
                if entry.type.endswith("()") or "Function" in entry.type:
                    declared_functions.add(entry.name)
                else:
                    declared_variables.add(entry.name)

        # Fallback scan of tokens for top-level function headers/prototypes
        i = 0
        n = len(self.tokens)
        while i < n:
            tok = self.tokens[i]
            if tok.token_type == "KEYWORD" and tok.lexeme in TYPES:
                idx = i + 1
                if idx < n and self.tokens[idx].lexeme == "*":
                    idx += 1
                if idx < n and self.tokens[idx].token_type == "IDENTIFIER" and idx + 1 < n and self.tokens[idx + 1].lexeme == "(":
                    declared_functions.add(self.tokens[idx].lexeme)
            i += 1

        # 2. Check for redeclarations recorded in symbol table
        for entry in self.symbol_table:
            if "Redeclared" in entry.status:
                kind = "function" if entry.type.endswith("()") else "variable"
                self.issues.append(SemanticIssue(
                    line=entry.line,
                    column=1,
                    message=f"Redeclaration of {kind} '{entry.name}' in scope '{entry.scope}'",
                    suggestion=f"Remove duplicate declaration of '{entry.name}' or rename it.",
                    issue_type="Redeclaration",
                    severity="error"
                ))

        # 3. Scan tokens for usages of identifiers
        for i, tok in enumerate(self.tokens):
            if tok.token_type == "IDENTIFIER":
                # Built-in functions, constants, or keywords
                if tok.lexeme in BUILTIN_FUNCTIONS or tok.lexeme in BUILTIN_CONSTANTS:
                    continue

                # Check if this token is at a declaration site (e.g. int x, void foo, char *str)
                prev_tok = self.tokens[i - 1] if i > 0 else None
                prev_prev_tok = self.tokens[i - 2] if i > 1 else None

                is_declaration_site = False
                if prev_tok and prev_tok.token_type == "KEYWORD" and prev_tok.lexeme in TYPES:
                    is_declaration_site = True
                elif prev_tok and prev_tok.lexeme == "*" and prev_prev_tok and prev_prev_tok.lexeme in TYPES:
                    is_declaration_site = True

                if is_declaration_site:
                    continue

                next_tok = self.tokens[i + 1] if i + 1 < len(self.tokens) else None
                is_function_call = (next_tok is not None and next_tok.lexeme == "(")

                if is_function_call:
                    # Function call: calls to previously defined/declared functions are valid
                    if tok.lexeme not in declared_functions:
                        already_reported = any(iss.line == tok.line and tok.lexeme in iss.message for iss in self.issues)
                        if not already_reported:
                            self.issues.append(SemanticIssue(
                                line=tok.line,
                                column=tok.column,
                                message=f"Undeclared function: '{tok.lexeme}'",
                                suggestion=f"Define or declare '{tok.lexeme}()' before calling it.",
                                issue_type="Undeclared Function",
                                severity="error"
                            ))
                else:
                    # Variable usage: if identifier is a known function (e.g. function pointer callback), allow it
                    if tok.lexeme not in declared_variables and tok.lexeme not in declared_functions:
                        already_reported = any(iss.line == tok.line and tok.lexeme in iss.message for iss in self.issues)
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
