import re
from typing import List, Tuple


class SyntaxValidator:
    """Performs static syntax verification on patched files to reject corrupted files early."""

    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate C++ code blocks for brace, parenthesis, and bracket balance.

        Returns
        -------
        (success, errors) : Tuple[bool, List[str]]
        """
        errors = []

        # Remove string literals and comments to prevent false matching in comments/strings
        cleaned_code = self._clean_code(code)

        # 1. Balanced character verification
        stack = []
        mapping = {')': '(', '}': '{', ']': '['}
        line_numbers = self._get_line_numbers_mapping(code)

        for idx, char in enumerate(cleaned_code):
            if char in '({[':
                stack.append((char, idx))
            elif char in ')}]':
                expected = mapping[char]
                if not stack:
                    line_no = line_numbers[idx]
                    errors.append(f"Mismatched closing character '{char}' at line {line_no}")
                else:
                    top, _ = stack.pop()
                    if top != expected:
                        line_no = line_numbers[idx]
                        errors.append(
                            f"Mismatched closing character '{char}' (expected closing for '{top}') at line {line_no}"
                        )

        while stack:
            top, idx = stack.pop()
            line_no = line_numbers[idx]
            errors.append(f"Unclosed opening character '{top}' at line {line_no}")

        # 2. Check for basic preprocessor directives syntax
        errors.extend(self._validate_preprocessor(code))

        success = len(errors) == 0
        return success, errors

    def _clean_code(self, code: str) -> str:
        # Regex to strip single-line and multi-line comments
        no_comments = re.sub(r'(/\*([^*]|(\*+[^*/]))*\*+/)|(//.*)', '', code)
        
        # Strip string and character literals
        # Match double quoted string or single quoted char
        no_strings = re.sub(r'("(?:\\.|[^"\\])*")|(\'(?:\\.|[^\'\\])*\')', '""', no_comments)
        return no_strings

    def _get_line_numbers_mapping(self, code: str) -> List[int]:
        mapping = []
        current_line = 1
        for char in code:
            mapping.append(current_line)
            if char == '\n':
                current_line += 1
        return mapping

    def _validate_preprocessor(self, code: str) -> List[str]:
        errors = []
        lines = code.splitlines()
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                # Validate include syntax
                if stripped.startswith("#include"):
                    # Must be followed by <header.h> or "header.h"
                    match = re.match(r'^#include\s*(<[^>]+>|"[^"]+")$', stripped)
                    if not match:
                        errors.append(f"Malformed #include directive at line {idx + 1}: '{line}'")
                elif stripped.startswith("#define"):
                    # Check for simple define spacing
                    if not re.match(r'^#define\s+[a-zA-Z_][a-zA-Z0-9_]*', stripped):
                        errors.append(f"Malformed #define macro at line {idx + 1}: '{line}'")
        return errors
