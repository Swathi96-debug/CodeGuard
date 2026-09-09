from typing import List, Dict
from models import Token, MemoryAllocation

class MemoryAnalyzer:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.allocations: List[MemoryAllocation] = []

    def analyze(self) -> List[MemoryAllocation]:
        self.allocations = []
        n = len(self.tokens)

        # Track allocations map: pointer_name -> MemoryAllocation
        alloc_map: Dict[str, MemoryAllocation] = {}

        i = 0
        while i < n:
            tok = self.tokens[i]

            # Detect allocation: p = malloc(...) or int *p = malloc(...)
            if tok.lexeme in ("malloc", "calloc", "realloc"):
                alloc_fn = tok.lexeme
                alloc_line = tok.line
                
                # Find target pointer variable name on left side of '='
                ptr_name = "unknown_ptr"
                # Search backwards for identifier before '='
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

                # Record allocation
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
                self.allocations.append(alloc_obj)

            # Detect free: free(p)
            elif tok.lexeme == "free":
                free_line = tok.line
                # Look inside parenthesis for pointer identifier e.g. free(p)
                freed_ptr = None
                if i + 2 < n and self.tokens[i+1].lexeme == "(" and self.tokens[i+2].token_type == "IDENTIFIER":
                    freed_ptr = self.tokens[i+2].lexeme

                if freed_ptr:
                    if freed_ptr in alloc_map:
                        existing = alloc_map[freed_ptr]
                        if existing.freed:
                            # Double Free!
                            double_free_obj = MemoryAllocation(
                                pointer=freed_ptr,
                                allocation_function=existing.allocation_function,
                                allocation_line=existing.allocation_line,
                                freed=True,
                                free_line=free_line,
                                status="DOUBLE FREE",
                                severity="error"
                            )
                            self.allocations.append(double_free_obj)
                        else:
                            existing.freed = True
                            existing.free_line = free_line
                            existing.status = "SAFE"
                            existing.severity = "safe"
                    else:
                        # Invalid free of unallocated pointer
                        invalid_free_obj = MemoryAllocation(
                            pointer=freed_ptr,
                            allocation_function="None",
                            allocation_line=0,
                            freed=True,
                            free_line=free_line,
                            status="INVALID FREE",
                            severity="error"
                        )
                        self.allocations.append(invalid_free_obj)

            i += 1

        return self.allocations
