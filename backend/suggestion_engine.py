from typing import List, Tuple
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

            # Safe fix for missing semicolon
            safe_fix = None
            if "Missing semicolon" in syn.message:
                safe_fix = self._apply_missing_semicolon_fix(syn.line)

            suggestions.append(SuggestionItem(
                id=suggestion_id,
                title="Syntax Error Fix",
                message=syn.message,
                suggestion=syn.suggestion,
                line=syn.line,
                safe_fix=safe_fix,
                category="SYNTAX"
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

            safe_fix = None
            if "Undeclared variable" in sem.message:
                var_name = sem.message.split("'")[1] if "'" in sem.message else ""
                if var_name:
                    safe_fix = f"int {var_name} = 0;"

            suggestions.append(SuggestionItem(
                id=suggestion_id,
                title="Semantic Error Fix",
                message=sem.message,
                suggestion=sem.suggestion,
                line=sem.line,
                safe_fix=safe_fix,
                category="SEMANTIC"
            ))
            suggestion_id += 1

        # 3. Memory Issues
        for mem in self.memory_analysis:
            if mem.status == "POSSIBLE LEAK":
                msg = f"Memory allocated to pointer '{mem.pointer}' via {mem.allocation_function}() was not freed."
                why = "Unreleased memory allocations stay occupied on the heap, leading to memory leaks and resource depletion."
                sugg = f"Add free({mem.pointer}); after usage."
                
                anomalies.append(Anomaly(
                    id=anomaly_id,
                    issue_type="MEMORY LEAK",
                    severity="warning",
                    line=mem.allocation_line,
                    column=1,
                    message=msg,
                    why_it_matters=why,
                    suggestion=sugg
                ))
                anomaly_id += 1

                suggestions.append(SuggestionItem(
                    id=suggestion_id,
                    title="Memory Leak Prevention",
                    message=msg,
                    suggestion=sugg,
                    line=mem.allocation_line,
                    safe_fix=f"free({mem.pointer});",
                    category="MEMORY"
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

    def _apply_missing_semicolon_fix(self, line: int) -> str:
        lines = self.raw_code.splitlines()
        if 0 <= line - 1 < len(lines):
            target_line = lines[line - 1]
            if not target_line.rstrip().endswith(";"):
                return target_line.rstrip() + ";"
        return ""
