from typing import Dict, List, Type
from backend.core.analysis.rules.base import BaseRule


class RuleRegistry:
    """Registry class managing static analysis rules registration and discovery."""

    _rules: Dict[str, List[Type[BaseRule]]] = {}

    @classmethod
    def register_rule(cls, rule_class: Type[BaseRule]):
        lang = rule_class.language.lower()
        if lang not in cls._rules:
            cls._rules[lang] = []
        # Prevent duplicate rule registration
        if rule_class not in cls._rules[lang]:
            cls._rules[lang].append(rule_class)

    @classmethod
    def get_rules_for_language(cls, language: str) -> List[BaseRule]:
        lang_key = language.lower()
        rule_classes = cls._rules.get(lang_key, [])
        return [r_class() for r_class in rule_classes]
