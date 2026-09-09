from typing import Any, Dict, List, Optional

def create_program_node(statements: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "type": "ProgramNode",
        "label": "Program",
        "statements": statements,
        "line": 1
    }

def create_function_decl_node(return_type: str, name: str, body: Dict[str, Any], line: int) -> Dict[str, Any]:
    return {
        "type": "FunctionDeclarationNode",
        "label": f"Function {name} ({return_type})",
        "name": name,
        "return_type": return_type,
        "body": body,
        "line": line
    }

def create_declaration_node(var_type: str, name: str, is_pointer: bool, initializer: Optional[Dict[str, Any]], line: int) -> Dict[str, Any]:
    label_type = f"{var_type}{'*' if is_pointer else ''}"
    return {
        "type": "DeclarationNode",
        "label": f"Declaration: {label_type} {name}",
        "var_type": var_type,
        "is_pointer": is_pointer,
        "name": name,
        "initializer": initializer,
        "line": line
    }

def create_assignment_node(target: str, value: Dict[str, Any], line: int) -> Dict[str, Any]:
    return {
        "type": "AssignmentNode",
        "label": f"Assignment: {target} =",
        "target": target,
        "value": value,
        "line": line
    }

def create_binary_expr_node(operator: str, left: Dict[str, Any], right: Dict[str, Any], line: int) -> Dict[str, Any]:
    return {
        "type": "BinaryExpressionNode",
        "label": f"BinaryOp ({operator})",
        "operator": operator,
        "left": left,
        "right": right,
        "line": line
    }

def create_identifier_node(name: str, line: int) -> Dict[str, Any]:
    return {
        "type": "IdentifierNode",
        "label": f"Identifier ({name})",
        "name": name,
        "line": line
    }

def create_literal_node(value: str, lit_type: str, line: int) -> Dict[str, Any]:
    return {
        "type": "LiteralNode",
        "label": f"Literal ({value})",
        "value": value,
        "literal_type": lit_type,
        "line": line
    }

def create_function_call_node(name: str, args: List[Dict[str, Any]], line: int) -> Dict[str, Any]:
    return {
        "type": "FunctionCallNode",
        "label": f"Call: {name}()",
        "name": name,
        "args": args,
        "line": line
    }

def create_if_node(condition: Dict[str, Any], then_branch: Dict[str, Any], else_branch: Optional[Dict[str, Any]], line: int) -> Dict[str, Any]:
    return {
        "type": "IfNode",
        "label": "If Statement",
        "condition": condition,
        "then_branch": then_branch,
        "else_branch": else_branch,
        "line": line
    }

def create_while_node(condition: Dict[str, Any], body: Dict[str, Any], line: int) -> Dict[str, Any]:
    return {
        "type": "WhileNode",
        "label": "While Loop",
        "condition": condition,
        "body": body,
        "line": line
    }

def create_return_node(value: Optional[Dict[str, Any]], line: int) -> Dict[str, Any]:
    return {
        "type": "ReturnNode",
        "label": "Return",
        "value": value,
        "line": line
    }

def create_block_node(statements: List[Dict[str, Any]], line: int) -> Dict[str, Any]:
    return {
        "type": "BlockNode",
        "label": "Block {...}",
        "statements": statements,
        "line": line
    }
