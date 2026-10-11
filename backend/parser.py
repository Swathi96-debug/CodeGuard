from typing import List, Dict, Any, Optional
from models import Token, SyntaxIssue
from ast_nodes import (
    create_program_node, create_function_decl_node, create_declaration_node,
    create_assignment_node, create_binary_expr_node, create_identifier_node,
    create_literal_node, create_function_call_node, create_if_node,
    create_while_node, create_for_node, create_do_while_node,
    create_break_node, create_continue_node, create_unary_expr_node,
    create_return_node, create_block_node
)

TYPES = {"int", "float", "double", "char", "void", "long", "short", "unsigned", "signed"}

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
                # If None returned (e.g. empty statement ';'), advance if still on the same token
                if self.current_token() and self.current_token().lexeme == ';':
                    self.advance()
                elif self.current_token() is not None:
                    # Synchronize parser after error
                    self.advance()
        return create_program_node(statements)

    def parse_top_level_or_statement(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        # Function declaration or variable declaration starting with type
        if tok.token_type == "KEYWORD" and tok.lexeme in TYPES:
            # Lookahead to check if it's function declaration e.g. int main() { or int *func() {
            p1 = self.peek_token(1)
            p2 = self.peek_token(2)
            p3 = self.peek_token(3)

            # Check if pointer return type like int *func(
            if p1 and p1.lexeme == '*' and p2 and p2.token_type == "IDENTIFIER" and p3 and p3.lexeme == '(':
                return self.parse_function_declaration()
            elif p1 and p1.token_type == "IDENTIFIER" and p2 and p2.lexeme == '(':
                return self.parse_function_declaration()
            else:
                return self.parse_declaration(expect_semicolon=True)

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
        
        # Parse params
        params = []
        while self.current_token() and not self.match("SEPARATOR", ")"):
            tok = self.current_token()
            if tok.token_type == "IDENTIFIER" and tok.lexeme not in TYPES:
                params.append(tok.lexeme)
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

        ret_type_str = (ret_type_tok.lexeme if ret_type_tok else "int") + ("*" if is_ptr else "")

        # Check for function prototype e.g. int add(int a, int b);
        if self.match("SEPARATOR", ";"):
            self.advance()
            return create_function_decl_node(ret_type_str, func_name, None, line, params=params)

        # Parse block
        body = self.parse_block()
        return create_function_decl_node(ret_type_str, func_name, body or create_block_node([], line), line, params=params)

    def parse_statement(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        # 1. Block statement
        if tok.lexeme == '{':
            return self.parse_block()

        # 2. Control flow statements
        if tok.lexeme == 'if':
            return self.parse_if_statement()
        if tok.lexeme == 'while':
            return self.parse_while_statement()
        if tok.lexeme == 'for':
            return self.parse_for_statement()
        if tok.lexeme == 'do':
            return self.parse_do_while_statement()

        # 3. Jump statements
        if tok.lexeme == 'return':
            return self.parse_return_statement()
        if tok.lexeme == 'break':
            b_tok = self.advance()
            self.check_semicolon()
            return create_break_node(b_tok.line)
        if tok.lexeme == 'continue':
            c_tok = self.advance()
            self.check_semicolon()
            return create_continue_node(c_tok.line)

        # 4. Solitary semicolon (empty statement)
        if tok.lexeme == ';':
            self.advance()
            return None

        # 5. Variable declaration
        if tok.token_type == "KEYWORD" and tok.lexeme in TYPES:
            return self.parse_declaration(expect_semicolon=True)

        # 6. Pointer dereference assignment e.g. *ptr = expr;
        if tok.lexeme == '*':
            p1 = self.peek_token(1)
            p2 = self.peek_token(2)
            if p1 and p1.token_type == "IDENTIFIER" and p2 and p2.lexeme in ("=", "+=", "-=", "*=", "/=", "%="):
                self.advance()  # consume '*'
                target = self.advance()  # consume identifier
                op = self.advance()  # consume '=' or compound operator
                val = self.parse_expression()
                self.check_semicolon()
                return create_assignment_node(f"*{target.lexeme}", val, tok.line)

        # 7. Assignment statement e.g. x = expr; or x += expr;
        if tok.token_type == "IDENTIFIER":
            p1 = self.peek_token(1)
            if p1 and p1.lexeme in ("=", "+=", "-=", "*=", "/=", "%="):
                return self.parse_assignment()

        # 8. Expression statement (function calls func(...);, post/pre increments i++;, etc.)
        expr = self.parse_expression()
        self.check_semicolon()
        return expr

    def parse_declaration(self, expect_semicolon: bool = True) -> Optional[Dict[str, Any]]:
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

        if expect_semicolon:
            self.check_semicolon()

        return create_declaration_node(type_tok.lexeme if type_tok else "int", var_name, is_ptr, initializer, line)

    def parse_assignment(self) -> Optional[Dict[str, Any]]:
        target_tok = self.advance()
        op_tok = self.advance()
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

    def parse_for_statement(self) -> Optional[Dict[str, Any]]:
        for_tok = self.advance()
        self.consume("SEPARATOR", "(", error_msg="Expected '(' after 'for'", suggestion="Add '(' after 'for'")

        # 1. Parse initialization (can be declaration, assignment, expression, or empty)
        init = None
        if self.match("SEPARATOR", ";"):
            self.advance()  # Empty init
        elif self.current_token() and self.current_token().token_type == "KEYWORD" and self.current_token().lexeme in TYPES:
            init = self.parse_declaration(expect_semicolon=True)  # Consumes the first ';'
        else:
            if (self.current_token() and self.current_token().token_type == "IDENTIFIER" and 
                self.peek_token(1) and self.peek_token(1).lexeme in ("=", "+=", "-=", "*=", "/=", "%=")):
                init = self.parse_assignment()  # Consumes the first ';'
            else:
                init = self.parse_expression()
                self.consume("SEPARATOR", ";", error_msg="Expected ';' after for-loop initialization", suggestion="Add ';' after initialization")

        # 2. Parse condition (can be expression or empty)
        cond = None
        if self.match("SEPARATOR", ";"):
            self.advance()  # Empty condition
        else:
            cond = self.parse_expression()
            self.consume("SEPARATOR", ";", error_msg="Expected ';' after for-loop condition", suggestion="Add ';' after condition")

        # 3. Parse increment / step (can be assignment, unary expression, or empty)
        increment = None
        if not self.match("SEPARATOR", ")"):
            if (self.current_token() and self.current_token().token_type == "IDENTIFIER" and 
                self.peek_token(1) and self.peek_token(1).lexeme in ("=", "+=", "-=", "*=", "/=", "%=")):
                target_tok = self.advance()
                op_tok = self.advance()
                val_expr = self.parse_expression()
                increment = create_assignment_node(target_tok.lexeme, val_expr, target_tok.line)
            else:
                increment = self.parse_expression()

        if not self.match("SEPARATOR", ")"):
            self.syntax_issues.append(SyntaxIssue(
                line=for_tok.line,
                column=for_tok.column,
                message="Missing closing parenthesis ')' in for loop header",
                suggestion="Add ')' after for loop expressions",
                severity="error"
            ))
        else:
            self.advance()

        # 4. Parse body (block or single statement)
        body = self.parse_statement()
        return create_for_node(init, cond, increment, body, for_tok.line)

    def parse_do_while_statement(self) -> Optional[Dict[str, Any]]:
        do_tok = self.advance()
        body = self.parse_statement()
        self.consume("KEYWORD", "while", error_msg="Expected 'while' after 'do' body", suggestion="Add 'while' keyword")
        self.consume("SEPARATOR", "(", error_msg="Expected '(' after 'while'", suggestion="Add '(' after 'while'")
        cond = self.parse_expression()
        self.consume("SEPARATOR", ")", error_msg="Expected ')' after do-while condition", suggestion="Add ')' after condition")
        self.check_semicolon()
        return create_do_while_node(body, cond, do_tok.line)

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

    # ----------------- Expression Precedence Hierarchy -----------------

    def parse_expression(self) -> Optional[Dict[str, Any]]:
        return self.parse_logical_or_expression()

    def parse_logical_or_expression(self) -> Optional[Dict[str, Any]]:
        left = self.parse_logical_and_expression()
        while self.current_token() and self.current_token().lexeme == "||":
            op_tok = self.advance()
            right = self.parse_logical_and_expression()
            left = create_binary_expr_node(op_tok.lexeme, left, right, op_tok.line)
        return left

    def parse_logical_and_expression(self) -> Optional[Dict[str, Any]]:
        left = self.parse_comparison_expression()
        while self.current_token() and self.current_token().lexeme == "&&":
            op_tok = self.advance()
            right = self.parse_comparison_expression()
            left = create_binary_expr_node(op_tok.lexeme, left, right, op_tok.line)
        return left

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
        left = self.parse_unary_expression()
        while self.current_token() and self.current_token().lexeme in ("*", "/", "%"):
            op_tok = self.advance()
            right = self.parse_unary_expression()
            left = create_binary_expr_node(op_tok.lexeme, left, right, op_tok.line)
        return left

    def parse_unary_expression(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        # Prefix unary operators: ++, --, !, ~, &, +, -, *
        if tok.lexeme in ("++", "--", "!", "~", "&") or (tok.token_type == "OPERATOR" and tok.lexeme in ("+", "-", "*")):
            op_tok = self.advance()
            operand = self.parse_unary_expression()
            return create_unary_expr_node(op_tok.lexeme, operand, is_prefix=True, line=op_tok.line)

        # sizeof operator
        if tok.lexeme == "sizeof":
            sz_tok = self.advance()
            if self.match("SEPARATOR", "("):
                self.advance()
                if self.current_token() and self.current_token().lexeme in TYPES:
                    t_tok = self.advance()
                    operand = create_identifier_node(t_tok.lexeme, t_tok.line)
                else:
                    operand = self.parse_expression()
                self.consume("SEPARATOR", ")", error_msg="Expected ')' after sizeof")
            else:
                operand = self.parse_unary_expression()
            return create_unary_expr_node("sizeof", operand, is_prefix=True, line=sz_tok.line)

        return self.parse_postfix_expression()

    def parse_postfix_expression(self) -> Optional[Dict[str, Any]]:
        expr = self.parse_primary()
        while self.current_token():
            tok = self.current_token()
            # Postfix increment / decrement: expr++ / expr--
            if tok.lexeme in ("++", "--"):
                op_tok = self.advance()
                expr = create_unary_expr_node(op_tok.lexeme, expr, is_prefix=False, line=op_tok.line)
            # Array index: expr[index]
            elif tok.lexeme == "[":
                self.advance()
                index_expr = self.parse_expression()
                self.consume("SEPARATOR", "]", error_msg="Expected ']' after array index")
                expr = create_binary_expr_node("[]", expr, index_expr, tok.line)
            # Struct pointer / member access: expr->field, expr.field
            elif tok.lexeme in ("->", "."):
                op_tok = self.advance()
                member_tok = self.consume("IDENTIFIER", error_msg="Expected member identifier")
                member_node = create_identifier_node(member_tok.lexeme if member_tok else "", op_tok.line)
                expr = create_binary_expr_node(op_tok.lexeme, expr, member_node, op_tok.line)
            else:
                break
        return expr

    def parse_primary(self) -> Optional[Dict[str, Any]]:
        tok = self.current_token()
        if not tok:
            return None

        # Parenthesized expression or type cast: ( expr ) or ( type * ) expr
        if tok.lexeme == '(':
            p1 = self.peek_token(1)
            p2 = self.peek_token(2)
            p3 = self.peek_token(3)
            if p1 and p1.token_type == "KEYWORD" and p1.lexeme in TYPES:
                if p2 and p2.lexeme == '*' and p3 and p3.lexeme == ')':
                    # Typecast with pointer e.g. (int *) or (char *)
                    self.advance()  # '('
                    self.advance()  # type
                    self.advance()  # '*'
                    self.advance()  # ')'
                    return self.parse_unary_expression()
                elif p2 and p2.lexeme == ')':
                    # Value typecast e.g. (int) or (float)
                    self.advance()  # '('
                    self.advance()  # type
                    self.advance()  # ')'
                    return self.parse_unary_expression()

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

        # Function call or standalone identifier
        if tok.token_type == "IDENTIFIER":
            next_tok = self.peek_token(1)
            if next_tok and next_tok.lexeme == '(':
                return self.parse_function_call()
            self.advance()
            return create_identifier_node(tok.lexeme, tok.line)

        # Literals & constants
        if tok.token_type in ("INT_CONSTANT", "FLOAT_CONSTANT", "STRING_LITERAL", "CHAR_LITERAL"):
            self.advance()
            return create_literal_node(tok.lexeme, tok.token_type, tok.line)

        # NULL macro representation
        if tok.lexeme == "NULL":
            self.advance()
            return create_literal_node("NULL", "IDENTIFIER", tok.line)

        # Unexpected token
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
