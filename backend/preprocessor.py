import re

class Preprocessor:
    @staticmethod
    def process(source_code: str) -> str:
        """
        Removes single-line (//...) and multi-line (/*...*/) comments from C source code.
        Preserves line numbers by replacing removed content with corresponding newlines or spaces.
        """
        result = []
        i = 0
        length = len(source_code)
        
        in_single_comment = False
        in_multi_comment = False
        in_string = False
        in_char = False

        out_chars = []

        while i < length:
            ch = source_code[i]
            next_ch = source_code[i+1] if i + 1 < length else ''

            if in_single_comment:
                if ch == '\n':
                    in_single_comment = False
                    out_chars.append('\n')
                else:
                    out_chars.append(' ')
                i += 1
                continue

            if in_multi_comment:
                if ch == '*' and next_ch == '/':
                    in_multi_comment = False
                    out_chars.append(' ')
                    out_chars.append(' ')
                    i += 2
                else:
                    if ch == '\n':
                        out_chars.append('\n')
                    else:
                        out_chars.append(' ')
                    i += 1
                continue

            if in_string:
                out_chars.append(ch)
                if ch == '\\' and i + 1 < length:
                    out_chars.append(source_code[i+1])
                    i += 2
                    continue
                if ch == '"':
                    in_string = False
                i += 1
                continue

            if in_char:
                out_chars.append(ch)
                if ch == '\\' and i + 1 < length:
                    out_chars.append(source_code[i+1])
                    i += 2
                    continue
                if ch == "'":
                    in_char = False
                i += 1
                continue

            # Check string/char literal start
            if ch == '"':
                in_string = True
                out_chars.append(ch)
                i += 1
                continue

            if ch == "'":
                in_char = True
                out_chars.append(ch)
                i += 1
                continue

            # Check single line comment start
            if ch == '/' and next_ch == '/':
                in_single_comment = True
                out_chars.append(' ')
                out_chars.append(' ')
                i += 2
                continue

            # Check multi line comment start
            if ch == '/' and next_ch == '*':
                in_multi_comment = True
                out_chars.append(' ')
                out_chars.append(' ')
                i += 2
                continue

            out_chars.append(ch)
            i += 1

        return "".join(out_chars)
