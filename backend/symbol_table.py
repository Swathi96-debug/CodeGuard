from typing import List, Dict, Optional
from models import SymbolEntry, Token

class SymbolTableBuilder:
    def __init__(self, tokens: List[Token], ast: Dict):
        self.tokens = tokens
        self.ast = ast
        self.entries: List[SymbolEntry] = []
        self.redeclarations: List[Dict] = []

    def build(self) -> List[SymbolEntry]:
        self.entries = []
        self.redeclarations = []

        # Traversal of AST or token stream to discover variable declarations
        current_scope = "Global"
        scope_depth = 0

        i = 0
        n = len(self.tokens)
        
        while i < n:
            tok = self.tokens[i]

            # Detect function headers for scope name
            if tok.token_type == "KEYWORD" and tok.lexeme in ("int", "float", "double", "char", "void"):
                # Peek if next is function identifier
                if i + 1 < n and self.tokens[i+1].token_type == "IDENTIFIER":
                    if i + 2 < n and self.tokens[i+2].lexeme == "(":
                        current_scope = f"Function {self.tokens[i+1].lexeme}"
                        i += 3
                        continue

            # Detect variable declarations e.g. int x = 10; or int *p = malloc(100);
            if tok.token_type == "KEYWORD" and tok.lexeme in ("int", "float", "double", "char", "void"):
                var_type = tok.lexeme
                is_ptr = False
                idx = i + 1

                if idx < n and self.tokens[idx].lexeme == "*":
                    is_ptr = True
                    var_type += "*"
                    idx += 1

                if idx < n and self.tokens[idx].token_type == "IDENTIFIER":
                    var_name = self.tokens[idx].lexeme
                    decl_line = self.tokens[idx].line

                    # Check redeclaration in current scope
                    existing = [e for e in self.entries if e.name == var_name and e.scope == current_scope]
                    if existing:
                        self.entries.append(SymbolEntry(
                            name=var_name,
                            type=var_type,
                            scope=current_scope,
                            line=decl_line,
                            status="Redeclared (Error)"
                        ))
                        self.redeclarations.append({
                            "name": var_name,
                            "line": decl_line,
                            "column": self.tokens[idx].column,
                            "scope": current_scope
                        })
                    else:
                        self.entries.append(SymbolEntry(
                            name=var_name,
                            type=var_type,
                            scope=current_scope,
                            line=decl_line,
                            status="Declared"
                        ))
                    i = idx + 1
                    continue

            i += 1

        return self.entries
