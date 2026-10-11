from typing import Dict, Any, List, Optional
from models import FunctionComplexity, Token

class ComplexityAnalyzer:
    """
    Computes code complexity metrics:
    - Cyclomatic Complexity (McCabe):
        Base = 1 per function.
        +1 for each decision point: if, while, for, do-while, and logical operators (&&, ||).
    - Statement Count: Total executable statements in function body.
    - Max Nesting Depth: Peak nesting depth of control flow blocks.
    - Complexity Rating:
        1 - 5: "LOW"
        6 - 10: "MODERATE"
        > 10: "HIGH"
    """

    def __init__(self, ast: Optional[Dict[str, Any]], tokens: Optional[List[Token]] = None):
        self.ast = ast or {}
        self.tokens = tokens or []

    def analyze(self) -> List[FunctionComplexity]:
        results: List[FunctionComplexity] = []
        if not self.ast or self.ast.get("type") != "ProgramNode":
            return results

        statements = self.ast.get("statements", [])
        functions = [s for s in statements if s.get("type") == "FunctionDeclarationNode" and s.get("body") is not None]

        if functions:
            for func in functions:
                metrics = self._analyze_function(func)
                results.append(metrics)
        elif statements:
            # Code without explicit function declarations (e.g. top-level statements)
            top_level_block = {"type": "BlockNode", "statements": statements, "line": 1}
            pseudo_func = {
                "name": "<global>",
                "line": 1,
                "body": top_level_block
            }
            results.append(self._analyze_function(pseudo_func))

        return results

    def _count_logical_ops(self, node: Any) -> int:
        """Count && and || operators in an expression."""
        if not isinstance(node, dict):
            return 0
        cnt = 0
        if node.get("type") == "BinaryExpressionNode":
            if node.get("operator") in ("&&", "||"):
                cnt += 1
            cnt += self._count_logical_ops(node.get("left"))
            cnt += self._count_logical_ops(node.get("right"))
        elif node.get("type") == "UnaryExpressionNode":
            cnt += self._count_logical_ops(node.get("operand"))
        return cnt

    def _analyze_function(self, func_node: Dict[str, Any]) -> FunctionComplexity:
        name = func_node.get("name", "anonymous")
        line = func_node.get("line", 1)
        body = func_node.get("body")

        if not body:
            return FunctionComplexity(
                name=name,
                line=line,
                cyclomatic_complexity=1,
                statement_count=0,
                max_nesting_depth=0,
                rating="LOW"
            )

        cc = 1  # Base McCabe cyclomatic complexity
        stmt_count = 0
        max_depth = 0

        def traverse(node: Any, current_depth: int):
            nonlocal cc, stmt_count, max_depth
            if not isinstance(node, dict):
                return

            ntype = node.get("type")

            # Update peak nesting depth
            if current_depth > max_depth:
                max_depth = current_depth

            # Count executable statements (BlockNode itself is not an atomic statement)
            if ntype in (
                "DeclarationNode", "AssignmentNode", "IfNode", "WhileNode",
                "ForNode", "DoWhileNode", "ReturnNode", "BreakNode",
                "ContinueNode", "FunctionCallNode"
            ):
                stmt_count += 1

            # Decision points for Cyclomatic Complexity
            if ntype == "IfNode":
                cc += 1
                cc += self._count_logical_ops(node.get("condition"))
                traverse(node.get("then_branch"), current_depth + 1)
                if node.get("else_branch"):
                    else_br = node.get("else_branch")
                    # An 'else if' is an IfNode: it contributes its own decision point and depth
                    if else_br.get("type") == "IfNode":
                        traverse(else_br, current_depth)
                    else:
                        traverse(else_br, current_depth + 1)
                return

            elif ntype in ("WhileNode", "DoWhileNode"):
                cc += 1
                cc += self._count_logical_ops(node.get("condition"))
                traverse(node.get("body"), current_depth + 1)
                return

            elif ntype == "ForNode":
                cc += 1
                cc += self._count_logical_ops(node.get("condition"))
                traverse(node.get("init"), current_depth)
                traverse(node.get("increment"), current_depth)
                traverse(node.get("body"), current_depth + 1)
                return

            elif ntype == "BlockNode":
                for child in node.get("statements", []):
                    traverse(child, current_depth)
                return

            # Check expressions for logical operators if found in other expressions (e.g. assignment x = a && b;)
            if ntype == "BinaryExpressionNode":
                op = node.get("operator")
                if op in ("&&", "||"):
                    cc += 1
                traverse(node.get("left"), current_depth)
                traverse(node.get("right"), current_depth)
                return

            # Generic traversal for remaining child nodes
            for k, v in node.items():
                if k in ("type", "label", "line", "name", "operator", "var_type", "is_pointer", "value", "literal_type"):
                    continue
                if isinstance(v, dict):
                    traverse(v, current_depth)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            traverse(item, current_depth)

        # Function body top-level starts at depth 1
        if body.get("type") == "BlockNode":
            for stmt in body.get("statements", []):
                traverse(stmt, 1)
        else:
            traverse(body, 1)

        # Rating determination
        if cc <= 5:
            rating = "LOW"
        elif cc <= 10:
            rating = "MODERATE"
        else:
            rating = "HIGH"

        return FunctionComplexity(
            name=name,
            line=line,
            cyclomatic_complexity=cc,
            statement_count=stmt_count,
            max_nesting_depth=max_depth,
            rating=rating
        )
