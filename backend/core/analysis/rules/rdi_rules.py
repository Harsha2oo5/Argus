import re
from typing import List
from backend.core.analysis.parsers.base import CodeRepresentation
from backend.core.analysis.schemas import NormalizedFinding
from backend.core.analysis.rules.base import BaseRule
from backend.core.analysis.rules.registry import RuleRegistry

# RDI-specific known method prefixes
KNOWN_PREFIXES = [
    "get", "set", "read", "write",
    "pin", "label", "burst", "execute",
    "vForce", "iForce", "vMeas", "iMeas",
    "samples", "begin", "end", "wait",
    "connect", "disconnect", "reset", "init",
    "enable", "disable", "configure", "trigger",
    "groundForce", "iMeas"
]


class UnknownMethodRule(BaseRule):
    rule_id = "suspicious_method_name"
    name = "Unknown RDI Method"
    description = "RDI method name appears invalid or incorrectly formed."
    category = "API Misuse"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.8

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        for line in representation.lines:
            if line.is_comment:
                continue
            if line.contains_rdi:
                for method in re.findall(r'\.\s*(\w+)\s*\(', line.text):
                    if not any(method.startswith(p) for p in KNOWN_PREFIXES):
                        findings.append(NormalizedFinding(
                            rule_id=self.rule_id,
                            line_number=line.line_number,
                            line_text=line.stripped,
                            severity=self.severity,
                            static_confidence=self.confidence,
                            description=f"Unknown RDI method: '{method}'",
                            evidence=f"Flagged method: {method}",
                            remediation="Verify the RDI API documentation and use a correct method name."
                        ))
        return findings


class UnmatchedBlockRule(BaseRule):
    rule_id = "rdi_block_mismatch"
    name = "Unmatched RDI Execution Block"
    description = "RDI_BEGIN and RDI_END blocks must match."
    category = "Syntax Error"
    language = "cpp"
    severity = "CRITICAL"
    confidence = 0.9

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        begin_count = representation.raw_code.count("RDI_BEGIN")
        end_count = representation.raw_code.count("RDI_END")
        
        if begin_count != end_count:
            findings.append(NormalizedFinding(
                rule_id=self.rule_id,
                line_number=None,
                line_text="RDI_BEGIN/RDI_END mismatch",
                severity=self.severity,
                static_confidence=self.confidence,
                description=f"Mismatched blocks: Found {begin_count} RDI_BEGIN but {end_count} RDI_END",
                evidence=f"BEGIN={begin_count}, END={end_count}",
                remediation="Ensure every RDI_BEGIN has a matching RDI_END block terminator."
            ))
        return findings


class IncompleteChainRule(BaseRule):
    rule_id = "incomplete_chain"
    name = "Incomplete Method Chain"
    description = "RDI method call sequence is missing a terminating semicolon or closure."
    category = "Syntax Error"
    language = "cpp"
    severity = "MEDIUM"
    confidence = 0.7

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        lines = representation.lines
        for i, line in enumerate(lines):
            if line.is_comment:
                continue
            if "rdi." in line.text and not line.stripped.endswith((";", "}", "{", ",")):
                # Check for line continuation starting with a dot
                has_continuation = False
                for next_line in lines[i + 1:]:
                    if next_line.stripped:
                        if next_line.stripped.startswith("."):
                            has_continuation = True
                        break
                if not has_continuation:
                    findings.append(NormalizedFinding(
                        rule_id=self.rule_id,
                        line_number=line.line_number,
                        line_text=line.stripped,
                        severity=self.severity,
                        static_confidence=self.confidence,
                        description="Incomplete method chain — missing terminator.",
                        evidence=line.stripped,
                        remediation="Append a semicolon ';' to terminate the statement, or continue chaining."
                    ))
        return findings


class OverflowRiskRule(BaseRule):
    rule_id = "overflow_risk"
    name = "Integer Overflow Risk"
    description = "Declaring small integer accumulators can risk overflow under bounds."
    category = "Resource Management"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.75

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        for line in representation.lines:
            if line.is_comment:
                continue
            if "uint8_t" in line.text and any(k in line.text for k in ["total", "sum", "avg", "count", "acc"]):
                findings.append(NormalizedFinding(
                    rule_id=self.rule_id,
                    line_number=line.line_number,
                    line_text=line.stripped,
                    severity=self.severity,
                    static_confidence=self.confidence,
                    description="uint8_t accumulator will overflow for values > 255.",
                    evidence="uint8_t variable declaration",
                    remediation="Upgrade the type to uint16_t or uint32_t to expand the byte capacity."
                ))
            if re.search(r'\bint\b', line.text) and "sensor" in line.text.lower():
                findings.append(NormalizedFinding(
                    rule_id="type_mismatch",
                    line_number=line.line_number,
                    line_text=line.stripped,
                    severity="MEDIUM",
                    static_confidence=0.6,
                    description="Signed int used for sensor values — consider uint16_t/uint32_t.",
                    evidence="Signed int declaration",
                    remediation="Use unsigned integers (uint16_t or uint32_t) for strictly non-negative measurements."
                ))
        return findings


class MissingVolatileRule(BaseRule):
    rule_id = "missing_volatile"
    name = "Missing Volatile Variable"
    description = "Variables shared inside ISR context should use volatile keywords."
    category = "Memory Safety"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.85

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        for line in representation.lines:
            if line.is_comment:
                continue
            if re.search(r'\b(bool|uint8_t|int)\b', line.text) and "=" in line.text and "volatile" not in line.text:
                if any(k in line.text for k in ["flag", "ready", "done", "busy", "irq", "data_ready", "isr"]):
                    findings.append(NormalizedFinding(
                        rule_id=self.rule_id,
                        line_number=line.line_number,
                        line_text=line.stripped,
                        severity=self.severity,
                        static_confidence=self.confidence,
                        description="ISR-shared variable missing 'volatile' keyword.",
                        evidence=line.stripped,
                        remediation="Add the 'volatile' keyword to prevent compiler caching."
                    ))
        return findings


class NullPointerRule(BaseRule):
    rule_id = "null_pointer"
    name = "Null Pointer Risk"
    description = "Pointer dereferences without allocations trigger runtime crashes."
    category = "Memory Safety"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.9

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        declared, allocated = set(), set()
        
        for line in representation.lines:
            if line.is_comment:
                continue
            # Extract declarations
            for p in re.findall(r'\b\w+\s*\*\s*(\w+)\s*;', line.text):
                declared.add(p)
            # Match allocations
            for p in declared:
                if re.search(rf'\b{p}\s*=\s*(?:malloc|calloc|new\b)', line.text):
                    allocated.add(p)
            # Match dereference
            if not re.search(r'\b\w+\s*\*\s*\w+\s*;', line.text):
                for p in re.findall(r'\*(\w+)\b', line.text):
                    if p in declared and p not in allocated:
                        findings.append(NormalizedFinding(
                            rule_id=self.rule_id,
                            line_number=line.line_number,
                            line_text=line.stripped,
                            severity=self.severity,
                            static_confidence=self.confidence,
                            description=f"Pointer '{p}' dereferenced without allocation.",
                            evidence=f"Dereference: *{p}",
                            remediation="Ensure the pointer is allocated memory using malloc/calloc/new before dereferencing."
                        ))
        return findings


class BlockingDelayRule(BaseRule):
    rule_id = "blocking_in_isr"
    name = "Blocking inside ISR"
    description = "Blocking delays inside interrupt contexts freeze system executions."
    category = "Performance"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.85

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        for line in representation.lines:
            if line.is_comment:
                continue
            if line.in_isr and re.search(r'delay|HAL_Delay|sleep|busy_wait|while\s*\(', line.text):
                findings.append(NormalizedFinding(
                    rule_id=self.rule_id,
                    line_number=line.line_number,
                    line_text=line.stripped,
                    severity=self.severity,
                    static_confidence=self.confidence,
                    description="Blocking call inside interrupt context.",
                    evidence=line.stripped,
                    remediation="Avoid delays or loops inside interrupts. Use hardware timers or tasks instead."
                ))
        return findings


class BitManipulationRule(BaseRule):
    rule_id = "bit_clear_error"
    name = "Bit Clearing Manipulation Error"
    description = "Bit clear operations should use bitwise AND with a negated mask."
    category = "Syntax Error"
    language = "cpp"
    severity = "HIGH"
    confidence = 0.8

    def execute(self, representation: CodeRepresentation) -> List[NormalizedFinding]:
        findings = []
        for line in representation.lines:
            if line.is_comment:
                continue
            if re.search(r'&\s*\d+\b', line.text) and "~" not in line.text:
                if any(k in line.text.lower() for k in ["clear", "disable", "off"]):
                    findings.append(NormalizedFinding(
                        rule_id=self.rule_id,
                        line_number=line.line_number,
                        line_text=line.stripped,
                        severity=self.severity,
                        static_confidence=self.confidence,
                        description="Use '& ~mask' not '& mask' to clear a bit.",
                        evidence=line.stripped,
                        remediation="Change the operation to 'value &= ~mask' to safely clear bit flags."
                    ))
        return findings


# Auto-register C++ rules in dynamic registry
RuleRegistry.register_rule(UnknownMethodRule)
RuleRegistry.register_rule(UnmatchedBlockRule)
RuleRegistry.register_rule(IncompleteChainRule)
RuleRegistry.register_rule(OverflowRiskRule)
RuleRegistry.register_rule(MissingVolatileRule)
RuleRegistry.register_rule(NullPointerRule)
RuleRegistry.register_rule(BlockingDelayRule)
RuleRegistry.register_rule(BitManipulationRule)
