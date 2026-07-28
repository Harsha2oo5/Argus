from typing import Dict, Type
from backend.core.analysis.parsers.base import BaseParser
from backend.core.analysis.parsers.cpp import CppParser


class ParserRegistry:
    """Registry class matching file extensions to programming language parser adapters."""

    _parsers: Dict[str, Type[BaseParser]] = {
        "cpp": CppParser,
        "h": CppParser,
        "hpp": CppParser,
        "cc": CppParser
    }

    @classmethod
    def get_parser(cls, extension: str) -> BaseParser:
        clean_ext = extension.lower().lstrip(".")
        parser_class = cls._parsers.get(clean_ext, CppParser)  # Default fallback to CppParser
        return parser_class()
