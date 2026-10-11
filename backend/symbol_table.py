from typing import List, Dict, Optional, Any
from models import SymbolEntry, Token

TYPES = {"int", "float", "double", "char", "void", "long", "short", "unsigned", "signed"}

class SymbolTableBuilder:
    def __init__(self, tokens: List[Token], ast: Optional[Dict[str, Any]] = None):
        self.tokens = tokens
        self.ast = ast or {}
        self.entries: List[SymbolEntry] = []
        self.redeclarations: List[Dict[str, Any]] = []

    def build(self) -> List[SymbolEntry]:
        self.entries = []
        self.redeclarations = []

        # 1. Register function declarations / definitions from AST if available
        declared_function_names = set()
        if self.ast and "statements" in self.ast:
            for stmt in self.ast.get("statements", []):
                if isinstance(stmt, dict) and stmt.get("type") == "FunctionDeclarationNode":
                    fn_name = stmt.get("name")
                    ret_type = stmt.get("return_type", "int")
                    line = stmt.get("line", 1)
                    if fn_name and fn_name not in declared_function_names:
                        declared_function_names.add(fn_name)
                        self.entries.append(SymbolEntry(
                            name=fn_name,
                            type=f"{ret_type}()",
                            scope="Global",
                            line=line,
                            status="Declared"
                        ))

        # 2. Token traversal for function scopes and variable declarations
        current_scope = "Global"
        scope_depth = 0

        i = 0
        n = len(self.tokens)

        while i < n:
            tok = self.tokens[i]

            # Track brace depth for scope management
            if tok.lexeme == "{":
                scope_depth += 1
                if scope_depth > 1 and current_scope != "Global":
                    base_fn = current_scope.split(" (Block")[0]
                    current_scope = f"{base_fn} (Block {scope_depth})"
                i += 1
                continue
            elif tok.lexeme == "}":
                scope_depth = max(0, scope_depth - 1)
                if scope_depth == 0:
                    current_scope = "Global"
                elif scope_depth == 1 and current_scope != "Global":
                    base_fn = current_scope.split(" (Block")[0]
                    current_scope = base_fn
                elif scope_depth > 1 and current_scope != "Global":
                    base_fn = current_scope.split(" (Block")[0]
                    current_scope = f"{base_fn} (Block {scope_depth})"
                i += 1
                continue

            # Detect function header
            if tok.token_type == "KEYWORD" and tok.lexeme in TYPES:
                var_type = tok.lexeme
                is_ptr = False
                idx = i + 1

                if idx < n and self.tokens[idx].lexeme == "*":
                    is_ptr = True
                    var_type += "*"
                    idx += 1

                if idx < n and self.tokens[idx].token_type == "IDENTIFIER" and idx + 1 < n and self.tokens[idx + 1].lexeme == "(":
                    func_name = self.tokens[idx].lexeme
                    func_line = self.tokens[idx].line
                    current_scope = f"Function {func_name}"

                    # If not already registered via AST, add to entries
                    if func_name not in declared_function_names:
                        declared_function_names.add(func_name)
                        self.entries.append(SymbolEntry(
                            name=func_name,
                            type=f"{var_type}()",
                            scope="Global",
                            line=func_line,
                            status="Declared"
                        ))

                    # Parse parameters inside '(' ... ')'
                    idx += 2
                    param_depth = 1
                    while idx < n and param_depth > 0:
                        if self.tokens[idx].lexeme == "(":
                            param_depth += 1
                        elif self.tokens[idx].lexeme == ")":
                            param_depth -= 1
                            if param_depth == 0:
                                idx += 1
                                break
                        elif self.tokens[idx].token_type == "KEYWORD" and self.tokens[idx].lexeme in TYPES:
                            p_type = self.tokens[idx].lexeme
                            p_idx = idx + 1
                            if p_idx < n and self.tokens[p_idx].lexeme == "*":
                                p_type += "*"
                                p_idx += 1
                            if p_idx < n and self.tokens[p_idx].token_type == "IDENTIFIER":
                                p_name = self.tokens[p_idx].lexeme
                                p_line = self.tokens[p_idx].line
                                self.entries.append(SymbolEntry(
                                    name=p_name,
                                    type=p_type,
                                    scope=current_scope,
                                    line=p_line,
                                    status="Declared"
                                ))
                                idx = p_idx
                        idx += 1
                    i = idx
                    continue

                # Detect variable declaration
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
