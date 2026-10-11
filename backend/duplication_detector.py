from typing import List, Dict, Tuple, Set, Optional
import difflib
from models import Token, DuplicateBlock

class DuplicationDetector:
    """
    Detects duplicated and near-duplicated code blocks in C source code:
    - Type 1 Clones: Exact repeated code blocks (ignoring whitespace and formatting differences).
    - Type 2 Clones: Structural clones with renamed identifiers and minor literal differences.
    - Cross-function duplication: Repeated logic in different functions.
    - Prevents overlapping duplicate reports and suppresses trivial boilerplate.
    """

    def __init__(self, raw_code: str, tokens: List[Token]):
        self.raw_code = raw_code
        self.code_lines = raw_code.splitlines()
        # Filter out preprocessor tokens for duplication scanning
        self.tokens = [t for t in tokens if t.token_type != "PREPROCESSOR"]

    def detect(self) -> List[DuplicateBlock]:
        duplicates: List[DuplicateBlock] = []
        if not self.tokens:
            return duplicates

        # Group tokens by line
        line_tokens: Dict[int, List[Token]] = {}
        line_raw: Dict[int, str] = {}

        for tok in self.tokens:
            if tok.line not in line_tokens:
                line_tokens[tok.line] = []
                line_raw[tok.line] = self.code_lines[tok.line - 1] if 0 <= tok.line - 1 < len(self.code_lines) else ""
            line_tokens[tok.line].append(tok)

        # Normalize tokens per line
        # Normalized: IDENTIFIER -> "ID", INT/FLOAT -> "NUMBER", STRING/CHAR -> "LITERAL"
        lines_seq = []
        line_numbers = sorted(line_tokens.keys())

        for ln in line_numbers:
            toks = line_tokens[ln]
            # Ignore solitary brace/semicolon lines (e.g. "}", "{", ";")
            meaningful_toks = [t for t in toks if t.lexeme not in ("{", "}", ";")]
            if not meaningful_toks:
                continue

            norm_tokens = []
            for t in toks:
                if t.token_type == "IDENTIFIER":
                    norm_tokens.append("ID")
                elif t.token_type in ("INT_CONSTANT", "FLOAT_CONSTANT"):
                    norm_tokens.append("NUMBER")
                elif t.token_type in ("STRING_LITERAL", "CHAR_LITERAL"):
                    norm_tokens.append("LITERAL")
                else:
                    norm_tokens.append(t.lexeme)

            norm_seq = " ".join(norm_tokens)
            lines_seq.append((ln, norm_seq, line_raw.get(ln, ""), toks))

        n = len(lines_seq)
        if n < 2:
            return duplicates

        reported_ranges: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []
        max_window = min(50, n // 2)

        for window in range(max_window, 1, -1):
            for i in range(n - window + 1):
                ln_a_start = lines_seq[i][0]
                ln_a_end = lines_seq[i + window - 1][0]
                range_a = (ln_a_start, ln_a_end)

                # Skip if block A is already a sub-block of a reported duplication
                if any(r_a[0] <= ln_a_start and ln_a_end <= r_a[1] for r_a, _ in reported_ranges):
                    continue

                # Token count of candidate block
                block_a_toks = [t for k in range(window) for t in lines_seq[i + k][3]]
                total_tokens = len(block_a_toks)

                # Boilerplate filter: require >= 10 tokens for window >= 3, or >= 12 for window == 2
                if window == 2 and total_tokens < 12:
                    continue
                if window >= 3 and total_tokens < 10:
                    continue

                # Ensure block contains substantive statements (not just empty declarations)
                has_operation = any(
                    t.token_type == "OPERATOR" or t.lexeme in ("if", "while", "for", "return", "(", ")")
                    for t in block_a_toks
                )
                if not has_operation:
                    continue

                block_a_seq = [lines_seq[i + k][1] for k in range(window)]

                for j in range(i + window, n - window + 1):
                    ln_b_start = lines_seq[j][0]
                    ln_b_end = lines_seq[j + window - 1][0]
                    range_b = (ln_b_start, ln_b_end)

                    # Check if this pair or a superset pair was already reported
                    if any(
                        (r_a[0] <= ln_a_start and ln_a_end <= r_a[1] and r_b[0] <= ln_b_start and ln_b_end <= r_b[1]) or
                        (r_a[0] <= ln_b_start and ln_b_end <= r_a[1] and r_b[0] <= ln_a_start and ln_a_end <= r_b[1])
                        for r_a, r_b in reported_ranges
                    ):
                        continue

                    block_b_seq = [lines_seq[j + k][1] for k in range(window)]

                    if block_a_seq == block_b_seq:
                        # Extract code snippets
                        snippet_a = "\n".join(lines_seq[i + k][2].rstrip() for k in range(window))
                        snippet_b = "\n".join(lines_seq[j + k][2].rstrip() for k in range(window))

                        block_b_toks = [t for k in range(window) for t in lines_seq[j + k][3]]
                        raw_a_lexemes = [t.lexeme for t in block_a_toks]
                        raw_b_lexemes = [t.lexeme for t in block_b_toks]

                        # Calculate similarity percentage
                        if raw_a_lexemes == raw_b_lexemes:
                            is_exact = True
                            similarity = 100.0
                            reason = (
                                f"Exact code block duplication across lines {ln_a_start}-{ln_a_end} "
                                f"and {ln_b_start}-{ln_b_end} ({window} lines)."
                            )
                        else:
                            is_exact = False
                            matcher = difflib.SequenceMatcher(None, raw_a_lexemes, raw_b_lexemes)
                            ratio = matcher.ratio() * 100.0
                            # Structural match with renamed identifiers/literals
                            similarity = round(max(80.0, min(99.0, 75.0 + 0.25 * ratio)), 1)
                            reason = (
                                f"Structural clone with renamed identifiers or literals across lines "
                                f"{ln_a_start}-{ln_a_end} and {ln_b_start}-{ln_b_end} ({window} lines)."
                            )

                        duplicates.append(DuplicateBlock(
                            block_a_lines=[ln_a_start, ln_a_end],
                            block_b_lines=[ln_b_start, ln_b_end],
                            similarity_percentage=similarity,
                            reason=reason,
                            suggestion="Consider extracting repeated logic into a reusable helper function or consolidating common logic.",
                            code_snippet_a=snippet_a,
                            code_snippet_b=snippet_b
                        ))

                        reported_ranges.append((range_a, range_b))
                        break

        return duplicates
