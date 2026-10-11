from typing import List, Dict
from models import Token, DuplicateBlock

class DuplicationDetector:
    def __init__(self, raw_code: str, tokens: List[Token]):
        self.raw_code = raw_code
        self.code_lines = raw_code.splitlines()
        self.tokens = tokens

    def detect(self) -> List[DuplicateBlock]:
        duplicates: List[DuplicateBlock] = []

        # Group tokens by line
        line_tokens: Dict[int, List[str]] = {}
        line_raw: Dict[int, str] = {}

        for tok in self.tokens:
            if tok.line not in line_tokens:
                line_tokens[tok.line] = []
                line_raw[tok.line] = self.code_lines[tok.line - 1] if 0 <= tok.line - 1 < len(self.code_lines) else ""
            
            # Normalize lexemes
            if tok.token_type == "IDENTIFIER":
                line_tokens[tok.line].append("ID")
            elif tok.token_type in ("INT_CONSTANT", "FLOAT_CONSTANT"):
                line_tokens[tok.line].append("NUMBER")
            else:
                line_tokens[tok.line].append(tok.lexeme)

        # Convert lines to normalized token strings
        lines_seq = []
        line_numbers = sorted(line_tokens.keys())

        for ln in line_numbers:
            # Only consider non-empty lines with meaningful tokens (>= 3 tokens)
            if len(line_tokens[ln]) >= 3:
                seq = " ".join(line_tokens[ln])
                lines_seq.append((ln, seq, line_raw.get(ln, "")))

        n = len(lines_seq)
        matched_indices_a = set()
        matched_indices_b = set()

        # Multi-line block detection (window size >= 2 down to 2)
        # Prevents false-positive single-line matches (e.g. adjacent variable declarations)
        max_window = min(10, n // 2)
        for window in range(max_window, 1, -1):
            for i in range(n - window + 1):
                if any(idx in matched_indices_a for idx in range(i, i + window)):
                    continue
                token_count = sum(len(line_tokens[lines_seq[i + k][0]]) for k in range(window))
                if window < 3 and token_count < 12:
                    continue
                block_a_seq = [lines_seq[i + k][1] for k in range(window)]
                for j in range(i + window, n - window + 1):
                    if any(idx in matched_indices_b for idx in range(j, j + window)):
                        continue
                    block_b_seq = [lines_seq[j + k][1] for k in range(window)]
                    if block_a_seq == block_b_seq:
                        for k in range(window):
                            matched_indices_a.add(i + k)
                            matched_indices_b.add(j + k)
                        
                        ln_a_start = lines_seq[i][0]
                        ln_a_end = lines_seq[i + window - 1][0]
                        ln_b_start = lines_seq[j][0]
                        ln_b_end = lines_seq[j + window - 1][0]
                        
                        snippet_a = "\n".join(lines_seq[i + k][2].strip() for k in range(window))
                        snippet_b = "\n".join(lines_seq[j + k][2].strip() for k in range(window))
                        
                        is_exact = (snippet_a == snippet_b)
                        similarity = 100.0 if is_exact else 92.5
                        reason = (
                            f"Exact multi-line block match ({window} lines)."
                            if is_exact else
                            f"Normalized token block match ({window} lines with renamed variables)."
                        )
                        
                        duplicates.append(DuplicateBlock(
                            block_a_lines=[ln_a_start, ln_a_end],
                            block_b_lines=[ln_b_start, ln_b_end],
                            similarity_percentage=similarity,
                            reason=reason,
                            suggestion="Consider extracting repeated logic into a reusable helper function.",
                            code_snippet_a=snippet_a,
                            code_snippet_b=snippet_b
                        ))
                        break

        return duplicates
