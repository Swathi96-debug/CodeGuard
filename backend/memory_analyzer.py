import re
from typing import List, Dict, Optional, Any, Set, Tuple
from models import Token, MemoryAllocation, SymbolEntry
from parser import Parser

class AllocationInstance:
    """Represents a unique heap memory allocation identity with provenance and path tracking."""
    def __init__(self, alloc_id: str, fn: str, line: int, target_ptr: str, col: int = 1):
        self.alloc_id = alloc_id
        self.allocation_function = fn
        self.allocation_line = line
        self.column = col
        self.target_ptr = target_ptr
        self.freed = False
        self.free_line: Optional[int] = None
        self.escaped = False
        self.status = "POSSIBLE LEAK"
        self.severity = "warning"
        # Set of active pointer variable names that currently reference this allocation
        self.owners: Set[str] = {target_ptr} if target_ptr and target_ptr != "unknown_ptr" else set()
        self.realloc_from: Optional[str] = None
        self.was_reallocated: bool = False
        self.is_conditional: bool = False
        self.path_outcomes: List[str] = []  # "SAFE", "ESCAPED", "LEAK"

class PathState:
    """Represents the memory state (pointer environment and allocation status) along a control flow path."""
    def __init__(self):
        self.env: Dict[str, Optional[str]] = {}
        # alloc_id -> dict with keys: freed, free_line, escaped, owners, was_reallocated, realloc_from, leaked
        self.alloc_states: Dict[str, Dict[str, Any]] = {}
        self.scopes: List[Set[str]] = [set()]
        self.returned: bool = False
        self.return_line: Optional[int] = None
        self.broken: bool = False
        self.continued: bool = False
        self.path_completed: bool = False

    def clone(self) -> 'PathState':
        cp = PathState()
        cp.env = dict(self.env)
        cp.alloc_states = {
            aid: {
                "freed": st["freed"],
                "free_line": st["free_line"],
                "escaped": st["escaped"],
                "owners": set(st["owners"]),
                "was_reallocated": st.get("was_reallocated", False),
                "realloc_from": st.get("realloc_from"),
                "leaked": st.get("leaked", False),
                "maybe_freed": st.get("maybe_freed", False)
            }
            for aid, st in self.alloc_states.items()
        }
        cp.scopes = [set(s) for s in self.scopes]
        cp.returned = self.returned
        cp.return_line = self.return_line
        cp.broken = self.broken
        cp.continued = self.continued
        cp.path_completed = False
        return cp

class MemoryAnalyzer:
    """
    Structured C Memory Safety Analyzer (Phase 3A, Milestone 4: Control-Flow Analysis).
    Tracks allocation provenance across malloc, calloc, realloc, pointer aliasing,
    conditional branches (if/else), loops (while, for, do-while), early exits (return, break, continue),
    and nested scope blocks.
    """
    def __init__(
        self,
        tokens: List[Token],
        ast: Optional[Dict[str, Any]] = None,
        symbol_table: Optional[List[SymbolEntry]] = None
    ):
        self.tokens = tokens
        self.symbol_table = symbol_table or []
        self.alloc_records: Dict[str, AllocationInstance] = {}
        self.extra_issues: List[MemoryAllocation] = []
        self.alloc_counter = 1
        self.fn_params: Set[str] = set()
        self.in_conditional_depth = 0
        self.in_loop_depth = 0

        # Use provided AST or parse tokens to build AST
        if ast and isinstance(ast, dict) and ast.get("statements"):
            self.ast = ast
        else:
            try:
                self.ast = Parser(tokens).parse()
            except Exception:
                self.ast = {"type": "ProgramNode", "statements": []}

    def analyze(self) -> List[MemoryAllocation]:
        self.alloc_records = {}
        self.extra_issues = []
        self.alloc_counter = 1
        self.fn_params = set()
        self.global_vars: Set[str] = set()
        self.in_conditional_depth = 0
        self.in_loop_depth = 0

        # Register global variables from symbol table and AST
        for entry in self.symbol_table:
            if entry.scope == "Global" and not entry.type.endswith("()") and "Function" not in entry.type:
                self.global_vars.add(entry.name)
        if self.ast and isinstance(self.ast, dict):
            for stmt in self.ast.get("statements", []):
                if isinstance(stmt, dict) and stmt.get("type") == "DeclarationNode":
                    var_name = stmt.get("name")
                    if var_name:
                        self.global_vars.add(var_name)

        # 1. Walk AST statements
        initial_state = PathState()
        statements = self.ast.get("statements", [])
        for stmt in statements:
            self._walk_node(stmt, initial_state)

        # If top-level completed without returning (e.g. script / top-level block), record path completion
        if statements and not initial_state.returned:
            self._record_path_completion(initial_state)

        # 2. Finalize allocation status across all recorded path outcomes
        for alloc_id, alloc in self.alloc_records.items():
            if alloc.path_outcomes:
                all_safe = all(o == "SAFE" for o in alloc.path_outcomes)
                all_escaped = all(o == "ESCAPED" for o in alloc.path_outcomes)
                all_leaked = all(o == "LEAK" for o in alloc.path_outcomes)

                if all_safe:
                    alloc.status = "SAFE"
                    alloc.severity = "safe"
                    alloc.freed = True
                elif all_escaped:
                    alloc.status = "ESCAPED"
                    alloc.severity = "safe"
                    alloc.escaped = True
                    alloc.freed = False
                elif all_leaked:
                    if alloc.is_conditional or alloc.was_reallocated:
                        alloc.status = "POSSIBLE LEAK"
                        alloc.severity = "warning"
                    else:
                        alloc.status = "DEFINITE LEAK"
                        alloc.severity = "error"
                    alloc.freed = False
                else:
                    # Mixed outcomes across branches (e.g. freed on one branch, leaked on another)
                    alloc.status = "POSSIBLE LEAK"
                    alloc.severity = "warning"
                    alloc.freed = False

        # 3. If AST produced no statements (e.g. malformed or partial snippet),
        # run token fallback scan to guarantee robustness across incomplete inputs.
        if not statements and not self.alloc_records and not self.extra_issues:
            self._token_fallback_scan()

        # 4. Assemble results preserving MemoryAllocation model format
        results: List[MemoryAllocation] = []
        for alloc in self.alloc_records.values():
            results.append(MemoryAllocation(
                pointer=alloc.target_ptr,
                allocation_function=alloc.allocation_function,
                allocation_line=alloc.allocation_line,
                freed=alloc.freed,
                free_line=alloc.free_line,
                status=alloc.status,
                severity=alloc.severity
            ))

        results.extend(self.extra_issues)
        return results

    def _create_allocation(
        self, fn: str, line: int, target_ptr: str, state: PathState, is_conditional: bool = False, col: int = 1
    ) -> AllocationInstance:
        if getattr(self, "simulating_loop_carried", False):
            alloc_id = f"sim_{self.alloc_counter}"
            self.alloc_counter += 1
            inst = AllocationInstance(alloc_id, fn, line, target_ptr, col)
            state.alloc_states[alloc_id] = {
                "freed": False,
                "free_line": None,
                "escaped": False,
                "owners": {target_ptr} if target_ptr and target_ptr != "unknown_ptr" else set(),
                "was_reallocated": False,
                "realloc_from": None,
                "leaked": False
            }
            return inst

        alloc_id = f"alloc_{self.alloc_counter}"
        self.alloc_counter += 1
        inst = AllocationInstance(alloc_id, fn, line, target_ptr, col)
        inst.is_conditional = is_conditional
        self.alloc_records[alloc_id] = inst
        state.alloc_states[alloc_id] = {
            "freed": False,
            "free_line": None,
            "escaped": False,
            "owners": {target_ptr} if target_ptr and target_ptr != "unknown_ptr" else set(),
            "was_reallocated": False,
            "realloc_from": None,
            "leaked": False,
            "maybe_freed": False
        }
        return inst

    def _record_path_completion(self, state: PathState):
        """Records terminal allocation states for a completed execution path."""
        if state.path_completed:
            return
        state.path_completed = True

        for alloc_id, st in state.alloc_states.items():
            if alloc_id not in self.alloc_records:
                continue
            alloc = self.alloc_records[alloc_id]
            if st["freed"]:
                alloc.path_outcomes.append("SAFE")
            elif st["escaped"]:
                alloc.path_outcomes.append("ESCAPED")
            else:
                alloc.path_outcomes.append("LEAK")

    def _copy_state(self, src: PathState, dest: PathState):
        """Copies full state from src to dest."""
        dest.env = dict(src.env)
        dest.alloc_states = {
            aid: {
                "freed": st["freed"],
                "free_line": st["free_line"],
                "escaped": st["escaped"],
                "owners": set(st["owners"]),
                "was_reallocated": st.get("was_reallocated", False),
                "realloc_from": st.get("realloc_from"),
                "leaked": st.get("leaked", False),
                "maybe_freed": st.get("maybe_freed", False)
            }
            for aid, st in src.alloc_states.items()
        }
        dest.scopes = [set(s) for s in src.scopes]
        dest.returned = src.returned
        dest.return_line = src.return_line
        dest.broken = src.broken
        dest.continued = src.continued
        dest.path_completed = src.path_completed

    def _is_local_var(self, name: str, state: PathState) -> bool:
        """Returns True if name is declared in any active local scope on this path."""
        return any(name in s for s in state.scopes)

    def _merge_states(self, state_a: PathState, state_b: PathState, state_out: PathState):
        """Merges two continuing control flow paths conservatively into state_out."""
        # 1. Merge pointer environment
        all_vars = set(state_a.env.keys()).union(state_b.env.keys())
        merged_env: Dict[str, Optional[str]] = {}
        for v in all_vars:
            val_a = state_a.env.get(v)
            val_b = state_b.env.get(v)
            if val_a == val_b:
                merged_env[v] = val_a
            else:
                merged_env[v] = val_a or val_b
        state_out.env = merged_env

        # 2. Merge allocation states
        all_aids = set(state_a.alloc_states.keys()).union(state_b.alloc_states.keys())
        merged_allocs: Dict[str, Dict[str, Any]] = {}
        for aid in all_aids:
            if aid in state_a.alloc_states and aid in state_b.alloc_states:
                st_a = state_a.alloc_states[aid]
                st_b = state_b.alloc_states[aid]
                both_freed = st_a["freed"] and st_b["freed"]
                either_freed = st_a["freed"] or st_b["freed"]
                both_escaped = st_a["escaped"] and st_b["escaped"]

                if either_freed and not both_freed:
                    if aid in self.alloc_records:
                        self.alloc_records[aid].is_conditional = True
                        self.alloc_records[aid].status = "POSSIBLE LEAK"
                        self.alloc_records[aid].severity = "warning"

                was_maybe_freed = st_a.get("maybe_freed", False) or st_b.get("maybe_freed", False)
                merged_maybe_freed = (either_freed and not both_freed) or (was_maybe_freed and not both_freed)

                merged_allocs[aid] = {
                    "freed": both_freed,
                    "free_line": st_a.get("free_line") or st_b.get("free_line"),
                    "escaped": both_escaped,
                    "owners": st_a["owners"].union(st_b["owners"]),
                    "was_reallocated": st_a.get("was_reallocated", False) or st_b.get("was_reallocated", False),
                    "realloc_from": st_a.get("realloc_from") or st_b.get("realloc_from"),
                    "leaked": st_a.get("leaked", False) and st_b.get("leaked", False),
                    "maybe_freed": merged_maybe_freed
                }
            elif aid in state_a.alloc_states:
                st_a = state_a.alloc_states[aid]
                merged_allocs[aid] = dict(st_a)
                merged_allocs[aid]["owners"] = set(st_a["owners"])
                if aid in self.alloc_records:
                    self.alloc_records[aid].is_conditional = True
            else:
                st_b = state_b.alloc_states[aid]
                merged_allocs[aid] = dict(st_b)
                merged_allocs[aid]["owners"] = set(st_b["owners"])
                if aid in self.alloc_records:
                    self.alloc_records[aid].is_conditional = True

        state_out.alloc_states = merged_allocs
        state_out.returned = False
        state_out.broken = False
        state_out.continued = False
        state_out.path_completed = False

    def _eval_constant_condition(self, cond: Any) -> Optional[bool]:
        """Statically evaluates constant conditions where verifiable."""
        if not isinstance(cond, dict):
            return None
        node_type = cond.get("type")
        if node_type == "LiteralNode":
            val = cond.get("value")
            lit_type = cond.get("literal_type")
            if val in ("0", "NULL", "false"):
                return False
            if val in ("1", "true"):
                return True
            if lit_type == "INT_CONSTANT":
                try:
                    return int(val) != 0
                except ValueError:
                    return None
        elif node_type == "IdentifierNode":
            name = cond.get("name")
            if name in ("NULL", "false", "FALSE"):
                return False
            if name in ("true", "TRUE"):
                return True
        elif node_type == "UnaryExpressionNode" and cond.get("operator") == "!":
            inner = self._eval_constant_condition(cond.get("operand"))
            if inner is not None:
                return not inner
        elif node_type == "BinaryExpressionNode":
            op = cond.get("operator")
            left = cond.get("left")
            right = cond.get("right")
            if (isinstance(left, dict) and left.get("type") == "LiteralNode" and left.get("literal_type") == "INT_CONSTANT" and
                isinstance(right, dict) and right.get("type") == "LiteralNode" and right.get("literal_type") == "INT_CONSTANT"):
                try:
                    lv = int(left.get("value", "0"))
                    rv = int(right.get("value", "0"))
                    if op == "==": return lv == rv
                    if op == "!=": return lv != rv
                    if op == "<": return lv < rv
                    if op == "<=": return lv <= rv
                    if op == ">": return lv > rv
                    if op == ">=": return lv >= rv
                except ValueError:
                    pass
        return None

    def _extract_null_check(self, cond: Any) -> Optional[Tuple[str, str]]:
        """Extracts (pointer_name, operator) if cond is a pointer NULL-check guard (e.g. ptr != NULL)."""
        if not isinstance(cond, dict):
            return None
        node_type = cond.get("type")
        if node_type == "BinaryExpressionNode":
            op = cond.get("operator")
            if op in ("!=", "=="):
                left = cond.get("left")
                right = cond.get("right")
                if isinstance(left, dict) and left.get("type") == "IdentifierNode":
                    if isinstance(right, dict) and (right.get("value") in ("NULL", "0") or right.get("name") == "NULL"):
                        return (left.get("name"), op)
                elif isinstance(right, dict) and right.get("type") == "IdentifierNode":
                    if isinstance(left, dict) and (left.get("value") in ("NULL", "0") or left.get("name") == "NULL"):
                        return (right.get("name"), op)
        elif node_type == "IdentifierNode":
            return (cond.get("name"), "!=")
        elif node_type == "UnaryExpressionNode" and cond.get("operator") == "!":
            operand = cond.get("operand")
            if isinstance(operand, dict) and operand.get("type") == "IdentifierNode":
                return (operand.get("name"), "==")
        return None

    def _extract_alloc_call(self, expr: Any) -> Optional[Tuple[str, List[Any], int]]:
        """Extracts (fn_name, args, line) if expr represents a heap allocation primitive."""
        if not isinstance(expr, dict):
            return None

        node_type = expr.get("type")
        if node_type == "FunctionCallNode":
            name = expr.get("name")
            if name in ("malloc", "calloc", "realloc"):
                return (name, expr.get("args", []), expr.get("line", 1))

        elif node_type == "UnaryExpressionNode":
            return self._extract_alloc_call(expr.get("operand"))

        elif node_type == "BinaryExpressionNode":
            return self._extract_alloc_call(expr.get("left")) or self._extract_alloc_call(expr.get("right"))

        elif "value" in expr and isinstance(expr["value"], dict):
            return self._extract_alloc_call(expr["value"])

        return None

    def _check_and_orphan(self, ptr_name: str, state: PathState):
        """Removes ptr_name from its previous allocation's owner set and flags a leak if orphaned."""
        old_alloc_id = state.env.get(ptr_name)
        if old_alloc_id and old_alloc_id in state.alloc_states:
            st = state.alloc_states[old_alloc_id]
            st["owners"].discard(ptr_name)
            if len(st["owners"]) == 0 and not st["freed"] and not st["escaped"]:
                st["leaked"] = True
                if old_alloc_id in self.alloc_records:
                    alloc = self.alloc_records[old_alloc_id]
                    if alloc.was_reallocated or self.in_conditional_depth > 0 or self.in_loop_depth > 0:
                        alloc.status = "POSSIBLE LEAK"
                        alloc.severity = "warning"
                    else:
                        alloc.status = "DEFINITE LEAK"
                        alloc.severity = "error"

    def _add_extra_issue(
        self, pointer: str, allocation_function: str, allocation_line: int, freed: bool, free_line: int, status: str, severity: str
    ):
        """Appends an extra issue while deduplicating by status, pointer, and line."""
        already = any(
            iss.status == status and iss.pointer == pointer and iss.free_line == free_line
            for iss in self.extra_issues
        )
        if not already:
            self.extra_issues.append(MemoryAllocation(
                pointer=pointer,
                allocation_function=allocation_function,
                allocation_line=allocation_line,
                freed=freed,
                free_line=free_line,
                status=status,
                severity=severity
            ))

    def _is_string_literal(self, expr: Any) -> Optional[str]:
        """Checks if expr is a string literal (direct or wrapped in cast/parenthesis)."""
        if not isinstance(expr, dict):
            return None
        if expr.get("literal_type") == "STRING_LITERAL":
            return str(expr.get("value", '""'))
        if expr.get("type") == "LiteralNode" and str(expr.get("value", "")).startswith('"'):
            return str(expr.get("value", '""'))
        if expr.get("type") == "UnaryExpressionNode":
            return self._is_string_literal(expr.get("operand"))
        return None

    def _extract_pointer_arithmetic(self, expr: Any, state: PathState) -> Optional[Tuple[str, str, str]]:
        """
        Checks if expr is pointer arithmetic (e.g. p + 2, 2 + p, p - 1, p + i)
        derived from a known heap allocation or interior pointer.
        Returns (base_ptr, alloc_id, display_expr) if found, else None.
        """
        if not isinstance(expr, dict):
            return None

        node_type = expr.get("type")
        if node_type == "UnaryExpressionNode":
            return self._extract_pointer_arithmetic(expr.get("operand"), state)

        if node_type == "BinaryExpressionNode":
            op = expr.get("operator")
            if op in ("+", "-"):
                left = expr.get("left")
                right = expr.get("right")

                def check_ptr(node: Any) -> Optional[Tuple[str, str]]:
                    if isinstance(node, dict) and node.get("type") == "IdentifierNode":
                        pname = node.get("name")
                        val = state.env.get(pname)
                        if val and val in state.alloc_states:
                            return (pname, val)
                        if isinstance(val, str) and val.startswith("interior:"):
                            parts = val.split(":")
                            return (pname, parts[1])
                    return None

                def is_non_zero_offset(node: Any) -> bool:
                    if not isinstance(node, dict):
                        return True
                    val = node.get("value")
                    return val not in ("0", 0)

                ptr_info = check_ptr(left)
                if ptr_info and is_non_zero_offset(right):
                    pname, aid = ptr_info
                    r_val = right.get("value") if isinstance(right, dict) and "value" in right else (right.get("name") if isinstance(right, dict) else "offset")
                    return (pname, aid, f"{pname} {op} {r_val}")

                if op == "+":
                    ptr_info = check_ptr(right)
                    if ptr_info and is_non_zero_offset(left):
                        pname, aid = ptr_info
                        l_val = left.get("value") if isinstance(left, dict) and "value" in left else (left.get("name") if isinstance(left, dict) else "offset")
                        return (pname, aid, f"{pname} + {l_val}")

        return None

    def _extract_deref_base_name(self, target: str, state: PathState) -> Optional[str]:
        """Extracts the base pointer variable from a dereference assignment target (e.g. *p, *(p + 1), *q)."""
        if not isinstance(target, str) or not target.startswith("*"):
            return None
        inner = target[1:].strip().strip("()").strip()
        if inner in state.env:
            return inner
        tokens = re.findall(r'[a-zA-Z_]\w*', inner)
        for t in tokens:
            if t in state.env:
                return t
        return tokens[0] if tokens else None

    def _report_uaf_if_freed(self, ptr_name: str, line: int, state: PathState):
        """Reports a USE AFTER FREE issue if ptr_name points to an allocation that has been freed."""
        if not ptr_name:
            return
        alloc_id = state.env.get(ptr_name)
        if isinstance(alloc_id, str) and alloc_id.startswith("interior:"):
            parts = alloc_id.split(":")
            alloc_id = parts[1]
        if alloc_id and alloc_id in state.alloc_states:
            st = state.alloc_states[alloc_id]
            if st["freed"]:
                alloc = self.alloc_records.get(alloc_id)
                self._add_extra_issue(
                    pointer=ptr_name,
                    allocation_function=alloc.allocation_function if alloc else "malloc",
                    allocation_line=alloc.allocation_line if alloc else 0,
                    freed=True,
                    free_line=line,
                    status="USE AFTER FREE",
                    severity="error"
                )

    def _check_use_after_free(self, expr: Any, line: int, state: PathState):
        """Recursively checks expressions for dereferences (*ptr, *(p+1), ptr[idx], node->field) of freed memory."""
        if not isinstance(expr, dict):
            return

        node_type = expr.get("type")

        # Case 1: Unary dereference: *p or *(p + 1)
        if node_type == "UnaryExpressionNode" and expr.get("operator") == "*":
            operand = expr.get("operand")
            if isinstance(operand, dict) and operand.get("type") == "IdentifierNode":
                ptr_name = operand.get("name")
                self._report_uaf_if_freed(ptr_name, line, state)
            elif isinstance(operand, dict):
                arith = self._extract_pointer_arithmetic(operand, state)
                if arith:
                    base_ptr, _, _ = arith
                    self._report_uaf_if_freed(base_ptr, line, state)
                else:
                    self._check_use_after_free(operand, line, state)
            return

        # Case 2: Array index dereference: p[idx]
        if node_type == "BinaryExpressionNode" and expr.get("operator") == "[]":
            left = expr.get("left")
            if isinstance(left, dict) and left.get("type") == "IdentifierNode":
                ptr_name = left.get("name")
                self._report_uaf_if_freed(ptr_name, line, state)
            elif isinstance(left, dict):
                self._check_use_after_free(left, line, state)
            self._check_use_after_free(expr.get("right"), line, state)
            return

        # Case 3: Arrow operator member dereference: node->field
        if node_type == "BinaryExpressionNode" and expr.get("operator") == "->":
            left = expr.get("left")
            if isinstance(left, dict) and left.get("type") == "IdentifierNode":
                ptr_name = left.get("name")
                self._report_uaf_if_freed(ptr_name, line, state)
            elif isinstance(left, dict):
                self._check_use_after_free(left, line, state)
            self._check_use_after_free(expr.get("right"), line, state)
            return

        # Case 4: Other unary / binary / call expressions
        if node_type == "UnaryExpressionNode":
            self._check_use_after_free(expr.get("operand"), line, state)
        elif node_type == "BinaryExpressionNode":
            self._check_use_after_free(expr.get("left"), line, state)
            self._check_use_after_free(expr.get("right"), line, state)
        elif node_type == "FunctionCallNode":
            fn_name = expr.get("name")
            args = expr.get("args", [])
            # Built-in functions that unconditionally dereference pointer argument
            if fn_name in ("puts", "strlen", "fputs"):
                if args and isinstance(args[0], dict) and args[0].get("type") == "IdentifierNode":
                    self._report_uaf_if_freed(args[0].get("name"), line, state)
            for arg in args:
                self._check_use_after_free(arg, line, state)

    def _handle_pointer_assignment(self, target: str, expr: Any, line: int, state: PathState):
        """Tracks allocation assignment, pointer aliasing, address-of assignments, and NULL overwrites."""
        alloc_info = self._extract_alloc_call(expr)

        # Case A: Assignment to a new allocation (malloc / calloc / realloc)
        if alloc_info:
            fn_name, args, alloc_line = alloc_info
            realloc_source = None
            if fn_name == "realloc" and args and isinstance(args[0], dict) and args[0].get("type") == "IdentifierNode":
                realloc_source = args[0].get("name")

            if fn_name == "realloc" and realloc_source:
                src_alloc_id = state.env.get(realloc_source)
                if src_alloc_id and src_alloc_id in self.alloc_records:
                    src_alloc = self.alloc_records[src_alloc_id]
                    src_alloc.was_reallocated = True
                    src_alloc.status = "POSSIBLE LEAK"
                    src_alloc.severity = "warning"

            # If realloc is performed on target itself (e.g. p = realloc(p, size)):
            if fn_name == "realloc" and realloc_source and realloc_source == target:
                old_alloc_id = state.env.get(target)
                if old_alloc_id and old_alloc_id in state.alloc_states:
                    state.alloc_states[old_alloc_id]["owners"].discard(target)
                    if old_alloc_id in self.alloc_records:
                        old_alloc = self.alloc_records[old_alloc_id]
                        old_alloc.status = "POSSIBLE LEAK"
                        old_alloc.severity = "warning"
                        old_alloc.freed = False
            else:
                self._check_and_orphan(target, state)

            is_cond = (self.in_conditional_depth > 0 or self.in_loop_depth > 0)
            inst = self._create_allocation(fn_name, alloc_line or line, target, state, is_conditional=is_cond)
            if realloc_source:
                inst.realloc_from = realloc_source
                state.alloc_states[inst.alloc_id]["realloc_from"] = realloc_source
            state.env[target] = inst.alloc_id
            return

        # Case B: Assignment to string literal e.g. target = "literal"
        str_lit = self._is_string_literal(expr)
        if str_lit:
            self._check_and_orphan(target, state)
            state.env[target] = "string_literal"
            return

        # Case C: Assignment to pointer arithmetic e.g. target = p + 2 (interior pointer)
        ptr_arith = self._extract_pointer_arithmetic(expr, state)
        if ptr_arith:
            base_ptr, aid, _ = ptr_arith
            self._check_and_orphan(target, state)
            state.env[target] = f"interior:{aid}:{base_ptr}"
            return

        # Case D: Assignment to address-of variable e.g. target = &local_var or &global_var
        if isinstance(expr, dict) and expr.get("type") == "UnaryExpressionNode" and expr.get("operator") == "&":
            operand = expr.get("operand")
            if isinstance(operand, dict) and operand.get("type") == "IdentifierNode":
                var_name = operand.get("name")
                self._check_and_orphan(target, state)
                if self._is_local_var(var_name, state):
                    state.env[target] = f"stack:{var_name}"
                elif var_name in self.global_vars:
                    state.env[target] = f"global:{var_name}"
                else:
                    state.env[target] = f"stack:{var_name}"
                return

        # Case E: Assignment to NULL or 0 (lost pointer leak if target was sole owner)
        if isinstance(expr, dict) and (
            expr.get("value") in ("NULL", "0") or
            expr.get("name") == "NULL"
        ):
            self._check_and_orphan(target, state)
            state.env[target] = None
            return

        # Case F: Assignment to another pointer variable (aliasing)
        if isinstance(expr, dict) and expr.get("type") == "IdentifierNode":
            src_var = expr.get("name")
            if src_var in state.env:
                src_val = state.env[src_var]
                if state.env.get(target) != src_val:
                    self._check_and_orphan(target, state)
                state.env[target] = src_val
                if src_val and src_val in state.alloc_states:
                    state.alloc_states[src_val]["owners"].add(target)
                return

        # Default: Overwrite target with non-heap value
        self._check_and_orphan(target, state)
        state.env[target] = None

    def _handle_free_call(self, args: List[Any], line: int, state: PathState):
        """Processes a free(p) invocation against the path state."""
        if not args:
            return
        arg0 = args[0]
        if not isinstance(arg0, dict):
            return

        # Case 1: Direct free(&var) of stack or global address
        if arg0.get("type") == "UnaryExpressionNode" and arg0.get("operator") == "&":
            operand = arg0.get("operand")
            var_name = operand.get("name") if isinstance(operand, dict) else "var"
            if self._is_local_var(var_name, state):
                fn_kind = "stack"
            elif var_name in self.global_vars:
                fn_kind = "global"
            else:
                fn_kind = "stack"
            self._add_extra_issue(f"&{var_name}", fn_kind, 0, True, line, "INVALID FREE", "error")
            return

        # Case 2: Direct free("literal") of string literal
        str_lit = self._is_string_literal(arg0)
        if str_lit:
            self._add_extra_issue(str_lit, "string_literal", 0, True, line, "INVALID FREE", "error")
            return

        # Case 3: Direct free(p + 2) of pointer arithmetic expression
        arith_info = self._extract_pointer_arithmetic(arg0, state)
        if arith_info:
            _, _, disp = arith_info
            self._add_extra_issue(disp, "interior", 0, True, line, "INVALID FREE", "error")
            return

        freed_ptr = arg0.get("name")
        if not freed_ptr:
            return

        # Case 4: free(NULL) or freeing pointer explicitly set to NULL
        if freed_ptr == "NULL" or (freed_ptr in state.env and state.env.get(freed_ptr) in (None, "NULL")):
            # Standard C defines free(NULL) as a valid no-op
            return

        # Case 5: Freeing pointer holding string literal: s = "text"; free(s);
        ptr_val = state.env.get(freed_ptr)
        if ptr_val == "string_literal":
            self._add_extra_issue(freed_ptr, "string_literal", 0, True, line, "INVALID FREE", "error")
            return

        # Case 6: Freeing interior pointer: q = p + 2; free(q);
        if isinstance(ptr_val, str) and ptr_val.startswith("interior:"):
            self._add_extra_issue(freed_ptr, "interior", 0, True, line, "INVALID FREE", "error")
            return

        # Case 7: Freeing pointer holding stack or global address: p = &x; free(p);
        if isinstance(ptr_val, str) and (ptr_val.startswith("stack:") or ptr_val.startswith("global:")):
            fn_kind = "global" if ptr_val.startswith("global:") else "stack"
            self._add_extra_issue(freed_ptr, fn_kind, 0, True, line, "INVALID FREE", "error")
            return

        # Case 8: Known heap allocation on this path
        alloc_id = state.env.get(freed_ptr)
        if alloc_id and alloc_id in state.alloc_states:
            st = state.alloc_states[alloc_id]
            if not st["freed"]:
                if st.get("maybe_freed", False):
                    # Possible double-free: allocation may have already been freed along an alternate control-flow path
                    alloc = self.alloc_records.get(alloc_id)
                    self._add_extra_issue(
                        freed_ptr,
                        alloc.allocation_function if alloc else "malloc",
                        alloc.allocation_line if alloc else 0,
                        True,
                        line,
                        "POSSIBLE DOUBLE FREE",
                        "warning"
                    )
                    st["freed"] = True
                    st["maybe_freed"] = False
                    st["free_line"] = line
                    st["owners"].discard(freed_ptr)
                else:
                    st["freed"] = True
                    st["free_line"] = line
                    st["owners"].discard(freed_ptr)

                    if alloc_id in self.alloc_records:
                        alloc = self.alloc_records[alloc_id]
                        alloc.freed = True
                        alloc.free_line = line
                        alloc.status = "SAFE"
                        alloc.severity = "safe"
            else:
                # Definite double-free! (either direct free(p) or through alias free(q))
                alloc = self.alloc_records.get(alloc_id)
                self._add_extra_issue(
                    freed_ptr,
                    alloc.allocation_function if alloc else "malloc",
                    alloc.allocation_line if alloc else 0,
                    True,
                    line,
                    "DOUBLE FREE",
                    "error"
                )
        else:
            # Case 9: Pointer not bound to any known heap allocation on this path
            if freed_ptr in self.fn_params:
                return

            # Check if freed_ptr previously belonged to an allocation that was already freed on this path
            prev_st = next(
                (st for aid, st in state.alloc_states.items()
                 if aid in self.alloc_records and (self.alloc_records[aid].target_ptr == freed_ptr or freed_ptr in st["owners"])),
                None
            )
            if prev_st and prev_st["freed"]:
                self._add_extra_issue(freed_ptr, "malloc", 0, True, line, "DOUBLE FREE", "error")
            elif prev_st and prev_st.get("maybe_freed", False):
                self._add_extra_issue(freed_ptr, "malloc", 0, True, line, "POSSIBLE DOUBLE FREE", "warning")
            else:
                self._add_extra_issue(freed_ptr, "None", 0, True, line, "INVALID FREE", "error")

    def _handle_return(self, val_expr: Any, line: int, state: PathState):
        """Handles return statement: marks escaping pointers and flags early-exit leaks."""
        if isinstance(val_expr, dict) and val_expr.get("type") == "IdentifierNode":
            ret_ptr = val_expr.get("name")
            alloc_id = state.env.get(ret_ptr)
            if alloc_id and alloc_id in state.alloc_states:
                state.alloc_states[alloc_id]["escaped"] = True
                if alloc_id in self.alloc_records:
                    self.alloc_records[alloc_id].escaped = True

        state.returned = True
        state.return_line = line

        # Mark all un-freed, un-escaped allocations as leaked at this return
        for aid, st in state.alloc_states.items():
            if not st["freed"] and not st["escaped"]:
                st["leaked"] = True

        self._record_path_completion(state)

    def _walk_statements(self, statements: List[Dict[str, Any]], state: PathState):
        """Walks a list of statements sequentially on the given path state."""
        for stmt in statements:
            if state.returned or state.broken or state.continued:
                break
            self._walk_node(stmt, state)

    def _walk_if(self, node: Dict[str, Any], state: PathState):
        """Performs branch-sensitive control flow analysis on an IfNode."""
        cond = node.get("condition")
        line = node.get("line", 1)
        self._check_use_after_free(cond, line, state)

        cond_const = self._eval_constant_condition(cond)
        then_branch = node.get("then_branch")
        else_branch = node.get("else_branch")

        if cond_const is True:
            if then_branch:
                self._walk_node(then_branch, state)
            return

        if cond_const is False:
            if else_branch:
                self._walk_node(else_branch, state)
            return

        # Check for pointer null-check guard e.g. if (ptr != NULL) or if (ptr)
        null_guard = self._extract_null_check(cond)

        # Dynamic / unknown condition: analyze both branches separately
        self.in_conditional_depth += 1

        state_then = state.clone()
        state_else = state.clone()

        if null_guard:
            var_name, op = null_guard
            if op == "!=":
                # On else branch: var_name is NULL (failed allocation), so no heap buffer exists on this path
                aid = state_else.env.get(var_name)
                state_else.env[var_name] = None
                if aid and aid in state_else.alloc_states:
                    del state_else.alloc_states[aid]
                # On then branch: var_name is non-NULL (realloc succeeded)
                aid_then = state_then.env.get(var_name)
                if aid_then and aid_then in self.alloc_records:
                    realloc_src = self.alloc_records[aid_then].realloc_from
                    if realloc_src:
                        for s_id, s_a in self.alloc_records.items():
                            if s_a.target_ptr == realloc_src and s_id != aid_then and s_id in state_then.alloc_states:
                                state_then.alloc_states[s_id]["freed"] = True
            elif op == "==":
                # On then branch: var_name is NULL (failed allocation)
                aid = state_then.env.get(var_name)
                state_then.env[var_name] = None
                if aid and aid in state_then.alloc_states:
                    del state_then.alloc_states[aid]
                # On else branch: var_name is non-NULL (realloc succeeded)
                aid_else = state_else.env.get(var_name)
                if aid_else and aid_else in self.alloc_records:
                    realloc_src = self.alloc_records[aid_else].realloc_from
                    if realloc_src:
                        for s_id, s_a in self.alloc_records.items():
                            if s_a.target_ptr == realloc_src and s_id != aid_else and s_id in state_else.alloc_states:
                                state_else.alloc_states[s_id]["freed"] = True

        if then_branch:
            self._walk_node(then_branch, state_then)

        if else_branch:
            self._walk_node(else_branch, state_else)

        self.in_conditional_depth -= 1

        # Check jump exit outcomes of branches (return, break, continue)
        then_exits = state_then.returned or state_then.broken or state_then.continued
        else_exits = state_else.returned or state_else.broken or state_else.continued

        if then_exits and else_exits:
            if state_then.returned:
                self._record_path_completion(state_then)
            if state_else.returned:
                self._record_path_completion(state_else)
            state.returned = state_then.returned and state_else.returned
            state.broken = state_then.broken and state_else.broken
            state.continued = state_then.continued and state_else.continued
            state.return_line = state_then.return_line or state_else.return_line
        elif then_exits and not else_exits:
            if state_then.returned:
                self._record_path_completion(state_then)
            if state_then.broken or state_then.continued:
                for aid, st in state_then.alloc_states.items():
                    if not st["freed"] and not st["escaped"] and aid in self.alloc_records:
                        self.alloc_records[aid].is_conditional = True
                        self.alloc_records[aid].path_outcomes.append("LEAK")
            self._copy_state(state_else, state)
        elif not then_exits and else_exits:
            if state_else.returned:
                self._record_path_completion(state_else)
            if state_else.broken or state_else.continued:
                for aid, st in state_else.alloc_states.items():
                    if not st["freed"] and not st["escaped"] and aid in self.alloc_records:
                        self.alloc_records[aid].is_conditional = True
                        self.alloc_records[aid].path_outcomes.append("LEAK")
            self._copy_state(state_then, state)
        else:
            # Neither branch exited: merge states to continue fallthrough execution
            self._merge_states(state_then, state_else, state)

    def _walk_loop(self, node: Dict[str, Any], state: PathState):
        """Analyzes loop constructs (while, for, do-while) accounting for 0, 1, or multiple iterations."""
        node_type = node.get("type")
        line = node.get("line", 1)

        # 1. Initialization for for-loops
        if node_type == "ForNode" and node.get("init"):
            self._walk_node(node["init"], state)

        cond = node.get("condition")
        if cond:
            self._check_use_after_free(cond, line, state)

        cond_const = self._eval_constant_condition(cond) if cond else None

        # Loop condition known false (for while and for loops)
        if cond_const is False and node_type != "DoWhileNode":
            return

        body = node.get("body")
        increment = node.get("increment") if node_type == "ForNode" else None

        if cond_const is True:
            # Loop definitely executes
            self.in_loop_depth += 1
            if body:
                self._walk_node(body, state)
            if increment and not state.broken and not state.returned:
                self._walk_node(increment, state)
            self.in_loop_depth -= 1
            if state.broken:
                state.broken = False
            return

        # Dynamic condition: may execute 0 times or 1+ times
        state_0 = state.clone()  # 0 iterations path

        state_1 = state.clone()  # 1st iteration path
        self.in_loop_depth += 1
        self.in_conditional_depth += 1
        if body:
            self._walk_node(body, state_1)
        if increment and not state_1.broken and not state_1.returned:
            self._walk_node(increment, state_1)
        self.in_loop_depth -= 1
        self.in_conditional_depth -= 1

        if state_1.returned:
            self._record_path_completion(state_1)
            self._copy_state(state_0, state)
            return

        if state_1.broken:
            state_1.broken = False

        # Iteration 2 check for loop-carried issues (e.g. repeated free or UAF)
        state_2 = state_1.clone()
        self.in_loop_depth += 1
        self.simulating_loop_carried = True
        if body:
            self._walk_node(body, state_2)
        self.simulating_loop_carried = False
        self.in_loop_depth -= 1

        # Merge 0-iteration path and 1+-iteration path
        self._merge_states(state_0, state_1, state)

    def _walk_node(self, node: Any, state: PathState):
        """Recursively walks AST nodes to track allocations, dereferences, and control flow."""
        if not isinstance(node, dict):
            return

        node_type = node.get("type")

        if node_type == "ProgramNode":
            self._walk_statements(node.get("statements", []), state)

        elif node_type == "FunctionDeclarationNode":
            prev_params = self.fn_params
            self.fn_params = set(node.get("params", []))
            fn_state = PathState()
            fn_state.scopes = [set(self.fn_params)]
            body = node.get("body", {})
            self._walk_node(body, fn_state)
            if not fn_state.returned:
                self._record_path_completion(fn_state)
            self.fn_params = prev_params

        elif node_type == "BlockNode":
            state.scopes.append(set())
            block_vars: Set[str] = set()
            for stmt in node.get("statements", []):
                if isinstance(stmt, dict) and stmt.get("type") == "DeclarationNode":
                    var_name = stmt.get("name")
                    if var_name:
                        block_vars.add(var_name)
                        state.scopes[-1].add(var_name)

            self._walk_statements(node.get("statements", []), state)

            # Scope exit for block-scoped variables:
            for var in block_vars:
                self._check_and_orphan(var, state)
                state.env.pop(var, None)

            if len(state.scopes) > 1:
                state.scopes.pop()

        elif node_type == "DeclarationNode":
            var_name = node.get("name")
            init_expr = node.get("initializer")
            line = node.get("line", 1)
            if state.scopes and var_name:
                state.scopes[-1].add(var_name)
            if init_expr:
                self._check_use_after_free(init_expr, line, state)
                self._handle_pointer_assignment(var_name, init_expr, line, state)
            else:
                state.env[var_name] = None

        elif node_type == "AssignmentNode":
            target = node.get("target")
            val_expr = node.get("value")
            line = node.get("line", 1)

            # Check if LHS is a dereference: *p = 10, *(p + 1) = 42, node->next = NULL, or p[0] = 10
            if isinstance(target, str) and target.startswith("*"):
                base_ptr = self._extract_deref_base_name(target, state)
                if base_ptr:
                    self._report_uaf_if_freed(base_ptr, line, state)
            elif isinstance(target, str) and "->" in target:
                base_ptr = target.split("->")[0].strip()
                if base_ptr:
                    self._report_uaf_if_freed(base_ptr, line, state)
            elif isinstance(target, str) and "[" in target:
                base_ptr = target.split("[")[0].strip()
                if base_ptr:
                    self._report_uaf_if_freed(base_ptr, line, state)
            else:
                self._handle_pointer_assignment(target, val_expr, line, state)

            self._check_use_after_free(val_expr, line, state)

        elif node_type in ("UnaryExpressionNode", "BinaryExpressionNode"):
            line = node.get("line", 1)
            self._check_use_after_free(node, line, state)

        elif node_type == "FunctionCallNode":
            fn_name = node.get("name")
            args = node.get("args", [])
            line = node.get("line", 1)
            if fn_name == "free":
                self._handle_free_call(args, line, state)
            else:
                self._check_use_after_free(node, line, state)

        elif node_type == "ReturnNode":
            val_expr = node.get("value")
            line = node.get("line", 1)
            self._check_use_after_free(val_expr, line, state)
            self._handle_return(val_expr, line, state)

        elif node_type == "BreakNode":
            state.broken = True

        elif node_type == "ContinueNode":
            state.continued = True

        elif node_type == "IfNode":
            self._walk_if(node, state)

        elif node_type in ("WhileNode", "ForNode", "DoWhileNode"):
            self._walk_loop(node, state)

    def _token_fallback_scan(self):
        """Fallback token scanner for incomplete snippets without full AST statements."""
        alloc_map: Dict[str, MemoryAllocation] = {}
        n = len(self.tokens)
        i = 0
        while i < n:
            tok = self.tokens[i]
            if tok.lexeme in ("malloc", "calloc", "realloc"):
                alloc_fn = tok.lexeme
                alloc_line = tok.line
                ptr_name = "unknown_ptr"
                eq_idx = -1
                for j in range(i - 1, max(-1, i - 10), -1):
                    if self.tokens[j].lexeme == "=":
                        eq_idx = j
                        break
                if eq_idx != -1:
                    for k in range(eq_idx - 1, max(-1, eq_idx - 5), -1):
                        if self.tokens[k].token_type == "IDENTIFIER":
                            ptr_name = self.tokens[k].lexeme
                            break
                alloc_obj = MemoryAllocation(
                    pointer=ptr_name,
                    allocation_function=alloc_fn,
                    allocation_line=alloc_line,
                    freed=False,
                    free_line=None,
                    status="POSSIBLE LEAK",
                    severity="warning"
                )
                alloc_map[ptr_name] = alloc_obj
                self.alloc_records[f"token_{i}"] = AllocationInstance(
                    f"token_{i}", alloc_fn, alloc_line, ptr_name
                )
            elif tok.lexeme == "free":
                free_line = tok.line
                freed_ptr = None
                if i + 2 < n and self.tokens[i+1].lexeme == "(" and self.tokens[i+2].token_type == "IDENTIFIER":
                    freed_ptr = self.tokens[i+2].lexeme
                if freed_ptr:
                    if freed_ptr == "NULL":
                        continue
                    matching = [a for a in self.alloc_records.values() if a.target_ptr == freed_ptr]
                    if matching:
                        m = matching[-1]
                        if not m.freed:
                            m.freed = True
                            m.free_line = free_line
                            m.status = "SAFE"
                            m.severity = "safe"
                        else:
                            self._add_extra_issue(freed_ptr, m.allocation_function, m.allocation_line, True, free_line, "DOUBLE FREE", "error")
                    else:
                        self._add_extra_issue(freed_ptr, "None", 0, True, free_line, "INVALID FREE", "error")
            i += 1
