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
        seen_mem_diagnostics = set()
        for mem in self.memory_analysis:
            diag_line = mem.free_line or mem.allocation_line
            diag_key = (mem.status, mem.pointer, diag_line)
            if diag_key in seen_mem_diagnostics:
                continue
            seen_mem_diagnostics.add(diag_key)

            if mem.status in ("POSSIBLE LEAK", "DEFINITE LEAK"):
                is_definite = mem.status == "DEFINITE LEAK"
                if is_definite:
                    issue_type = "MEMORY LEAK"
                    severity = "error"
                    title = "Memory Leak Prevention"
                    msg = f"Definite memory leak: memory allocated to pointer '{mem.pointer}' via {mem.allocation_function}() is definitely leaked (pointer overwritten or lost to scope exit)."
                    why = "Unreleased heap memory stays occupied until program termination, leading to memory exhaustion and resource depletion."
                    sugg = f"Add free({mem.pointer}); before overwriting or exiting scope."
                else:
                    issue_type = "POSSIBLE LEAK"
                    severity = "warning"
                    title = "Possible Memory Leak Warning"
                    msg = f"Possible memory leak: memory allocated to pointer '{mem.pointer}' via {mem.allocation_function}() may remain unreleased on at least one analyzed execution path."
                    why = "At least one analyzed path (such as a conditional branch, loop, or early exit) may leave this allocation unreleased."
                    sugg = f"Review allocation ownership and all exit paths to ensure '{mem.pointer}' is freed on every execution path, or verify error and branch handling."

                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type=issue_type,
                    severity=severity,
                    line=mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                # Safe fixes only: only offer automatic fix when strictly safe and local (never for possible leaks)
                safe_fix = None
                orig_snippet = None
                fixed_snippet = None
                fix_type = None
                fix_explanation = None
                target_line = None

                if is_definite:
                    free_info = self._get_safe_free_fix(mem.pointer, mem.allocation_line)
                    if free_info:
                        orig_snippet, fixed_snippet, safe_fix, fix_type, fix_explanation, target_line = free_info

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title=title,
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

            elif mem.status in ("DOUBLE FREE", "POSSIBLE DOUBLE FREE"):
                is_definite = mem.status == "DOUBLE FREE"
                if is_definite:
                    msg = f"Definite double-free: pointer '{mem.pointer}' releases an allocation that has already been freed along the analyzed execution path."
                    issue_type = "DOUBLE FREE"
                    severity = "error"
                    title = "Double Free Fix"
                    why = "The same allocation is released more than once along the analyzed execution path, causing heap corruption and undefined behavior."
                    sugg = f"Remove redundant free({mem.pointer}); calls so the allocation is released exactly once along this execution path."
                else:
                    msg = f"Possible double-free: pointer '{mem.pointer}' may have already been freed along an alternate control-flow path."
                    issue_type = "POSSIBLE DOUBLE FREE"
                    severity = "warning"
                    title = "Possible Double Free Warning"
                    why = "The allocation may already have been released on another execution path; calling free() again along an intersecting path causes heap corruption."
                    sugg = f"Review control-flow paths to ensure '{mem.pointer}' (and its aliases) is freed at most once across all branches, or restructure branches to be mutually exclusive."

                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type=issue_type,
                    severity=severity,
                    line=mem.free_line or mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title=title,
                    message=msg,
                    suggestion=sugg,
                    line=mem.free_line or mem.allocation_line,
                    safe_fix=None,
                    category="MEMORY"
                ))
                suggestion_id += 1

            elif mem.status == "USE AFTER FREE":
                msg = f"Use-after-free: pointer '{mem.pointer}' is accessed or dereferenced on line {mem.free_line or mem.allocation_line} after its memory has been released."
                why = "The pointer refers to an allocation that has already been released; accessing freed memory causes undefined behavior, heap corruption, or security vulnerabilities."
                sugg = f"Inspect the access to '{mem.pointer}' and its allocation lifetime; ensure the memory is not accessed after calling free(), or restructure the code so the allocation outlives all accesses."

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
                if mem.allocation_function == "string_literal":
                    msg = f"Invalid free: attempted to free string literal or read-only memory '{mem.pointer}' on line {mem.free_line or mem.allocation_line}."
                    why = "free() requires a dynamically allocated heap address; string literals reside in read-only memory (.rodata) and must not be freed."
                    sugg = f"Do not call free({mem.pointer}); string literals are statically managed and cannot be released."
                elif mem.allocation_function == "global":
                    msg = f"Invalid free: attempted to free static/global variable address '{mem.pointer}' on line {mem.free_line or mem.allocation_line}."
                    why = "free() requires a dynamic heap allocation address; global and static variables reside in fixed memory segments (.data/.bss) and must not be freed."
                    sugg = f"Do not call free({mem.pointer}); only dynamic heap allocations from malloc(), calloc(), or realloc() may be passed to free()."
                elif mem.allocation_function == "interior":
                    msg = f"Invalid free: attempted to free interior/offset pointer '{mem.pointer}' on line {mem.free_line or mem.allocation_line}."
                    why = "free() requires the original allocation base address returned by malloc(), calloc(), or realloc(); an interior pointer must not be freed."
                    sugg = f"Pass the base pointer returned by dynamic allocation to free(), not an interior or offset pointer."
                else:
                    msg = f"Invalid free: attempted to free pointer '{mem.pointer}' on line {mem.free_line or mem.allocation_line}, which does not reference a valid dynamic heap allocation."
                    why = "free() requires the original allocation address; stack, local, or unallocated addresses must not be freed. Calling free() on a stack, local, or unallocated pointer causes heap corruption, abort signals, and runtime crashes."
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
