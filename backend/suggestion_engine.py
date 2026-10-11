from typing import List, Tuple, Optional
from models import SyntaxIssue, SemanticIssue, MemoryAllocation, DuplicateBlock, Anomaly, SuggestionItem

class SuggestionEngine:
    def __init__(
        self,
        raw_code: str,
        syntax_issues: List[SyntaxIssue],
        semantic_issues: List[SemanticIssue],
        memory_analysis: List[MemoryAllocation],
        duplications: List[DuplicateBlock]
    ):
        self.raw_code = raw_code
        self.lines = raw_code.splitlines()
        self.syntax_issues = syntax_issues
        self.semantic_issues = semantic_issues
        self.memory_analysis = memory_analysis
        self.duplications = duplications

    def generate(self) -> Tuple[List[Anomaly], List[SuggestionItem]]:
        anomalies: List[Anomaly] = []
        suggestions: List[SuggestionItem] = []
        anomaly_id = 1
        suggestion_id = 1

        # 1. Syntax Issues
        for syn in self.syntax_issues:
            why = "Syntax errors prevent the compiler from building a valid Abstract Syntax Tree and executing the program."
            anomalies.append(Anomaly(
                id=anomaly_id,
                issue_type="SYNTAX",
                severity=syn.severity,
                line=syn.line,
                column=syn.column,
                message=syn.message,
                why_it_matters=why,
                suggestion=syn.suggestion
            ))
            anomaly_id += 1

            # Determine if a safe, precise fix is available
            safe_fix = None
            orig_snippet = None
            fixed_snippet = None
            fix_type = None
            fix_explanation = None
            target_line = None

            if "Missing semicolon" in syn.message:
                fix_info = self._get_missing_semicolon_fix(syn.line)
                if fix_info:
                    orig_snippet, fixed_snippet, safe_fix, fix_type, fix_explanation, target_line = fix_info

            suggestions.append(SuggestionItem(
                id=suggestion_id,
                title="Syntax Error Fix",
                message=syn.message,
                suggestion=syn.suggestion,
                line=syn.line,
                safe_fix=safe_fix,
                category="SYNTAX",
                original_snippet=orig_snippet,
                fixed_snippet=fixed_snippet,
                fix_explanation=fix_explanation,
                fix_type=fix_type,
                target_line=target_line
            ))
            suggestion_id += 1

        # 2. Semantic Issues
        for sem in self.semantic_issues:
            why = "Semantic violations break language rules such as variable scoping, type safety, or declaration order."
            anomalies.append(Anomaly(
                id=anomaly_id,
                issue_type="SEMANTIC",
                severity=sem.severity,
                line=sem.line,
                column=sem.column,
                message=sem.message,
                why_it_matters=why,
                suggestion=sem.suggestion
            ))
            anomaly_id += 1

            # Only provide safe_fix when strictly safe and justified (e.g. missing function prototype)
            safe_fix = None
            orig_snippet = None
            fixed_snippet = None
            fix_type = None
            fix_explanation = None
            target_line = None

            suggestions.append(SuggestionItem(
                id=suggestion_id,
                title="Semantic Error Fix",
                message=sem.message,
                suggestion=sem.suggestion,
                line=sem.line,
                safe_fix=safe_fix,
                category="SEMANTIC",
                original_snippet=orig_snippet,
                fixed_snippet=fixed_snippet,
                fix_explanation=fix_explanation,
                fix_type=fix_type,
                target_line=target_line
            ))
            suggestion_id += 1

        # 3. Memory Issues
        for mem in self.memory_analysis:
            if mem.status in ("POSSIBLE LEAK", "DEFINITE LEAK"):
                is_definite = mem.status == "DEFINITE LEAK"
                if is_definite:
                    msg = f"Memory allocated to pointer '{mem.pointer}' via {mem.allocation_function}() is definitely leaked (pointer overwritten or lost to scope exit)."
                else:
                    msg = f"Memory allocated to pointer '{mem.pointer}' via {mem.allocation_function}() was not freed or may leak on failure."
                why = "Unreleased memory allocations stay occupied on the heap, leading to memory leaks and resource depletion."
                sugg = f"Add free({mem.pointer}); before overwriting or exiting scope."
                
                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type="MEMORY LEAK",
                    severity="error" if is_definite else "warning",
                    line=mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                # Safe fixes only: do not automatically suggest free(ptr) unless safely justified
                safe_fix = None
                orig_snippet = None
                fixed_snippet = None
                fix_type = None
                fix_explanation = None
                target_line = None

                free_info = self._get_safe_free_fix(mem.pointer, mem.allocation_line)
                if free_info:
                    orig_snippet, fixed_snippet, safe_fix, fix_type, fix_explanation, target_line = free_info

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title="Memory Leak Prevention",
                    message=msg,
                    suggestion=sugg,
                    line=mem.allocation_line,
                    safe_fix=safe_fix,
                    category="MEMORY",
                    original_snippet=orig_snippet,
                    fixed_snippet=fixed_snippet,
                    fix_explanation=fix_explanation,
                    fix_type=fix_type,
                    target_line=target_line
                ))
                suggestion_id += 1

            elif mem.status == "DOUBLE FREE":
                msg = f"Pointer '{mem.pointer}' freed multiple times."
                why = "Calling free() twice on the same memory pointer leads to heap corruption and undefined behavior."
                sugg = f"Ensure free({mem.pointer}); is executed exactly once per allocation."

                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type="DOUBLE FREE",
                    severity="error",
                    line=mem.free_line or mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title="Double Free Fix",
                    message=msg,
                    suggestion=sugg,
                    line=mem.free_line or mem.allocation_line,
                    safe_fix=None,
                    category="MEMORY"
                ))
                suggestion_id += 1

            elif mem.status == "USE AFTER FREE":
                msg = f"Use-after-free: pointer '{mem.pointer}' is accessed/dereferenced on line {mem.free_line or mem.allocation_line} after its memory has been freed."
                why = "Dereferencing a pointer to freed memory causes heap corruption, undefined behavior, crashes, or security exploits."
                sugg = f"Do not access '{mem.pointer}' after calling free(); set pointer to NULL or allocate fresh memory before dereferencing."

                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type="USE AFTER FREE",
                    severity="error",
                    line=mem.free_line or mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title="Use-After-Free Prevention",
                    message=msg,
                    suggestion=sugg,
                    line=mem.free_line or mem.allocation_line,
                    safe_fix=None,
                    category="MEMORY"
                ))
                suggestion_id += 1

            elif mem.status == "INVALID FREE":
                msg = f"Invalid free: attempted to free pointer '{mem.pointer}' on line {mem.free_line or mem.allocation_line}, which does not reference a valid dynamic heap allocation."
                why = "Calling free() on a stack, local, or unallocated pointer causes heap corruption, abort signals, and runtime crashes."
                sugg = f"Do not call free({mem.pointer}); only heap memory allocated via malloc, calloc, or realloc may be passed to free()."

                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type="INVALID FREE",
                    severity="error",
                    line=mem.free_line or mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title="Invalid Free Prevention",
                    message=msg,
                    suggestion=sugg,
                    line=mem.free_line or mem.allocation_line,
                    safe_fix=None,
                    category="MEMORY"
                ))
                suggestion_id += 1

            elif mem.status == "ESCAPED":
                msg = f"Memory allocated to pointer '{mem.pointer}' via {mem.allocation_function}() escapes local function scope via return."
                why = "Ownership of the heap memory escapes to the calling function, which assumes responsibility for freeing it."
                sugg = f"Ensure caller invokes free({mem.pointer}); after usage."

                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type="MEMORY ESCAPE",
                    severity="info",
                    line=mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title="Escaping Pointer Ownership",
                    message=msg,
                    suggestion=sugg,
                    line=mem.allocation_line,
                    safe_fix=None,
                    category="MEMORY"
                ))
                suggestion_id += 1

        # 4. Duplication Issues
        for dup in self.duplications:
            msg = f"Duplicate code detected between lines {dup.block_a_lines[0]} and {dup.block_b_lines[0]} ({dup.similarity_percentage}% similarity)."
            why = "Duplicated code increases maintenance burden and makes bug fixes prone to being omitted in copies."
            sugg = dup.suggestion

            anomalies.append(Anomaly(
                id=anomaly_id,
                issue_type="DUPLICATION",
                severity="info",
                line=dup.block_b_lines[0],
                column=1,
                message=msg,
                why_it_matters=why,
                suggestion=sugg
            ))
            anomaly_id += 1

            suggestions.append(SuggestionItem(
                id=suggestion_id,
                title="Code Refactoring Suggestion",
                message=msg,
                suggestion=sugg,
                line=dup.block_b_lines[0],
                safe_fix=None,
                category="DUPLICATION"
            ))
            suggestion_id += 1

        return anomalies, suggestions

    def _get_missing_semicolon_fix(self, line: int):
        """Returns safe fix details for a missing semicolon on line."""
        if 0 <= line - 1 < len(self.lines):
            orig = self.lines[line - 1]
            if not orig.rstrip().endswith(";"):
                fixed = orig.rstrip() + ";"
                explanation = f"Appends a statement terminator ';' to line {line}."
                return (orig, fixed, fixed, "replace", explanation, line)
        return None

    def _get_safe_free_fix(self, pointer: str, alloc_line: int):
        """
        Only offers an automatic safe-fix insertion when justified and safe:
        - Pointer is a valid identifier (not unknown)
        - Allocation is purely local to a function with a clear return statement before exit
        - Pointer is not returned as a value (e.g. return ptr;)
        """
        if not pointer or pointer == "unknown_ptr":
            return None

        # Check subsequent lines within the same function
        n = len(self.lines)
        for idx in range(alloc_line, min(n, alloc_line + 50)):
            line_str = self.lines[idx].strip()
            # If the pointer is returned, it escapes local ownership - NOT safe to free before return!
            if line_str.startswith("return"):
                if pointer in line_str:
                    return None  # Escaping pointer, unsafe to free!
                
                # Safe to insert free immediately before return
                indent = " " * (len(self.lines[idx]) - len(self.lines[idx].lstrip()))
                inserted = f"{indent}free({pointer});"
                explanation = f"Frees allocated heap buffer '{pointer}' before exiting function scope at line {idx + 1}."
                return ("", inserted, inserted, "insert", explanation, idx + 1)

            # If function ended without return
            if line_str == "}":
                indent = "    "
                inserted = f"{indent}free({pointer});"
                explanation = f"Frees allocated heap buffer '{pointer}' before block close at line {idx + 1}."
                return ("", inserted, inserted, "insert", explanation, idx + 1)

        return None
