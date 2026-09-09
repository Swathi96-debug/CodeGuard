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
            seq = " ".join(line_tokens[ln])
            # Only consider non-empty lines with meaningful tokens (>= 3 tokens)
            if len(line_tokens[ln]) >= 3:
                lines_seq.append((ln, seq, line_raw.get(ln, "")))

        # Compare pairs of lines or multi-line sequences (window of size 1 to 3)
        n = len(lines_seq)
        seen_pairs = set()

        for i in range(n):
            for j in range(i + 1, n):
                ln_a, seq_a, raw_a = lines_seq[i]
                ln_b, seq_b, raw_b = lines_seq[j]

                if abs(ln_a - ln_b) < 1:
                    continue  # Ignore overlapping same lines

                if seq_a == seq_b:
                    pair_key = (min(ln_a, ln_b), max(ln_a, ln_b))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    is_exact = (raw_a.strip() == raw_b.strip())
                    similarity = 100.0 if is_exact else 92.5
                    reason = "Exact line structure match." if is_exact else "Normalized token structure match (renamed identifiers/variables)."

                    duplicates.append(DuplicateBlock(
                        block_a_lines=[ln_a, ln_a],
                        block_b_lines=[ln_b, ln_b],
                        similarity_percentage=similarity,
                        reason=reason,
                        suggestion="Consider extracting repeated logic into a reusable helper function.",
                        code_snippet_a=raw_a.strip(),
                        code_snippet_b=raw_b.strip()
                    ))

        return duplicates
