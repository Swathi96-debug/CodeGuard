from typing import List, Dict, Any, Optional
from models import Token, SyntaxIssue
from ast_nodes import (
    create_program_node, create_function_decl_node, create_declaration_node,
    create_assignment_node, create_binary_expr_node, create_identifier_node,
    create_literal_node, create_function_call_node, create_if_node,
    create_while_node, create_return_node, create_block_node
)

TYPES = {"int", "float", "double", "char", "void"}

class Parser:
    def __init__(self, tokens: List[Token]):
        # Filter out preprocessor tokens for parsing
        self.tokens = [t for t in tokens if t.token_type != "PREPROCESSOR"]
        self.pos = 0
        self.length = len(self.tokens)
        self.syntax_issues: List[SyntaxIssue] = []

    def current_token(self) -> Optional[Token]:
        if self.pos < self.length:
            return self.tokens[self.pos]
        return None

    def peek_token(self, offset: int = 1) -> Optional[Token]:
        idx = self.pos + offset
        if idx < self.length:
            return self.tokens[idx]
        return None

    def advance(self) -> Optional[Token]:
        tok = self.current_token()
        if self.pos < self.length:
            self.pos += 1
        return tok

    def match(self, token_type: str, lexeme: Optional[str] = None) -> bool:
        tok = self.current_token()
        if not tok:
            return False
        if tok.token_type != token_type:
            return False
        if lexeme is not None and tok.lexeme != lexeme:
            return False
        return True

    def consume(self, token_type: str, lexeme: Optional[str] = None, error_msg: str = "", suggestion: str = "") -> Optional[Token]:
        tok = self.current_token()
        if tok and self.match(token_type, lexeme):
            return self.advance()
        
        # Report syntax error
        line = tok.line if tok else (self.tokens[-1].line if self.tokens else 1)
        col = tok.column if tok else (self.tokens[-1].column if self.tokens else 1)
        
        msg = error_msg or f"Expected '{lexeme if lexeme else token_type}', got '{tok.lexeme if tok else 'EOF'}'"
        sugg = suggestion or f"Add '{lexeme if lexeme else token_type}'"
        
        self.syntax_issues.append(SyntaxIssue(
            line=line,
            column=col,
            message=msg,
            suggestion=sugg,
            severity="error"
        ))
        return None

    def parse(self) -> Dict[str, Any]:
        statements = []
        while self.current_token() is not None:
            stmt = self.parse_top_level_or_statement()
            if stmt:
                statements.append(stmt)
            else:
                # Synchronize parser after error
                self.advance()
        return create_program_node(statements)

    def parse_top_level_or_statement(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        # Function declaration or variable declaration starting with type
        if tok.token_type == "KEYWORD" and tok.lexeme in TYPES:
            # Lookahead to check if it's function declaration e.g. int main() {
            p1 = self.peek_token(1)
            p2 = self.peek_token(2)
            p3 = self.peek_token(3)

            # Check if pointer type like int *p
            if p1 and p1.lexeme == '*' and p2 and p2.token_type == "IDENTIFIER" and p3 and p3.lexeme == '(':
                return self.parse_function_declaration()
            elif p1 and p1.token_type == "IDENTIFIER" and p2 and p2.lexeme == '(':
                return self.parse_function_declaration()
            else:
                return self.parse_declaration()

        return self.parse_statement()

    def parse_function_declaration(self) -> Optional[Dict[str, Any]]:
        ret_type_tok = self.advance()
        is_ptr = False
        if self.match("OPERATOR", "*"):
            is_ptr = True
            self.advance()
        
        name_tok = self.consume("IDENTIFIER", error_msg="Expected function name")
        func_name = name_tok.lexeme if name_tok else "unknown"
        line = ret_type_tok.line if ret_type_tok else 1

        self.consume("SEPARATOR", "(", error_msg="Expected '(' after function name")
        
        # Parse params (simplified: skip until ')')
        while self.current_token() and not self.match("SEPARATOR", ")"):
            self.advance()
        
        if not self.match("SEPARATOR", ")"):
            self.syntax_issues.append(SyntaxIssue(
                line=self.tokens[self.pos-1].line if self.pos > 0 else 1,
                column=self.tokens[self.pos-1].column if self.pos > 0 else 1,
                message="Missing closing parenthesis ')' in function signature",
                suggestion="Add ')' to close parameters",
                severity="error"
            ))
        else:
            self.advance()

        # Parse block
        body = self.parse_block()
        ret_type_str = ret_type_tok.lexeme + ("*" if is_ptr else "") if ret_type_tok else "int"
        return create_function_decl_node(ret_type_str, func_name, body or create_block_node([], line), line)

    def parse_statement(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        if tok.lexeme == '{':
            return self.parse_block()
        if tok.lexeme == 'if':
            return self.parse_if_statement()
        if tok.lexeme == 'while':
            return self.parse_while_statement()
        if tok.lexeme == 'return':
            return self.parse_return_statement()
        if tok.token_type == "KEYWORD" and tok.lexeme in TYPES:
            return self.parse_declaration()
        
        # Could be assignment or function call or standalone expression
        if tok.token_type == "IDENTIFIER":
            next_tok = self.peek_token(1)
            if next_tok and next_tok.lexeme == '(':
                call_node = self.parse_function_call()
                self.check_semicolon()
                return call_node
            elif next_tok and next_tok.lexeme == '=':
                return self.parse_assignment()

        # Fallback parse expression statement
        expr = self.parse_expression()
        self.check_semicolon()
        return expr

    def parse_declaration(self) -> Optional[Dict[str, Any]]:
        type_tok = self.advance()
        is_ptr = False
        if self.match("OPERATOR", "*"):
            is_ptr = True
            self.advance()

        name_tok = self.consume("IDENTIFIER", error_msg="Expected identifier in variable declaration")
        var_name = name_tok.lexeme if name_tok else "var"
        line = type_tok.line if type_tok else 1

        initializer = None
        if self.match("OPERATOR", "="):
            self.advance()
            initializer = self.parse_expression()

        # Expect semicolon
        self.check_semicolon()

        return create_declaration_node(type_tok.lexeme if type_tok else "int", var_name, is_ptr, initializer, line)

    def parse_assignment(self) -> Optional[Dict[str, Any]]:
        target_tok = self.advance()
        self.consume("OPERATOR", "=", error_msg="Expected '=' in assignment")
        val_expr = self.parse_expression()
        self.check_semicolon()
        return create_assignment_node(target_tok.lexeme if target_tok else "var", val_expr, target_tok.line if target_tok else 1)

    def parse_if_statement(self) -> Optional[Dict[str, Any]]:
        if_tok = self.advance()
        self.consume("SEPARATOR", "(", error_msg="Expected '(' after 'if'", suggestion="Add '(' after 'if'")
        cond = self.parse_expression()
        
        if not self.match("SEPARATOR", ")"):
            self.syntax_issues.append(SyntaxIssue(
                line=self.tokens[self.pos-1].line if self.pos > 0 else if_tok.line,
                column=self.tokens[self.pos-1].column if self.pos > 0 else if_tok.column,
                message="Missing closing parenthesis ')' in condition",
                suggestion="Add ')' after condition",
                severity="error"
            ))
        else:
            self.advance()

        then_branch = self.parse_statement()
        else_branch = None

        if self.match("KEYWORD", "else"):
            self.advance()
            else_branch = self.parse_statement()

        return create_if_node(cond, then_branch, else_branch, if_tok.line)

    def parse_while_statement(self) -> Optional[Dict[str, Any]]:
        while_tok = self.advance()
        self.consume("SEPARATOR", "(", error_msg="Expected '(' after 'while'", suggestion="Add '(' after 'while'")
        cond = self.parse_expression()
        if not self.match("SEPARATOR", ")"):
            self.syntax_issues.append(SyntaxIssue(
                line=self.tokens[self.pos-1].line if self.pos > 0 else while_tok.line,
                column=self.tokens[self.pos-1].column if self.pos > 0 else while_tok.column,
                message="Missing closing parenthesis ')' in condition",
                suggestion="Add ')' after condition",
                severity="error"
            ))
        else:
            self.advance()

        body = self.parse_statement()
        return create_while_node(cond, body, while_tok.line)

    def parse_return_statement(self) -> Optional[Dict[str, Any]]:
        ret_tok = self.advance()
        val = None
        if not self.match("SEPARATOR", ";"):
            val = self.parse_expression()
        self.check_semicolon()
        return create_return_node(val, ret_tok.line)

    def parse_block(self) -> Optional[Dict[str, Any]]:
        brace_tok = self.consume("SEPARATOR", "{", error_msg="Expected '{' at start of block")
        line = brace_tok.line if brace_tok else 1
        stmts = []

        while self.current_token() and not self.match("SEPARATOR", "}"):
            s = self.parse_statement()
            if s:
                stmts.append(s)

        if not self.match("SEPARATOR", "}"):
            self.syntax_issues.append(SyntaxIssue(
                line=self.tokens[self.pos-1].line if self.pos > 0 else line,
                column=self.tokens[self.pos-1].column if self.pos > 0 else 1,
                message="Missing closing brace '}'",
                suggestion="Add '}' at end of block",
                severity="error"
            ))
        else:
            self.advance()

        return create_block_node(stmts, line)

    def parse_function_call(self) -> Optional[Dict[str, Any]]:
        name_tok = self.advance()
        self.consume("SEPARATOR", "(", error_msg="Expected '(' in function call")
        args = []
        if not self.match("SEPARATOR", ")"):
            args.append(self.parse_expression())
            while self.match("SEPARATOR", ","):
                self.advance()
                args.append(self.parse_expression())

        if not self.match("SEPARATOR", ")"):
            self.syntax_issues.append(SyntaxIssue(
                line=name_tok.line,
                column=name_tok.column,
                message="Missing closing parenthesis ')' in function call",
                suggestion="Add ')' at end of arguments",
                severity="error"
            ))
        else:
            self.advance()

        return create_function_call_node(name_tok.lexeme, args, name_tok.line)

    def parse_expression(self) -> Optional[Dict[str, Any]]:
        return self.parse_comparison_expression()

    def parse_comparison_expression(self) -> Optional[Dict[str, Any]]:
        left = self.parse_additive_expression()
        while self.current_token() and self.current_token().lexeme in ("==", "!=", "<", ">", "<=", ">="):
            op_tok = self.advance()
            right = self.parse_additive_expression()
            left = create_binary_expr_node(op_tok.lexeme, left, right, op_tok.line)
        return left

    def parse_additive_expression(self) -> Optional[Dict[str, Any]]:
        left = self.parse_multiplicative_expression()
        while self.current_token() and self.current_token().lexeme in ("+", "-"):
            op_tok = self.advance()
            right = self.parse_multiplicative_expression()
            left = create_binary_expr_node(op_tok.lexeme, left, right, op_tok.line)
        return left

    def parse_multiplicative_expression(self) -> Optional[Dict[str, Any]]:
        left = self.parse_factor()
        while self.current_token() and self.current_token().lexeme in ("*", "/", "%"):
            op_tok = self.advance()
            right = self.parse_factor()
            left = create_binary_expr_node(op_tok.lexeme, left, right, op_tok.line)
        return left

    def parse_factor(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        if tok.lexeme == '(':
            self.advance()
            expr = self.parse_expression()
            if not self.match("SEPARATOR", ")"):
                self.syntax_issues.append(SyntaxIssue(
                    line=tok.line,
                    column=tok.column,
                    message="Missing closing parenthesis ')'",
                    suggestion="Add ')' after expression",
                    severity="error"
                ))
            else:
                self.advance()
            return expr

        if tok.token_type == "IDENTIFIER":
            next_tok = self.peek_token(1)
            if next_tok and next_tok.lexeme == '(':
                return self.parse_function_call()
            self.advance()
            return create_identifier_node(tok.lexeme, tok.line)

        if tok.token_type in ("INT_CONSTANT", "FLOAT_CONSTANT", "STRING_LITERAL", "CHAR_LITERAL"):
            self.advance()
            return create_literal_node(tok.lexeme, tok.token_type, tok.line)

        # Unexpected token factor
        self.advance()
        return create_literal_node(tok.lexeme, "UNKNOWN", tok.line)

    def check_semicolon(self):
        tok = self.current_token()
        if tok and tok.lexeme == ';':
            self.advance()
        else:
            prev_tok = self.tokens[self.pos - 1] if self.pos > 0 else None
            line = prev_tok.line if prev_tok else 1
            col = (prev_tok.column + len(prev_tok.lexeme)) if prev_tok else 1
            self.syntax_issues.append(SyntaxIssue(
                line=line,
                column=col,
                message="Missing semicolon ';'",
                suggestion="Add ';' at the end of the statement",
                severity="error"
            ))
