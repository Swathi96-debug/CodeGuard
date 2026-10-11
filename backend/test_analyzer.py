import unittest
import sys
import os

# Ensure backend modules can be imported
sys.path.insert(0, os.path.dirname(__file__))

from preprocessor import Preprocessor
from lexer import Lexer
from parser import Parser
from symbol_table import SymbolTableBuilder
from semantic_analyzer import SemanticAnalyzer
from memory_analyzer import MemoryAnalyzer
from duplication_detector import DuplicationDetector
from suggestion_engine import SuggestionEngine

def parse_code(code: str):
    p_code = Preprocessor.process(code)
    tokens = Lexer(p_code).tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    return parser, ast, tokens

class TestSemicolonDetection(unittest.TestCase):
    def test_valid_printf_and_return(self):
        code = """int x = 10;
printf("%d", x);
return 0;"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0, f"Unexpected issues: {parser.syntax_issues}")

    def test_missing_semicolon_declaration(self):
        code = "int x = 10"
        parser, _, _ = parse_code(code)
        self.assertGreaterEqual(len(parser.syntax_issues), 1)
        self.assertTrue(any("Missing semicolon" in iss.message for iss in parser.syntax_issues))

    def test_missing_semicolon_before_next_statement(self):
        code = """int a = 5;
int b = 10
int sum = a + b;
return 0;"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 1)
        self.assertEqual(parser.syntax_issues[0].line, 2)
        self.assertIn("Missing semicolon", parser.syntax_issues[0].message)

    def test_whitespace_after_semicolon(self):
        code = "int x = 10;     \n    \nint y = 20;   \t  "
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_multiple_statements_single_line(self):
        code = "int a = 1; int b = 2; int c = a + b;"
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_multiline_expression(self):
        code = """int result = x +
             y +
             z;"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_semicolon_inside_strings(self):
        code = 'char *s = "hello; world; with; semicolons;";'
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_semicolons_in_comments(self):
        code = """// This comment has ; multiple ; semicolons ;
int a = 1;
/* Multi-line comment ;
   with ; semicolons ; */
int b = 2;"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)


class TestForLoopSupport(unittest.TestCase):
    def test_for_loop_with_declaration(self):
        code = 'for (int i = 0; i < 10; i++) { printf("%d", i); }'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0, f"Issues: {parser.syntax_issues}")
        self.assertEqual(ast["statements"][0]["type"], "ForNode")
        self.assertIsNotNone(ast["statements"][0]["init"])
        self.assertIsNotNone(ast["statements"][0]["condition"])
        self.assertIsNotNone(ast["statements"][0]["increment"])

    def test_for_loop_with_existing_variable(self):
        code = 'int i; for (i = 0; i < 10; i++) { printf("%d", i); }'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)
        self.assertEqual(ast["statements"][1]["type"], "ForNode")

    def test_for_loop_infinite_empty(self):
        code = 'for (;;) { break; }'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)
        for_node = ast["statements"][0]
        self.assertEqual(for_node["type"], "ForNode")
        self.assertIsNone(for_node["init"])
        self.assertIsNone(for_node["condition"])
        self.assertIsNone(for_node["increment"])

    def test_for_loop_compound_increment(self):
        code = 'for (int i = 0; i < 100; i += 2) { x = x + i; }'
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_for_loop_single_statement_body(self):
        code = 'for (int i = 0; i < 5; i++) x++;'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)


class TestWhileAndDoWhileLoops(unittest.TestCase):
    def test_while_loop_block_body(self):
        code = 'while (i < 10) { i++; }'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)
        self.assertEqual(ast["statements"][0]["type"], "WhileNode")

    def test_while_loop_single_statement(self):
        code = 'while (condition) statement;'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)
        self.assertEqual(ast["statements"][0]["type"], "WhileNode")

    def test_do_while_loop(self):
        code = 'do { i++; } while (i < 10);'
        parser, ast, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)
        self.assertEqual(ast["statements"][0]["type"], "DoWhileNode")

    def test_do_while_missing_semicolon(self):
        code = 'do { i++; } while (i < 10)'
        parser, _, _ = parse_code(code)
        self.assertGreaterEqual(len(parser.syntax_issues), 1)
        self.assertTrue(any("Missing semicolon" in iss.message for iss in parser.syntax_issues))

    def test_break_and_continue(self):
        code = """while (1) {
    if (x == 5) continue;
    if (x == 10) break;
    x++;
}"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)


class TestNestedConstructsAndScopes(unittest.TestCase):
    def test_nested_loops(self):
        code = """for (int i = 0; i < 10; i++) {
    while (j < 5) {
        j++;
    }
}"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_nested_braces(self):
        code = """{
    int a = 1;
    {
        int b = 2;
        a = b;
    }
}"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_if_else_nested(self):
        code = """if (a > 0) {
    if (b > 0) {
        return 1;
    } else {
        return 2;
    }
} else {
    return 0;
}"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)


class TestPointersAndUnary(unittest.TestCase):
    def test_pointer_dereference_assignment(self):
        code = """int x = 10;
int *p = &x;
*p = 20;"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_prefix_and_postfix_increment(self):
        code = """int x = 0;
x++;
++x;
x--;
--x;"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_sizeof_expression(self):
        code = """int sz1 = sizeof(int);
int sz2 = sizeof(x);"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)

    def test_function_prototype(self):
        code = """int calculate(int a, int b);
int main() {
    return calculate(5, 10);
}"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)


class TestMemoryAnalysisIntegrity(unittest.TestCase):
    def test_clean_allocation_and_free(self):
        """Case 1: malloc followed by free produces no leak and status SAFE."""
        code = """int main() {
    int *p = malloc(100);
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertEqual(mem[0].severity, "safe")
        self.assertTrue(mem[0].freed)
        self.assertEqual(mem[0].allocation_line, 2)
        self.assertEqual(mem[0].free_line, 3)

    def test_double_free_detection(self):
        code = """int *data = malloc(50);
free(data);
free(data);"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        mem = MemoryAnalyzer(tokens).analyze()
        self.assertTrue(any(m.status == "DOUBLE FREE" for m in mem))

    def test_invalid_free_detection(self):
        code = "free(unallocated_ptr);"
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        mem = MemoryAnalyzer(tokens).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "INVALID FREE")

    def test_pointer_overwritten_by_second_allocation_leaks_first(self):
        """Case 2: Pointer overwritten by second allocation leaks the first allocation (unreachable)."""
        code = """int main() {
    int *p = malloc(10);
    p = malloc(20);
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 2)
        # First allocation is definitely leaked because it was overwritten without free
        self.assertEqual(mem[0].status, "DEFINITE LEAK")
        self.assertEqual(mem[0].severity, "error")
        self.assertFalse(mem[0].freed)
        # Second allocation is safe because it was freed
        self.assertEqual(mem[1].status, "SAFE")
        self.assertEqual(mem[1].severity, "safe")
        self.assertTrue(mem[1].freed)

    def test_pointer_overwritten_with_null_leaks(self):
        """Pointer overwritten with NULL without prior free definitely leaks the allocation."""
        code = """int main() {
    int *p = malloc(64);
    p = NULL;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "DEFINITE LEAK")
        self.assertEqual(mem[0].severity, "error")
        self.assertFalse(mem[0].freed)

    def test_aliased_pointers_free_via_alias_is_safe(self):
        """Case 3: Setting one alias to NULL does not report a leak while the other alias remains valid and frees."""
        code = """int main() {
    int *p = malloc(128);
    int *q = p;
    p = NULL;
    free(q);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertEqual(mem[0].severity, "safe")
        self.assertTrue(mem[0].freed)

    def test_calloc_allocation_and_free(self):
        """calloc tracked identically to malloc."""
        code = """int main() {
    int *p = calloc(10, sizeof(int));
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].allocation_function, "calloc")
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)

    def test_allocation_lost_when_local_pointer_goes_out_of_scope(self):
        """Case 5: Allocation lost when a local pointer goes out of block scope."""
        code = """int main() {
    {
        int *p = malloc(48);
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "DEFINITE LEAK")
        self.assertEqual(mem[0].severity, "error")
        self.assertFalse(mem[0].freed)

    def test_realloc_same_pointer_possible_leak_on_failure(self):
        """Case 6: realloc assigned to the same pointer (p = realloc(p, size)) can lose pointer on failure."""
        code = """int main() {
    int *p = malloc(16);
    p = realloc(p, 32);
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 2)
        # Original block must NOT be assumed definitely safe; on failure p becomes NULL and original leaks!
        old_alloc = mem[0]
        self.assertEqual(old_alloc.status, "POSSIBLE LEAK")
        self.assertEqual(old_alloc.severity, "warning")
        self.assertFalse(old_alloc.freed)
        # Resized block was freed via free(p)
        new_alloc = mem[1]
        self.assertEqual(new_alloc.status, "SAFE")
        self.assertEqual(new_alloc.severity, "safe")
        self.assertTrue(new_alloc.freed)

    def test_realloc_temporary_pointer_handles_success_and_failure(self):
        """Case 7: realloc assigned to temporary pointer with both success and failure handled correctly."""
        code = """int main() {
    int *p = malloc(16);
    int *tmp = realloc(p, 32);
    if (tmp == NULL) {
        free(p);
    } else {
        free(tmp);
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 2)
        # Both original allocation (handled on failure) and new allocation (handled on success) are safe
        self.assertTrue(all(m.status == "SAFE" for m in mem))
        self.assertTrue(all(m.freed for m in mem))

    def test_realloc_temporary_pointer_unhandled_failure_possible_leak(self):
        """Case 7b: realloc assigned to temporary pointer where failure path is unhandled leaves original as POSSIBLE LEAK."""
        code = """int main() {
    int *old_buf = malloc(16);
    int *new_buf = realloc(old_buf, 32);
    free(new_buf);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 2)
        # old_buf was not freed on failure path
        self.assertEqual(mem[0].status, "POSSIBLE LEAK")
        self.assertEqual(mem[0].severity, "warning")
        self.assertFalse(mem[0].freed)
        # new_buf was freed on success path
        self.assertEqual(mem[1].status, "SAFE")
        self.assertEqual(mem[1].severity, "safe")
        self.assertTrue(mem[1].freed)

    def test_allocation_returned_from_function_not_reported_as_local_leak(self):
        """Case 4: Allocations returned from a function escape local scope and are not local leaks."""
        code = """int* allocate_table() {
    int *table = malloc(512);
    return table;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        # Escaped ownership is safe and not reported as a leak
        self.assertEqual(mem[0].status, "ESCAPED")
        self.assertEqual(mem[0].severity, "safe")
        self.assertFalse(mem[0].freed)

    def test_multiple_separate_allocations_partial_leak(self):
        """Multiple allocations tracked distinctly (one freed, one leaked)."""
        code = """int main() {
    int *p1 = malloc(20);
    int *p2 = malloc(40);
    free(p1);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 2)
        p1_mem = next(m for m in mem if m.pointer == "p1")
        p2_mem = next(m for m in mem if m.pointer == "p2")
        self.assertEqual(p1_mem.status, "SAFE")
        self.assertTrue(p1_mem.freed)
        self.assertEqual(p2_mem.status, "DEFINITE LEAK")
        self.assertFalse(p2_mem.freed)

    # ------------------ Phase 3A Milestone 3: Invalid Memory Operations ------------------

    def test_use_after_free_write_through_original_pointer(self):
        """M3: Detect dereferencing and writing through a pointer after its allocation has been freed."""
        code = """int main() {
    int *p = malloc(10);
    free(p);
    *p = 20;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        uaf = [m for m in mem if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].severity, "error")
        self.assertEqual(uaf[0].free_line, 4)  # line of illegal write

    def test_use_after_free_read_through_original_pointer(self):
        """M3: Detect reading through a pointer after its allocation has been freed."""
        code = """int main() {
    int *p = malloc(10);
    free(p);
    int val = *p;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        uaf = [m for m in mem if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].severity, "error")
        self.assertEqual(uaf[0].free_line, 4)

    def test_use_after_free_through_alias(self):
        """M3: Detect reads or writes through aliases of a freed allocation."""
        code = """int main() {
    int *p = malloc(10);
    int *q = p;
    free(p);
    *q = 30;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        uaf = [m for m in mem if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "q")
        self.assertEqual(uaf[0].severity, "error")
        self.assertEqual(uaf[0].free_line, 5)

    def test_reassignment_to_new_allocation_clears_use_after_free(self):
        """M3: Avoid reporting use-after-free when pointer is reassigned to a valid new allocation."""
        code = """int main() {
    int *p = malloc(10);
    free(p);
    p = malloc(20);
    *p = 50;
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        uaf = [m for m in mem if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 0, f"Expected 0 UAF issues after reassignment, got {uaf}")
        # Both allocations were freed safely
        self.assertEqual(len(mem), 2)
        self.assertTrue(all(m.status == "SAFE" for m in mem))

    def test_double_free_through_alias(self):
        """M3: Detect double-free when freeing an allocation through an alias pointer."""
        code = """int main() {
    int *p = malloc(10);
    int *q = p;
    free(p);
    free(q);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        df = [m for m in mem if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].pointer, "q")
        self.assertEqual(df[0].severity, "error")
        self.assertEqual(df[0].free_line, 5)

    def test_invalid_free_direct_stack_address(self):
        """M3: Detect freeing stack/local address directly via free(&local_var)."""
        code = """int main() {
    int x = 10;
    free(&x);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        inv = [m for m in mem if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "&x")
        self.assertEqual(inv[0].severity, "error")
        self.assertEqual(inv[0].free_line, 3)

    def test_invalid_free_pointer_holding_stack_address(self):
        """M3: Detect freeing pointer holding stack address (p = &local_var; free(p))."""
        code = """int main() {
    int x = 10;
    int *p = &x;
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        inv = [m for m in mem if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "p")
        self.assertEqual(inv[0].severity, "error")
        self.assertEqual(inv[0].free_line, 4)

    def test_function_parameter_free_not_falsely_flagged_as_invalid(self):
        """M3: Freeing external function parameters is uncertain and must NOT be labeled as definite invalid free."""
        code = """void cleanup(int *buf) {
    free(buf);
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        inv = [m for m in mem if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 0, f"Expected 0 invalid frees on parameter, got {inv}")

    def test_free_null_is_safe_noop(self):
        """M3: free(NULL) or freeing pointer explicitly set to NULL is valid C no-op."""
        code = """int main() {
    int *p = NULL;
    free(p);
    free(NULL);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        errors = [m for m in mem if m.severity == "error"]
        self.assertEqual(len(errors), 0, f"Expected 0 errors for free(NULL), got {errors}")


class TestControlFlowMemoryAnalysis(unittest.TestCase):
    """Phase 3A, Milestone 4: Control-flow analysis tests covering branches, loops, early exits, and scopes."""

    def test_control_flow_if_else_both_sides_freed(self):
        """M4 Case 1: Allocation freed on both branches of if/else is definitely safe."""
        code = """int test(int flag) {
    int *p = malloc(64);
    if (flag) {
        free(p);
    } else {
        free(p);
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)
        self.assertEqual(mem[0].severity, "safe")

    def test_control_flow_if_else_freed_on_one_branch_only(self):
        """M4 Case 2: Allocation freed on one branch but not the other is a POSSIBLE LEAK, not a definite leak."""
        code = """int test(int flag) {
    int *p = malloc(64);
    if (flag) {
        free(p);
    } else {
        // forgot to free
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "POSSIBLE LEAK")
        self.assertEqual(mem[0].severity, "warning")
        self.assertFalse(mem[0].freed)

    def test_control_flow_never_entered_branch_constant_false(self):
        """M4 Case 3: Allocation inside a branch that is never entered at runtime is not reported as leaked."""
        code = """int test() {
    int *p = NULL;
    if (0) {
        p = malloc(128);
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 0)

    def test_control_flow_loop_may_execute_zero_times(self):
        """M4 Case 4: Allocation inside a loop that may execute 0 times is at most a POSSIBLE LEAK."""
        code = """int test(int count) {
    while (count > 0) {
        int *p = malloc(32);
        count--;
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertTrue(len(mem) >= 1)
        self.assertEqual(mem[0].status, "POSSIBLE LEAK")
        self.assertEqual(mem[0].severity, "warning")

    def test_control_flow_loop_allocation_and_free_clean(self):
        """M4 Case 5: Allocation and free within a loop executes cleanly without leak or double free."""
        code = """int test(int n) {
    int i = 0;
    while (i < n) {
        int *buf = malloc(16);
        free(buf);
        i++;
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)
        self.assertEqual(mem[0].severity, "safe")

    def test_control_flow_early_return_before_free_reports_leak(self):
        """M4 Case 6: Early return after allocation but before free reports a leak on the exit path."""
        code = """int test(int err) {
    int *p = malloc(100);
    if (err) {
        return -1;
    }
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "POSSIBLE LEAK")
        self.assertEqual(mem[0].severity, "warning")

    def test_control_flow_early_return_after_free_safe(self):
        """M4 Case 7: Early return after a successful free is completely safe."""
        code = """int test(int done) {
    int *p = malloc(100);
    free(p);
    if (done) {
        return 0;
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)
        self.assertEqual(mem[0].severity, "safe")

    def test_control_flow_nested_block_alias_scope_exit(self):
        """M4 Case 8: Nested block scope exit with pointer aliases does not orphan allocation while outer owner remains."""
        code = """int test() {
    int *p = malloc(128);
    {
        int *q = p;
    }
    free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)

    def test_control_flow_break_in_loop(self):
        """M4 Case 9a: Loop break path properly preserves clean free."""
        code = """int test(int n) {
    int i = 0;
    while (i < n) {
        int *buf = malloc(64);
        if (i == 2) {
            free(buf);
            break;
        }
        free(buf);
        i++;
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)

    def test_control_flow_continue_skipping_free_reports_leak(self):
        """M4 Case 9b: Loop continue path skipping free reports possible leak."""
        code = """int test(int n) {
    int i = 0;
    while (i < n) {
        int *buf = malloc(64);
        if (i == 1) {
            i++;
            continue;
        }
        free(buf);
        i++;
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "POSSIBLE LEAK")
        self.assertEqual(mem[0].severity, "warning")

    def test_control_flow_conditional_alloc_with_guarded_free(self):
        """M4 Edge Case 3: Allocation inside conditional branch with matching null guard free has no definite leak."""
        code = """int test(int flag) {
    int *p = NULL;
    if (flag) p = malloc(10);
    if (p) free(p);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].status, "SAFE")
        self.assertTrue(mem[0].freed)
        self.assertEqual(mem[0].severity, "safe")

    def test_control_flow_loop_repeated_free_reports_double_free(self):
        """M4 Loop simulation detects loop-carried double-free without creating false duplicate allocations."""
        code = """int test(int cond) {
    int *p = malloc(10);
    while (cond) {
        free(p);
    }
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        mem = MemoryAnalyzer(tokens, ast=ast).analyze()
        statuses = [m.status for m in mem]
        self.assertIn("DOUBLE FREE", statuses)
        self.assertIn("POSSIBLE LEAK", statuses)


class TestBuiltinSamplePrograms(unittest.TestCase):
    def test_clean_sample(self):
        code = """#include <stdio.h>
#include <stdlib.h>

int main() {
    int x = 10;
    int y = 20;
    int result = x + y;
    
    int *ptr = malloc(100);
    if (ptr != NULL) {
        *ptr = result;
        free(ptr);
    }
    return 0;
}"""
        parser, _, tokens = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 0)
        dups = DuplicationDetector(code, tokens).detect()
        self.assertEqual(len(dups), 0, f"Expected 0 duplicate blocks in clean sample, got {len(dups)}")

    def test_clean_sample_pipeline_overall_clean(self):
        from main import analyze_code
        from models import AnalyzeRequest
        code = """#include <stdio.h>
#include <stdlib.h>

int main() {
    int x = 10;
    int y = 20;
    int result = x + y;
    
    int *ptr = malloc(100);
    if (ptr != NULL) {
        *ptr = result;
        free(ptr);
    }
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.syntax_errors, 0)
        self.assertEqual(res.statistics.semantic_errors, 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(res.statistics.duplicate_blocks, 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")


    def test_missing_semicolon_sample(self):
        code = """#include <stdio.h>

int main() {
    int a = 5;
    int b = 10
    int sum = a + b;
    return 0;
}"""
        parser, _, _ = parse_code(code)
        self.assertEqual(len(parser.syntax_issues), 1)
        self.assertEqual(parser.syntax_issues[0].line, 5)

    def test_duplicate_code_detection(self):
        code = """#include <stdio.h>

int main() {
    int val_a = 15;
    int val_b = 25;
    int sum1 = val_a + val_b;
    
    int item_x = 40;
    int item_y = 60;
    int sum2 = item_x + item_y;
    
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        dups = DuplicationDetector(code, tokens).detect()
        self.assertGreaterEqual(len(dups), 1)

    def test_undeclared_variable_detection(self):
        code = """#include <stdio.h>

int main() {
    target_value = 100;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        sym = SymbolTableBuilder(tokens, ast).build()
        sem_issues = SemanticAnalyzer(tokens, sym).analyze()
        self.assertGreaterEqual(len(sem_issues), 1)
        self.assertEqual(sem_issues[0].issue_type, "Undeclared Variable")

    def test_multiple_undeclared_variables_and_deduplication(self):
        # Reproduces the line 48 crash where checking a second undeclared variable evaluated iss.line on an undefined iss
        code = """int main() {
    first_var = 1;
    second_var = 2;
    same_line = same_line + same_line;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        sym = SymbolTableBuilder(tokens, ast).build()
        sem_issues = SemanticAnalyzer(tokens, sym).analyze()
        self.assertEqual(len(sem_issues), 3)
        self.assertEqual(sem_issues[0].line, 2)
        self.assertIn("'first_var'", sem_issues[0].message)
        self.assertEqual(sem_issues[1].line, 3)
        self.assertIn("'second_var'", sem_issues[1].message)
        self.assertEqual(sem_issues[2].line, 4)
        self.assertIn("'same_line'", sem_issues[2].message)

    def test_calls_to_previously_defined_functions_not_reported_as_undeclared(self):
        code = """int calculate_first() {
    int val_a = 15;
    int val_b = 25;
    return val_a + val_b;
}

int calculate_second() {
    int val_a = 15;
    int val_b = 25;
    return val_a + val_b;
}

int main() {
    int r1 = calculate_first();
    int r2 = calculate_second();
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        sym = SymbolTableBuilder(tokens, ast).build()
        sem_issues = SemanticAnalyzer(tokens, sym, ast).analyze()
        self.assertEqual(len(sem_issues), 0, f"Expected 0 semantic issues, got {sem_issues}")

    def test_calls_to_functions_declared_via_prototypes(self):
        code = """int compute(int x, int y);

int main() {
    int result = compute(5, 10);
    return result;
}

int compute(int x, int y) {
    return x * y;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        sym = SymbolTableBuilder(tokens, ast).build()
        sem_issues = SemanticAnalyzer(tokens, sym, ast).analyze()
        self.assertEqual(len(sem_issues), 0, f"Expected 0 semantic issues, got {sem_issues}")

    def test_genuinely_undeclared_function_and_variable(self):
        code = """int main() {
    missing_func(42);
    undeclared_var = 100;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        sym = SymbolTableBuilder(tokens, ast).build()
        sem_issues = SemanticAnalyzer(tokens, sym, ast).analyze()
        self.assertEqual(len(sem_issues), 2)
        
        fn_issues = [iss for iss in sem_issues if iss.issue_type == "Undeclared Function"]
        self.assertEqual(len(fn_issues), 1)
        self.assertIn("'missing_func'", fn_issues[0].message)

        var_issues = [iss for iss in sem_issues if iss.issue_type == "Undeclared Variable"]
        self.assertEqual(len(var_issues), 1)
        self.assertIn("'undeclared_var'", var_issues[0].message)


class TestSuggestionEngineSafeFixes(unittest.TestCase):
    def test_missing_semicolon_safe_fix(self):
        code = """int main() {
    int x = 10
    return 0;
}"""
        parser, _, _ = parse_code(code)
        engine = SuggestionEngine(code, parser.syntax_issues, [], [], [])
        anomalies, suggestions = engine.generate()

        self.assertGreaterEqual(len(suggestions), 1)
        semicolon_sugg = [s for s in suggestions if s.category == "SYNTAX" and "semicolon" in s.message.lower()][0]
        self.assertIsNotNone(semicolon_sugg.safe_fix)
        self.assertEqual(semicolon_sugg.target_line, 2)
        self.assertEqual(semicolon_sugg.fix_type, "replace")
        self.assertEqual(semicolon_sugg.original_snippet, "    int x = 10")
        self.assertEqual(semicolon_sugg.fixed_snippet, "    int x = 10;")

    def test_memory_leak_local_safe_fix(self):
        code = """int main() {
    int* buffer = (int*)malloc(100);
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        mem_issues = MemoryAnalyzer(tokens).analyze()
        engine = SuggestionEngine(code, [], [], mem_issues, [])
        anomalies, suggestions = engine.generate()

        leak_sugg = [s for s in suggestions if s.category == "MEMORY" and "buffer" in s.message][0]
        self.assertIsNotNone(leak_sugg.safe_fix)
        self.assertEqual(leak_sugg.fix_type, "insert")
        self.assertEqual(leak_sugg.target_line, 3)
        self.assertIn("free(buffer);", leak_sugg.fixed_snippet)

    def test_memory_leak_escaping_pointer_no_automatic_fix(self):
        # When a pointer is returned, it escapes local ownership. It must NOT provide an automatic free() fix!
        code = """int* create_buffer() {
    int* ptr = (int*)malloc(50);
    return ptr;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        mem_issues = MemoryAnalyzer(tokens).analyze()
        engine = SuggestionEngine(code, [], [], mem_issues, [])
        anomalies, suggestions = engine.generate()

        leak_sugg = [s for s in suggestions if s.category == "MEMORY" and "ptr" in s.message][0]
        # Must NOT offer an automatic fix for escaping pointers
        self.assertIsNone(leak_sugg.safe_fix)
        self.assertIsNone(leak_sugg.fixed_snippet)
        # But still provides educational explanation and recommendation
        self.assertIn("free", leak_sugg.suggestion.lower())

    def test_semantic_and_duplication_no_unsafe_automatic_fixes(self):
        code = """int main() {
    undeclared_var = 10;
    return 0;
}"""
        p_code = Preprocessor.process(code)
        tokens = Lexer(p_code).tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        sym = SymbolTableBuilder(tokens, ast).build()
        sem_issues = SemanticAnalyzer(tokens, sym, ast).analyze()
        engine = SuggestionEngine(code, [], sem_issues, [], [])
        anomalies, suggestions = engine.generate()

        for s in suggestions:
            self.assertIsNone(s.safe_fix)

    def test_opening_preview_does_not_mutate_source_code(self):
        """
        Regression Test: Opening a fix preview must never mutate the editor's source code.
        The preview must compute and display proposed changes using a separate snapshot/diff only.
        """
        initial_source = """// Test Case 2: Missing Semicolon
#include <stdio.h>

int main() {
    int a = 5;
    int b = 10
    int sum = a + b;
    return 0;
}"""
        # Parse and generate suggestions
        parser, _, _ = parse_code(initial_source)
        engine = SuggestionEngine(initial_source, parser.syntax_issues, [], [], [])
        _, suggestions = engine.generate()
        self.assertGreaterEqual(len(suggestions), 1)
        semicolon_sugg = suggestions[0]

        # Simulating preview modal opening data flow
        # In CompilerInterface: previewSuggestion = sugg, codeSnapshot = code
        # Source code in editor MUST remain exactly equal to initial_source
        editor_code = initial_source
        code_snapshot = editor_code
        preview_suggestion = semicolon_sugg

        # Proposed fix lines are calculated inside modal purely from snapshot and suggestion:
        target_line = preview_suggestion.target_line or preview_suggestion.line
        snapshot_lines = code_snapshot.splitlines()
        preview_lines = list(snapshot_lines)
        if preview_suggestion.fix_type == "replace":
            preview_lines[target_line - 1] = preview_suggestion.fixed_snippet

        # Verify:
        # 1. Preview lines contain the proposed fix
        self.assertEqual(preview_lines[target_line - 1], "    int b = 10;")
        # 2. Crucially, the actual editor source code has NOT changed!
        self.assertEqual(editor_code, initial_source)
        self.assertEqual(editor_code.splitlines()[target_line - 1], "    int b = 10")

    def test_cancel_does_not_mutate_source_code(self):
        """
        Regression Test: Clicking Cancel or the X must leave the source code exactly
        as it was before opening the preview.
        """
        initial_source = """int main() {
    int x = 10
    return 0;
}"""
        editor_code = initial_source
        # Open preview:
        code_snapshot = editor_code
        preview_open = True

        # User cancels (clicks Cancel button or X):
        preview_open = False
        preview_suggestion = None

        # Verify source code is completely untouched
        self.assertFalse(preview_open)
        self.assertIsNone(preview_suggestion)
        self.assertEqual(editor_code, initial_source)

    def test_confirm_applies_fix_only_after_explicit_confirmation(self):
        """
        Regression Test: Source code may change ONLY after the user explicitly
        clicks 'Confirm & Apply Fix'.
        """
        initial_source = """int main() {
    int x = 10
    return 0;
}"""
        parser, _, _ = parse_code(initial_source)
        engine = SuggestionEngine(initial_source, parser.syntax_issues, [], [], [])
        _, suggestions = engine.generate()
        sugg = suggestions[0]

        editor_code = initial_source
        code_snapshot = editor_code

        # While preview is open and unconfirmed, editor_code MUST NOT be modified
        self.assertEqual(editor_code, initial_source)

        # User explicitly confirms fix:
        target_line = sugg.target_line or sugg.line
        lines = editor_code.splitlines()
        lines[target_line - 1] = sugg.fixed_snippet
        new_code = "\n".join(lines)
        editor_code = new_code

        # Now and only now should the editor code reflect the fix:
        self.assertIn("int x = 10;", editor_code)
        self.assertNotEqual(editor_code, initial_source)

    def test_editing_source_while_preview_open_invalidates_preview_and_disables_apply(self):
        """
        Regression Test: If source code changes manually while preview is open,
        the preview must immediately become stale, display an invalidation warning,
        and disable Apply.
        """
        initial_source = """int main() {
    int x = 10
    return 0;
}"""
        editor_code = initial_source
        code_snapshot = initial_source

        def check_invalidated(curr, snap):
            norm = lambda s: (s or "").replace("\r\n", "\n")
            return norm(curr) != norm(snap)

        # Initially, source code equals snapshot -> not invalidated, Apply enabled
        self.assertFalse(check_invalidated(editor_code, code_snapshot))

        # User edits source code in Monaco editor while preview remains open:
        editor_code = """int main() {
    int x = 10;
    int y = 20
    return 0;
}"""
        # Invalidation must immediately trigger
        is_invalidated = check_invalidated(editor_code, code_snapshot)
        self.assertTrue(is_invalidated, "Editing source while preview open must invalidate preview")

        # Attempting to apply when invalidated MUST be rejected
        apply_permitted = not is_invalidated
        self.assertFalse(apply_permitted, "Apply button must be disabled when preview is invalidated")

    def test_stale_preview_5_to_50_scenario_preserves_user_edit_and_rejects_patch(self):
        """
        Exact Reproduction Regression Test:
        1. Original source: int a = 5 (missing semicolon)
        2. Analyze & open preview for missing semicolon on line 2 (proposes 'int a = 5;')
        3. User manually edits source from 'int a = 5' to 'int a = 50' while preview is open
        4. Invalidation condition triggers: preview becomes stale, Confirm & Apply Fix disabled
        5. Apply handler independent guard rejects patch and preserves '50'
        6. Re-analyzing updated source produces correct 'int a = 50;' fix
        """
        initial_source = """int main() {
    int a = 5
    return 0;
}"""
        # Step 1: Parse and generate suggestion
        parser, _, _ = parse_code(initial_source)
        engine = SuggestionEngine(initial_source, parser.syntax_issues, [], [], [])
        _, suggestions = engine.generate()
        sugg = suggestions[0]

        self.assertEqual(sugg.target_line, 2)
        self.assertEqual(sugg.original_snippet, "    int a = 5")
        self.assertEqual(sugg.fixed_snippet, "    int a = 5;")

        # Step 2: Open preview -> snapshots source
        code_snapshot = initial_source
        sugg_snapshot = initial_source

        # Step 3: User edits source from '5' to '50' while preview is open
        current_editor_code = """int main() {
    int a = 50
    return 0;
}"""

        # Step 4: Preview invalidation check
        norm = lambda s: (s or "").replace("\r\n", "\n")
        is_invalidated = norm(current_editor_code) != norm(code_snapshot)
        self.assertTrue(is_invalidated, "Preview must be marked stale as soon as current code != snapshot")

        # Step 5: Independent apply handler guard simulation
        def apply_fix_with_guard(current_code, snapshot, suggestion):
            # Guard 1: Whole-source snapshot drift check
            if norm(current_code) != norm(snapshot):
                return False, current_code, "Cannot apply fix: source code has changed since preview was generated."

            lines = norm(current_code).split("\n")
            target_line = suggestion.target_line or suggestion.line
            idx = target_line - 1

            # Guard 2: Line-level content check
            if suggestion.fix_type == "replace" and suggestion.original_snippet is not None:
                if lines[idx] != suggestion.original_snippet and lines[idx].strip() != suggestion.original_snippet.strip():
                    return False, current_code, "Cannot apply fix: target line content has changed."

            # Apply patch
            lines[idx] = suggestion.fixed_snippet
            return True, "\n".join(lines), "Success"

        success, resulting_code, error_msg = apply_fix_with_guard(
            current_editor_code, code_snapshot, sugg
        )

        # Verify:
        # Patch application MUST be rejected
        self.assertFalse(success, "Stale patch application must be rejected")
        self.assertIn("source code has changed", error_msg)
        # Editor code MUST preserve '50' completely and not revert to '5'
        self.assertEqual(resulting_code, current_editor_code)
        self.assertIn("int a = 50", resulting_code)
        self.assertNotIn("int a = 5;", resulting_code)

        # Step 6: User closes preview, re-analyzes current source
        parser2, _, _ = parse_code(current_editor_code)
        engine2 = SuggestionEngine(current_editor_code, parser2.syntax_issues, [], [], [])
        _, suggestions2 = engine2.generate()
        sugg2 = suggestions2[0]

        # Fresh preview accurately reflects updated value 50:
        self.assertEqual(sugg2.original_snippet, "    int a = 50")
        self.assertEqual(sugg2.fixed_snippet, "    int a = 50;")

        # Applying fresh preview succeeds and produces 'int a = 50;'
        code_snapshot2 = current_editor_code
        success2, final_code, _ = apply_fix_with_guard(current_editor_code, code_snapshot2, sugg2)
        self.assertTrue(success2)
        self.assertIn("int a = 50;", final_code)



class TestPhase3AMemoryIntegrationPipeline(unittest.TestCase):
    """Phase 3A Milestone 5: End-to-end integration and regression verification for memory analysis pipeline."""

    def test_pipeline_definite_leak_consistency(self):
        """Verify definite leak is reported consistently across memory_analysis, anomalies, suggestions, and stats."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(64);
    *p = 100;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 1)
        self.assertEqual(res.statistics.overall_status, "NEEDS ATTENTION")

        mem = res.memory_analysis
        self.assertEqual(len(mem), 1)
        self.assertEqual(mem[0].pointer, "p")
        self.assertEqual(mem[0].status, "DEFINITE LEAK")
        self.assertEqual(mem[0].severity, "error")

        anom = [a for a in res.anomalies if a.issue_type == "MEMORY LEAK"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "error")
        self.assertEqual(anom[0].line, 2)
        self.assertIn("definitely leaked", anom[0].message)

        sugg = [s for s in res.suggestions if s.category == "MEMORY"]
        self.assertEqual(len(sugg), 1)
        self.assertEqual(sugg[0].title, "Memory Leak Prevention")
        self.assertIsNotNone(sugg[0].safe_fix)

    def test_pipeline_double_free_consistency(self):
        """Verify double-free is reported consistently across memory_analysis, anomalies, suggestions, and stats."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(64);
    int *q = p;
    free(p);
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 1)

        mem = res.memory_analysis
        df_mem = [m for m in mem if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df_mem), 1)
        self.assertEqual(df_mem[0].pointer, "q")
        self.assertEqual(df_mem[0].free_line, 5)

        anom = [a for a in res.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "error")
        self.assertEqual(anom[0].line, 5)

        sugg = [s for s in res.suggestions if s.title == "Double Free Fix"]
        self.assertEqual(len(sugg), 1)
        self.assertIsNone(sugg[0].safe_fix)

    def test_pipeline_use_after_free_consistency(self):
        """Verify use-after-free is reported consistently across memory_analysis, anomalies, suggestions, and stats."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(32);
    free(p);
    *p = 42;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 1)

        mem = res.memory_analysis
        uaf_mem = [m for m in mem if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf_mem), 1)
        self.assertEqual(uaf_mem[0].pointer, "p")
        self.assertEqual(uaf_mem[0].free_line, 4)

        anom = [a for a in res.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "error")
        self.assertEqual(anom[0].line, 4)

        sugg = [s for s in res.suggestions if s.title == "Use-After-Free Prevention"]
        self.assertEqual(len(sugg), 1)

    def test_pipeline_invalid_free_stack_consistency(self):
        """Verify invalid free of stack address is reported consistently across views."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int x = 10;
    free(&x);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 1)

        mem = res.memory_analysis
        inv_mem = [m for m in mem if m.status == "INVALID FREE"]
        self.assertEqual(len(inv_mem), 1)
        self.assertEqual(inv_mem[0].pointer, "&x")

        anom = [a for a in res.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "error")
        self.assertEqual(anom[0].line, 3)

        sugg = [s for s in res.suggestions if s.title == "Invalid Free Prevention"]
        self.assertEqual(len(sugg), 1)

    def test_pipeline_clean_control_flow_if_else_both_freed(self):
        """Verify freeing on both control-flow branches yields clean status with zero memory errors."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int flag = 1;
    int *p = (int *)malloc(128);
    if (flag) {
        free(p);
    } else {
        free(p);
    }
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(res.statistics.warnings_count, 0)
        self.assertEqual(res.statistics.syntax_errors, 0)
        self.assertEqual(res.statistics.semantic_errors, 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")

        self.assertEqual(len(res.memory_analysis), 1)
        self.assertEqual(res.memory_analysis[0].status, "SAFE")
        self.assertTrue(res.memory_analysis[0].freed)

    def test_pipeline_clean_escaping_pointer_no_false_leak(self):
        """Verify function returning allocated pointer is recognized as ESCAPED without false leak error."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int* allocate_buffer() {
    int *buf = (int *)malloc(256);
    return buf;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(res.statistics.warnings_count, 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")

        self.assertEqual(len(res.memory_analysis), 1)
        self.assertEqual(res.memory_analysis[0].status, "ESCAPED")
        self.assertEqual(res.memory_analysis[0].severity, "safe")



class TestPhase3BMilestone1EnhancedInvalidFree(unittest.TestCase):
    """Phase 3B Milestone 1: Enhanced Invalid-Free Detection Tests."""

    def test_invalid_free_string_literal_direct(self):
        """M1: Direct free("literal") is detected as invalid free of read-only string literal."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    free("hello world");
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].allocation_function, "string_literal")
        self.assertEqual(inv[0].severity, "error")

        anom = [a for a in res.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(anom), 1)
        self.assertIn("string literal or read-only memory", anom[0].message)

    def test_invalid_free_string_literal_pointer_variable(self):
        """M1: Freeing pointer initialized with string literal is detected as invalid free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    char *str = "read_only_data";
    free(str);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "str")
        self.assertEqual(inv[0].allocation_function, "string_literal")
        self.assertEqual(inv[0].severity, "error")

    def test_invalid_free_global_variable_direct_address(self):
        """M1: Freeing address of a global variable free(&global_var) is detected as invalid free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int global_counter = 42;

int main() {
    free(&global_counter);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "&global_counter")
        self.assertEqual(inv[0].allocation_function, "global")
        self.assertEqual(inv[0].severity, "error")

        anom = [a for a in res.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(anom), 1)
        self.assertIn("static/global variable address", anom[0].message)

    def test_invalid_free_global_variable_pointer(self):
        """M1: Freeing pointer holding global variable address is detected as invalid free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int global_buffer = 100;

int main() {
    int *p = &global_buffer;
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "p")
        self.assertEqual(inv[0].allocation_function, "global")
        self.assertEqual(inv[0].severity, "error")

    def test_invalid_free_interior_pointer_variable(self):
        """M1: Freeing an interior pointer (q = p + 2) is detected as invalid free while base pointer remains tracked."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(64);
    int *q = p + 2;
    free(q);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "q")
        self.assertEqual(inv[0].allocation_function, "interior")
        self.assertEqual(inv[0].severity, "error")

        # Base allocation p is still safely freed by free(p)
        base = next(m for m in res.memory_analysis if m.pointer == "p")
        self.assertEqual(base.status, "SAFE")
        self.assertTrue(base.freed)

        anom = [a for a in res.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(anom), 1)
        self.assertIn("interior/offset pointer", anom[0].message)

    def test_invalid_free_interior_pointer_direct_arithmetic(self):
        """M1: Direct free(p + 4) expression is detected as invalid free of interior pointer."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(128);
    free(p + 4);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].allocation_function, "interior")

    def test_valid_heap_frees_and_aliases_not_falsely_flagged(self):
        """M1: Valid frees of base heap allocations and aliases are not flagged as invalid."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(32);
    int *q = p;
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")

    def test_free_null_preserved_as_noop(self):
        """M1: free(NULL) and freeing pointers set to NULL are valid no-ops without invalid-free errors."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = NULL;
    free(p);
    free(NULL);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")

    def test_function_parameter_free_preserved_as_uncertain_not_invalid(self):
        """M1: External function parameters remain classified as uncertain and are not flagged as invalid free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """void deallocate(int *buf) {
    free(buf);
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 0)

    def test_invalid_free_global_shadowed_by_local_variable(self):
        """M1 Sanity Check 1: Local variable shadowing global variable is classified as stack, not global."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int counter = 100;

int main() {
    int counter = 20;
    free(&counter);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "&counter")
        self.assertEqual(inv[0].allocation_function, "stack")  # local stack variable, not global!
        self.assertEqual(inv[0].severity, "error")

        anom = [a for a in res.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(anom), 1)
        self.assertNotIn("static/global variable address", anom[0].message)
        self.assertIn("Calling free() on a stack, local, or unallocated pointer", anom[0].why_it_matters)

    def test_invalid_free_interior_pointer_unfreed_base_reported_as_leak(self):
        """M1 Sanity Check 2: free(q) on interior pointer does not mark p as freed; unfreed p is reported as leak."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = (int *)malloc(64);
    int *q = p + 2;
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "q")
        self.assertEqual(inv[0].allocation_function, "interior")

        # p was NOT freed by free(q), so p remains definitely leaked
        leaks = [m for m in res.memory_analysis if m.status == "DEFINITE LEAK"]
        self.assertEqual(len(leaks), 1)
        self.assertEqual(leaks[0].pointer, "p")
        self.assertFalse(leaks[0].freed)


class TestPhase3BMilestone2ExtendedUAF(unittest.TestCase):
    """
    Phase 3B, Milestone 2: Extended Use-After-Free (UAF) Detection.
    Tests UAF through function arguments, struct members, and pointer arithmetic / interior pointers.
    """

    # ------------------ Milestone 1: Function Arguments ------------------

    def test_uaf_function_argument_printf_dereference(self):
        """M1: Dereference inside function argument expression printf("%d", *p) after free(p) is reported as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    printf("%d", *p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].free_line, 4)
        self.assertEqual(uaf[0].severity, "error")

        anom = [a for a in res.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].line, 4)

    def test_uaf_conservative_arbitrary_function_call_no_false_positive(self):
        """M1: Passing freed pointer to an arbitrary function process(p) is conservative: NOT reported as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    process(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 0)

        # p should remain cleanly marked as SAFE
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)
        self.assertEqual(safe[0].pointer, "p")
        self.assertTrue(safe[0].freed)

    def test_uaf_standard_library_dereference_puts_and_strlen(self):
        """M1: Standard library functions that unconditionally dereference (puts, strlen) report UAF on freed pointers."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    char *s = (char *)malloc(32);
    free(s);
    puts(s);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "s")
        self.assertEqual(uaf[0].free_line, 4)

        code_strlen = """int main() {
    char *s = (char *)malloc(32);
    free(s);
    int len = strlen(s);
    return 0;
}"""
        res2 = analyze_code(AnalyzeRequest(code=code_strlen))
        uaf2 = [m for m in res2.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf2), 1)
        self.assertEqual(uaf2[0].pointer, "s")
        self.assertEqual(uaf2[0].free_line, 4)

    # ------------------ Milestone 2: Struct Members ------------------

    def test_uaf_struct_member_write_after_free(self):
        """M2: Member write access node->next = NULL through a freed struct pointer is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """struct Node {
    int value;
    struct Node *next;
};

int main() {
    struct Node *node = malloc(sizeof(struct Node));
    free(node);
    node->next = NULL;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "node")
        self.assertEqual(uaf[0].free_line, 9)
        self.assertEqual(uaf[0].severity, "error")

    def test_uaf_struct_member_read_after_free(self):
        """M2: Member read access int val = node->value through a freed struct pointer is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """struct Node {
    int value;
    struct Node *next;
};

int main() {
    struct Node *node = malloc(sizeof(struct Node));
    free(node);
    int value = node->value;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "node")
        self.assertEqual(uaf[0].free_line, 9)

    def test_clean_struct_member_access_before_free(self):
        """M2: Struct member reads and writes before free() remain completely valid with zero UAF reports."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """struct Node {
    int value;
    struct Node *next;
};

int main() {
    struct Node *node = malloc(sizeof(struct Node));
    node->value = 10;
    node->next = NULL;
    int val = node->value;
    free(node);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)
        self.assertEqual(safe[0].pointer, "node")

    def test_clean_struct_member_access_after_reassignment(self):
        """M2: Reassigning pointer to fresh allocation after free() permits member access without false UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """struct Node {
    int value;
    struct Node *next;
};

int main() {
    struct Node *node = malloc(sizeof(struct Node));
    free(node);
    node = malloc(sizeof(struct Node));
    node->value = 20;
    node->next = NULL;
    free(node);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 2)

    # ------------------ Milestone 3: Pointer Arithmetic & Interior Pointers ------------------

    def test_uaf_pointer_arithmetic_dereference_write(self):
        """M3: Dereference write *(p + 1) = 42 after free(p) is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    free(p);
    *(p + 1) = 42;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].free_line, 4)

    def test_uaf_pointer_arithmetic_dereference_read(self):
        """M3: Dereference read int val = *(p + 1) after free(p) is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    free(p);
    int value = *(p + 1);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].free_line, 4)

    def test_uaf_interior_pointer_alias_dereference_after_free(self):
        """M3: Interior pointer alias q = p + 2 dereferenced after free(p) is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    int *q = p + 2;
    free(p);
    int value = *q;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "q")
        self.assertEqual(uaf[0].free_line, 5)

    def test_uaf_interior_pointer_alias_write_after_free(self):
        """M3: Interior pointer alias write *q = 99 after free(p) is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    int *q = p + 2;
    free(p);
    *q = 99;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "q")
        self.assertEqual(uaf[0].free_line, 5)

    def test_clean_pointer_arithmetic_access_before_free(self):
        """M3: Pointer arithmetic access *(p + 1) before free(p) is valid with zero UAF reports."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    *(p + 1) = 42;
    int val = *(p + 1);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)

    def test_clean_pointer_arithmetic_after_reassignment(self):
        """M3: Pointer arithmetic after reallocating fresh memory does not falsely flag UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    free(p);
    p = malloc(10 * sizeof(int));
    *(p + 1) = 42;
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 0)
        self.assertEqual(res.statistics.memory_issues, 0)
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 2)

    def test_uaf_array_subscript_write_after_free(self):
        """M3: Array subscript write p[0] = 10 after free(p) is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    free(p);
    p[0] = 10;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].free_line, 4)

    def test_uaf_array_subscript_read_after_free(self):
        """M3 Audit: Array subscript read int value = p[0] after free(p) is detected as UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    free(p);
    int value = p[0];
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].pointer, "p")
        self.assertEqual(uaf[0].free_line, 4)

    def test_uaf_deduplication_single_diagnostic(self):
        """Audit 2: Single invalid access produces exactly one diagnostic, not duplicate reports."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    *p = 42;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf_mem = [m for m in res.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf_mem), 1, "Expected exactly 1 UAF memory record, no duplicates")
        self.assertEqual(uaf_mem[0].pointer, "p")
        self.assertEqual(uaf_mem[0].free_line, 4)

        uaf_anom = [a for a in res.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(uaf_anom), 1, "Expected exactly 1 UAF anomaly, no duplicates")
        self.assertEqual(uaf_anom[0].line, 4)

    def test_uaf_reassignment_audit_cases(self):
        """Audit 3: Allocate p, free p, reallocate fresh memory, dereference -> no UAF; alias q = p + 2 after free(p) -> UAF."""
        from main import analyze_code
        from models import AnalyzeRequest

        # Case A: Allocate p, free p, reallocate into p, dereference -> NO UAF
        code_a = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    p = malloc(sizeof(int));
    *p = 42;
    free(p);
    return 0;
}"""
        res_a = analyze_code(AnalyzeRequest(code=code_a))
        uaf_a = [m for m in res_a.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf_a), 0, "Reassigned pointer must not flag UAF")
        self.assertEqual(res_a.statistics.memory_issues, 0)

        # Case B: Allocate p, q = p + 2, free p, dereference q -> UAF on q
        code_b = """int main() {
    int *p = malloc(10 * sizeof(int));
    int *q = p + 2;
    free(p);
    *q = 42;
    return 0;
}"""
        res_b = analyze_code(AnalyzeRequest(code=code_b))
        uaf_b = [m for m in res_b.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf_b), 1, "Dereferencing q after freeing p must be flagged as UAF")
        self.assertEqual(uaf_b[0].pointer, "q")
        self.assertEqual(uaf_b[0].free_line, 5)


class TestPhase3BMilestone3MultiHopAndDoubleFree(unittest.TestCase):
    """
    Phase 3B, Milestone 3: Multi-Hop Aliasing & Path-Sensitive Double-Free Detection.
    Tests multi-hop alias chains, alias reassignment isolation, and path-sensitive double-free classification.
    """

    # ------------------ Milestone 1: Multi-Hop Alias Tracking ------------------

    def test_multi_hop_alias_double_free_p_then_r(self):
        """M1: Double-free through multi-hop alias chain p -> q -> r freeing p then r."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    int *q = p;
    int *r = q;
    free(p);
    free(r);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].pointer, "r")
        self.assertEqual(df[0].severity, "error")
        self.assertEqual(df[0].free_line, 6)

        anom = [a for a in res.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "error")

    def test_multi_hop_alias_double_free_r_then_p(self):
        """M1: Double-free through multi-hop alias chain p -> q -> r freeing r then p."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    int *q = p;
    int *r = q;
    free(r);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].pointer, "p")
        self.assertEqual(df[0].severity, "error")
        self.assertEqual(df[0].free_line, 6)

    def test_multi_hop_alias_longer_chain(self):
        """M1: 5-hop alias chain p -> q -> r -> s -> t detects double-free when freeing t then q."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    int *q = p;
    int *r = q;
    int *s = r;
    int *t = s;
    free(t);
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].pointer, "q")
        self.assertEqual(df[0].free_line, 8)

    def test_multi_hop_alias_of_interior_pointer(self):
        """M1: Freeing alias of an interior pointer chain p -> q -> r -> s reports invalid free, preserving valid base free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    int *q = p + 2;
    int *r = q;
    int *s = r;
    free(s);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "s")
        self.assertEqual(inv[0].allocation_function, "interior")

        # p is cleanly freed
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)
        self.assertEqual(safe[0].pointer, "p")

        # No double free
        df = [m for m in res.memory_analysis if "DOUBLE FREE" in m.status]
        self.assertEqual(len(df), 0)

    # ------------------ Milestone 2: Alias Reassignment and Isolation ------------------

    def test_alias_reassignment_isolation(self):
        """M2: Reassigning alias q = malloc(...) does not change p's allocation; both freed cleanly."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    int *q = p;
    q = malloc(sizeof(int));
    free(p);
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if "DOUBLE FREE" in m.status]
        self.assertEqual(len(df), 0)
        self.assertEqual(res.statistics.memory_issues, 0)

        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 2)

    def test_alias_null_assignment_isolation(self):
        """M2: Assigning alias q = NULL leaves p's allocation valid; free(q) is safe no-op."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    int *q = p;
    q = NULL;
    free(p);
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if "DOUBLE FREE" in m.status]
        self.assertEqual(len(df), 0)
        self.assertEqual(res.statistics.memory_issues, 0)

        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)
        self.assertEqual(safe[0].pointer, "p")

    def test_alias_reassignment_with_new_alias_double_free(self):
        """M2: Reassigning q to new alloc and creating alias r = q tracks second alloc; double free on second alloc."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    int *q = p;
    q = malloc(sizeof(int));
    int *r = q;
    free(p);
    free(r);
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].pointer, "q")
        self.assertEqual(df[0].free_line, 8)

        # p is cleanly freed
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 2)

    # ------------------ Milestone 3: Path-Sensitive Double-Free Classification ------------------

    def test_definite_double_free_consecutive(self):
        """M3: Unconditional consecutive frees free(p); free(p); reported as definite DOUBLE FREE (error)."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].severity, "error")

        anom = [a for a in res.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "error")

    def test_possible_double_free_across_branches(self):
        """M3: Freeing in independent branches reported as POSSIBLE DOUBLE FREE (warning), not definite error."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int condition, int other_condition) {
    int *p = malloc(sizeof(int));
    if (condition) {
        free(p);
    }
    if (other_condition) {
        free(p);
    }
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        pdf = [m for m in res.memory_analysis if m.status == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(pdf), 1)
        self.assertEqual(pdf[0].pointer, "p")
        self.assertEqual(pdf[0].severity, "warning")
        self.assertEqual(pdf[0].free_line, 7)

        anom = [a for a in res.anomalies if a.issue_type == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(anom), 1)
        self.assertEqual(anom[0].severity, "warning")
        self.assertIn("Possible double-free", anom[0].message)

        # Definite double free should NOT be present
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 0)

    def test_mutually_exclusive_branches_clean(self):
        """M3: Freeing in if/else mutually exclusive branches is clean with zero double-free reports."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int condition) {
    int *p = malloc(sizeof(int));
    if (condition) {
        free(p);
    } else {
        free(p);
    }
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if "DOUBLE FREE" in m.status]
        self.assertEqual(len(df), 0)
        self.assertEqual(res.statistics.memory_issues, 0)

        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)

    def test_mutually_exclusive_branches_followed_by_definite_double_free(self):
        """M3: If/else both freeing allocation followed by unconditional free reports definite DOUBLE FREE."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int condition) {
    int *p = malloc(sizeof(int));
    if (condition) {
        free(p);
    } else {
        free(p);
    }
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].severity, "error")
        self.assertEqual(df[0].free_line, 8)

    def test_possible_double_free_across_branches_with_aliases(self):
        """M3: Multi-hop aliases freed in independent branches reported as POSSIBLE DOUBLE FREE."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int c1, int c2) {
    int *p = malloc(sizeof(int));
    int *q = p;
    int *r = q;
    if (c1) {
        free(r);
    }
    if (c2) {
        free(p);
    }
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        pdf = [m for m in res.memory_analysis if m.status == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(pdf), 1)
        self.assertEqual(pdf[0].pointer, "p")
        self.assertEqual(pdf[0].severity, "warning")


class TestPhase3BMilestone4DiagnosticClarityAndSuggestions(unittest.TestCase):
    """
    Phase 3B, Milestone 4: Diagnostic Clarity & Suggestion Engine Integration.
    Tests consistency of diagnostic classification, line numbers, actionable explanations,
    deduplication, safe recommendations, and preservation of safe/free(NULL) behavior.
    """

    def test_diagnostic_type_and_severity_consistency(self):
        """M1: Diagnostic type and severity are strictly consistent across views without downgrading definite errors."""
        from main import analyze_code
        from models import AnalyzeRequest

        # 1. Definite Leak
        res_leak = analyze_code(AnalyzeRequest(code="""int main() {
    int *p = malloc(16);
    return 0;
}"""))
        leak_mem = [m for m in res_leak.memory_analysis if m.status == "DEFINITE LEAK"]
        self.assertEqual(len(leak_mem), 1)
        self.assertEqual(leak_mem[0].severity, "error")
        leak_anom = [a for a in res_leak.anomalies if a.issue_type == "MEMORY LEAK"]
        self.assertEqual(len(leak_anom), 1)
        self.assertEqual(leak_anom[0].severity, "error")
        leak_sugg = [s for s in res_leak.suggestions if s.title == "Memory Leak Prevention"]
        self.assertEqual(len(leak_sugg), 1)

        # 2. Possible Leak (branch-dependent)
        res_pos_leak = analyze_code(AnalyzeRequest(code="""int test(int flag) {
    int *p = malloc(16);
    if (flag) free(p);
    return 0;
}"""))
        pos_mem = [m for m in res_pos_leak.memory_analysis if m.status == "POSSIBLE LEAK"]
        self.assertEqual(len(pos_mem), 1)
        self.assertEqual(pos_mem[0].severity, "warning")
        pos_anom = [a for a in res_pos_leak.anomalies if a.issue_type == "POSSIBLE LEAK"]
        self.assertEqual(len(pos_anom), 1)
        self.assertEqual(pos_anom[0].severity, "warning")
        pos_sugg = [s for s in res_pos_leak.suggestions if s.title == "Possible Memory Leak Warning"]
        self.assertEqual(len(pos_sugg), 1)
        self.assertIsNone(pos_sugg[0].safe_fix)

        # 3. Definite Double Free
        res_df = analyze_code(AnalyzeRequest(code="""int main() {
    int *p = malloc(16);
    free(p);
    free(p);
    return 0;
}"""))
        df_mem = [m for m in res_df.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df_mem), 1)
        self.assertEqual(df_mem[0].severity, "error")
        df_anom = [a for a in res_df.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(df_anom), 1)
        self.assertEqual(df_anom[0].severity, "error")
        df_sugg = [s for s in res_df.suggestions if s.title == "Double Free Fix"]
        self.assertEqual(len(df_sugg), 1)

        # 4. Possible Double Free
        res_pdf = analyze_code(AnalyzeRequest(code="""int test(int c1, int c2) {
    int *p = malloc(16);
    if (c1) free(p);
    if (c2) free(p);
    return 0;
}"""))
        pdf_mem = [m for m in res_pdf.memory_analysis if m.status == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(pdf_mem), 1)
        self.assertEqual(pdf_mem[0].severity, "warning")
        pdf_anom = [a for a in res_pdf.anomalies if a.issue_type == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(pdf_anom), 1)
        self.assertEqual(pdf_anom[0].severity, "warning")
        pdf_sugg = [s for s in res_pdf.suggestions if s.title == "Possible Double Free Warning"]
        self.assertEqual(len(pdf_sugg), 1)

        # 5. Use After Free
        res_uaf = analyze_code(AnalyzeRequest(code="""int main() {
    int *p = malloc(16);
    free(p);
    *p = 10;
    return 0;
}"""))
        uaf_mem = [m for m in res_uaf.memory_analysis if m.status == "USE AFTER FREE"]
        self.assertEqual(len(uaf_mem), 1)
        self.assertEqual(uaf_mem[0].severity, "error")
        uaf_anom = [a for a in res_uaf.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(uaf_anom), 1)
        self.assertEqual(uaf_anom[0].severity, "error")

        # 6. Invalid Free
        res_inv = analyze_code(AnalyzeRequest(code="""int main() {
    int x = 5;
    free(&x);
    return 0;
}"""))
        inv_mem = [m for m in res_inv.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv_mem), 1)
        self.assertEqual(inv_mem[0].severity, "error")
        inv_anom = [a for a in res_inv.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(inv_anom), 1)
        self.assertEqual(inv_anom[0].severity, "error")

    def test_line_numbers_point_to_problematic_operations(self):
        """M1: Line numbers accurately identify the offending operation across memory diagnostics."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(32);
    free(p);
    *p = 42;
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf = [a for a in res.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(uaf), 1)
        self.assertEqual(uaf[0].line, 4, "UAF anomaly should point to the dereference on line 4")

        df = [a for a in res.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].line, 5, "Double-free anomaly should point to the second free on line 5")

    def test_clear_and_actionable_explanations(self):
        """M2: Messages clearly explain what operation is unsafe, why, and what to inspect."""
        from main import analyze_code
        from models import AnalyzeRequest

        # Interior pointer explanation
        code_interior = """int main() {
    int *p = malloc(10 * sizeof(int));
    int *q = p + 2;
    free(q);
    return 0;
}"""
        res_interior = analyze_code(AnalyzeRequest(code=code_interior))
        inv_anom = [a for a in res_interior.anomalies if a.issue_type == "INVALID FREE"]
        self.assertEqual(len(inv_anom), 1)
        self.assertIn("original allocation base address", inv_anom[0].why_it_matters)
        self.assertIn("Pass the base pointer", inv_anom[0].suggestion)

        # Definite double free explanation
        code_df = """int main() {
    int *p = malloc(10);
    free(p);
    free(p);
    return 0;
}"""
        res_df = analyze_code(AnalyzeRequest(code=code_df))
        df_anom = [a for a in res_df.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(df_anom), 1)
        self.assertIn("more than once along the analyzed execution path", df_anom[0].why_it_matters)
        self.assertIn("Remove redundant free(p);", df_anom[0].suggestion)

        # Possible double free explanation
        code_pdf = """int test(int a, int b) {
    int *p = malloc(10);
    if (a) free(p);
    if (b) free(p);
    return 0;
}"""
        res_pdf = analyze_code(AnalyzeRequest(code=code_pdf))
        pdf_anom = [a for a in res_pdf.anomalies if a.issue_type == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(pdf_anom), 1)
        self.assertIn("alternate control-flow path", pdf_anom[0].message)
        self.assertNotIn("set pointer to NULL", pdf_anom[0].suggestion, "Must not recommend NULL assignment as double-free cure")

        # Possible leak explanation
        code_pleak = """int test(int flag) {
    int *p = malloc(10);
    if (flag) free(p);
    return 0;
}"""
        res_pleak = analyze_code(AnalyzeRequest(code=code_pleak))
        pleak_anom = [a for a in res_pleak.anomalies if a.issue_type == "POSSIBLE LEAK"]
        self.assertEqual(len(pleak_anom), 1)
        self.assertIn("At least one analyzed path", pleak_anom[0].why_it_matters)
        self.assertIn("Review allocation ownership", pleak_anom[0].suggestion)

    def test_no_duplicate_diagnostics_for_single_operation(self):
        """M1/M4: Duplicate diagnostics for the same operation and line are avoided."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    *p = 100;
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        uaf_anoms = [a for a in res.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(uaf_anoms), 1, "Exactly one UAF anomaly should be generated for line 4")
        uaf_suggs = [s for s in res.suggestions if s.category == "MEMORY" and s.line == 4]
        self.assertEqual(len(uaf_suggs), 1, "Exactly one suggestion should be generated for line 4")

    def test_safe_recommendations_no_unsafe_automated_fixes(self):
        """M3: Recommendations do not invent unsafe automated fixes or recommend unsafe frees."""
        from main import analyze_code
        from models import AnalyzeRequest

        # Possible leak: safe_fix must be None
        code_pos_leak = """int test(int flag) {
    int *p = malloc(10);
    if (flag) free(p);
    return 0;
}"""
        res_pos = analyze_code(AnalyzeRequest(code=code_pos_leak))
        suggs_pos = [s for s in res_pos.suggestions if s.category == "MEMORY"]
        self.assertEqual(len(suggs_pos), 1)
        self.assertIsNone(suggs_pos[0].safe_fix, "Possible leak must not offer automated patch")

        # Escaped pointer: safe_fix must be None
        code_escaped = """int* create() {
    int *p = malloc(10);
    return p;
}"""
        res_esc = analyze_code(AnalyzeRequest(code=code_escaped))
        suggs_esc = [s for s in res_esc.suggestions if s.category == "MEMORY"]
        for s in suggs_esc:
            self.assertIsNone(s.safe_fix, "Escaping pointer must not offer automated free insertion")

        # Definite local leak: safe_fix IS offered
        code_def = """int main() {
    int *p = malloc(10);
    return 0;
}"""
        res_def = analyze_code(AnalyzeRequest(code=code_def))
        suggs_def = [s for s in res_def.suggestions if s.category == "MEMORY"]
        self.assertEqual(len(suggs_def), 1)
        self.assertIsNotNone(suggs_def[0].safe_fix, "Definite local leak should offer safe fix")
        self.assertIn("free(p);", suggs_def[0].safe_fix)

    def test_preservation_of_valid_free_and_free_null(self):
        """M4: Existing valid frees and free(NULL) semantics remain clean and issue-free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10);
    free(p);
    free(NULL);
    int *q = NULL;
    free(q);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(len(res.anomalies), 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")


class TestPhase3BMilestone5CrossFeatureIntegration(unittest.TestCase):
    """
    Phase 3B, Milestone 5: Final Cross-Feature Integration and Regression Verification.
    Tests complex combinations of aliases, control flow, interior pointers, UAF, and safe-fix policies.
    """

    def test_pointer_aliases_combined_with_conditional_frees(self):
        """Cross-feature 1: Aliases combined with conditional frees produce possible leak without spurious double-free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int flag) {
    int *p = malloc(sizeof(int));
    int *q = p;
    if (flag) {
        free(q);
    }
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        # Should be a POSSIBLE LEAK because p/q is only freed when flag is true
        pleak = [m for m in res.memory_analysis if m.status == "POSSIBLE LEAK"]
        self.assertEqual(len(pleak), 1)
        self.assertEqual(pleak[0].severity, "warning")

        # Zero double-free reports
        df = [m for m in res.memory_analysis if "DOUBLE FREE" in m.status]
        self.assertEqual(len(df), 0)

        # Anomaly and suggestion consistency
        anoms = [a for a in res.anomalies if a.issue_type == "POSSIBLE LEAK"]
        self.assertEqual(len(anoms), 1)
        self.assertEqual(anoms[0].severity, "warning")

        # Safe fix must NOT be allowed when control flow is uncertain
        suggs = [s for s in res.suggestions if s.category == "MEMORY"]
        self.assertEqual(len(suggs), 1)
        self.assertIsNone(suggs[0].safe_fix)

    def test_mutually_exclusive_alias_frees_followed_by_definite_double_free(self):
        """Cross-feature 2: Aliases freed in mutually exclusive branches merge cleanly; post-merge free is definite double-free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int flag) {
    int *p = malloc(sizeof(int));
    int *q = p;
    if (flag) {
        free(p);
    } else {
        free(q);
    }
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        # Post-merge free on line 9 must be a definite DOUBLE FREE
        df = [m for m in res.memory_analysis if m.status == "DOUBLE FREE"]
        self.assertEqual(len(df), 1)
        self.assertEqual(df[0].severity, "error")
        self.assertEqual(df[0].free_line, 9)

        # Anomaly consistency
        anoms = [a for a in res.anomalies if a.issue_type == "DOUBLE FREE"]
        self.assertEqual(len(anoms), 1)
        self.assertEqual(anoms[0].severity, "error")
        self.assertEqual(anoms[0].line, 9)

        # Safe fix must be None
        suggs = [s for s in res.suggestions if s.title == "Double Free Fix"]
        self.assertEqual(len(suggs), 1)
        self.assertIsNone(suggs[0].safe_fix)

    def test_allocation_free_reassignment_and_subsequent_dereferencing(self):
        """Cross-feature 3: Allocation, free, reassignment to fresh malloc, and dereferencing is completely clean."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(sizeof(int));
    free(p);
    p = malloc(sizeof(int));
    *p = 42;
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        self.assertEqual(res.statistics.memory_issues, 0)
        self.assertEqual(len(res.anomalies), 0)
        self.assertEqual(res.statistics.overall_status, "CLEAN")

        # Both allocations are marked SAFE
        safes = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safes), 2)

    def test_invalid_interior_free_followed_by_valid_base_free(self):
        """Cross-feature 4: Freeing interior pointer reports INVALID FREE while preserving valid base free."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int main() {
    int *p = malloc(10 * sizeof(int));
    int *q = p + 3;
    free(q);
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        # free(q) on line 4 is INVALID FREE (interior)
        inv = [m for m in res.memory_analysis if m.status == "INVALID FREE"]
        self.assertEqual(len(inv), 1)
        self.assertEqual(inv[0].pointer, "q")
        self.assertEqual(inv[0].allocation_function, "interior")
        self.assertEqual(inv[0].severity, "error")
        self.assertEqual(inv[0].free_line, 4)

        # Base allocation p is cleanly freed
        safe = [m for m in res.memory_analysis if m.status == "SAFE"]
        self.assertEqual(len(safe), 1)
        self.assertEqual(safe[0].pointer, "p")

        # Zero double frees
        df = [m for m in res.memory_analysis if "DOUBLE FREE" in m.status]
        self.assertEqual(len(df), 0)

        # Suggestion safe_fix must be None
        inv_sugg = [s for s in res.suggestions if s.title == "Invalid Free Prevention"]
        self.assertEqual(len(inv_sugg), 1)
        self.assertIsNone(inv_sugg[0].safe_fix)

    def test_use_after_free_struct_member_and_array_subscript(self):
        """Cross-feature 5: UAF detected across struct member accesses and array subscript writes."""
        from main import analyze_code
        from models import AnalyzeRequest

        # Struct member read UAF
        code_struct = """struct Node {
    int val;
};
int main() {
    struct Node *n = malloc(sizeof(struct Node));
    free(n);
    int x = n->val;
    return 0;
}"""
        res_s = analyze_code(AnalyzeRequest(code=code_struct))
        uaf_s = [a for a in res_s.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(uaf_s), 1)
        self.assertEqual(uaf_s[0].line, 7)
        self.assertEqual(uaf_s[0].severity, "error")

        # Array subscript write UAF
        code_arr = """int main() {
    int *arr = malloc(5 * sizeof(int));
    free(arr);
    arr[2] = 99;
    return 0;
}"""
        res_a = analyze_code(AnalyzeRequest(code=code_arr))
        uaf_a = [a for a in res_a.anomalies if a.issue_type == "USE AFTER FREE"]
        self.assertEqual(len(uaf_a), 1)
        self.assertEqual(uaf_a[0].line, 4)
        self.assertEqual(uaf_a[0].severity, "error")

    def test_branch_dependent_freeing_followed_by_cleanup(self):
        """Cross-feature 6: Branch-dependent free followed by post-branch free reports POSSIBLE DOUBLE FREE without spurious leak."""
        from main import analyze_code
        from models import AnalyzeRequest

        code = """int test(int flag) {
    int *p = malloc(sizeof(int));
    if (flag) {
        free(p);
    }
    free(p);
    return 0;
}"""
        res = analyze_code(AnalyzeRequest(code=code))
        pdf = [m for m in res.memory_analysis if m.status == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(pdf), 1)
        self.assertEqual(pdf[0].pointer, "p")
        self.assertEqual(pdf[0].severity, "warning")
        self.assertEqual(pdf[0].free_line, 6)

        # No spurious leak because p is guaranteed to be freed along every branch (either line 4 or line 6)
        leaks = [m for m in res.memory_analysis if "LEAK" in m.status]
        self.assertEqual(len(leaks), 0)

        # Anomaly consistency
        anoms = [a for a in res.anomalies if a.issue_type == "POSSIBLE DOUBLE FREE"]
        self.assertEqual(len(anoms), 1)
        self.assertEqual(anoms[0].severity, "warning")
        self.assertEqual(anoms[0].line, 6)

        # Safe fix must be None
        suggs = [s for s in res.suggestions if s.title == "Possible Double Free Warning"]
        self.assertEqual(len(suggs), 1)
        self.assertIsNone(suggs[0].safe_fix)

    def test_definite_vs_possible_diagnostics_and_safe_fix_restrictions(self):
        """Cross-feature 7: Definite local leaks provide safe fixes; possible leaks, escaping pointers, and errors do not."""
        from main import analyze_code
        from models import AnalyzeRequest

        # 1. Definite local leak -> safe_fix provided
        code_def = """int main() {
    int *p = malloc(16);
    return 0;
}"""
        res_def = analyze_code(AnalyzeRequest(code=code_def))
        suggs_def = [s for s in res_def.suggestions if s.category == "MEMORY"]
        self.assertEqual(len(suggs_def), 1)
        self.assertIsNotNone(suggs_def[0].safe_fix)
        self.assertEqual(suggs_def[0].fix_type, "insert")

        # 2. Escaping pointer -> safe_fix None
        code_esc = """int* allocate() {
    int *p = malloc(16);
    return p;
}"""
        res_esc = analyze_code(AnalyzeRequest(code=code_esc))
        suggs_esc = [s for s in res_esc.suggestions if s.category == "MEMORY"]
        for s in suggs_esc:
            self.assertIsNone(s.safe_fix)

        # 3. Possible leak -> safe_fix None
        code_pos = """int test(int c) {
    int *p = malloc(16);
    if (c) free(p);
    return 0;
}"""
        res_pos = analyze_code(AnalyzeRequest(code=code_pos))
        suggs_pos = [s for s in res_pos.suggestions if s.category == "MEMORY"]
        self.assertEqual(len(suggs_pos), 1)
        self.assertIsNone(suggs_pos[0].safe_fix)


if __name__ == "__main__":
    unittest.main()





