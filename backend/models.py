from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class AnalyzeRequest(BaseModel):
    code: str

class Token(BaseModel):
    id: int
    lexeme: str
    token_type: str
    line: int
    column: int

class SyntaxIssue(BaseModel):
    line: int
    column: int
    message: str
    suggestion: str
    severity: str = "error"  # error, warning

class SymbolEntry(BaseModel):
    name: str
    type: str
    scope: str
    line: int
    status: str = "Declared"

class SemanticIssue(BaseModel):
    line: int
    column: int
    message: str
    suggestion: str
    issue_type: str
    severity: str = "error"

class MemoryAllocation(BaseModel):
    pointer: str
    allocation_function: str
    allocation_line: int
    freed: bool
    free_line: Optional[int] = None
    status: str  # SAFE, ESCAPED, POSSIBLE LEAK, DEFINITE LEAK, DOUBLE FREE, INVALID FREE, USE AFTER FREE
    severity: str  # safe, warning, error

class DuplicateBlock(BaseModel):
    block_a_lines: List[int]  # [start, end]
    block_b_lines: List[int]  # [start, end]
    similarity_percentage: float
    reason: str
    suggestion: str
    code_snippet_a: str
    code_snippet_b: str

class Anomaly(BaseModel):
    id: int
    issue_type: str  # SYNTAX, SEMANTIC, MEMORY, DUPLICATION
    severity: str    # error, warning, info
    line: int
    column: int
    message: str
    why_it_matters: str
    suggestion: str

class SuggestionItem(BaseModel):
    id: int
    title: str
    message: str
    suggestion: str
    line: int
    safe_fix: Optional[str] = None
    category: str
    original_snippet: Optional[str] = None
    fixed_snippet: Optional[str] = None
    fix_explanation: Optional[str] = None
    fix_type: Optional[str] = None  # "replace", "insert", "none"
    target_line: Optional[int] = None

class TokenStats(BaseModel):
    keywords: int = 0
    identifiers: int = 0
    constants: int = 0
    operators: int = 0
    separators: int = 0
    strings: int = 0
    total: int = 0

class FunctionComplexity(BaseModel):
    name: str
    line: int
    cyclomatic_complexity: int
    statement_count: int
    max_nesting_depth: int
    rating: str  # LOW, MODERATE, HIGH

class ReportStats(BaseModel):
    lines_of_code: int
    tokens_count: int
    syntax_errors: int
    semantic_errors: int
    warnings_count: int
    memory_issues: int
    duplicate_blocks: int
    variables_count: int
    overall_status: str  # CLEAN, NEEDS ATTENTION, ERRORS FOUND
    cyclomatic_complexity: Optional[int] = 1
    complexity_rating: Optional[str] = "LOW"

class PreprocessResult(BaseModel):
    original_code: str
    processed_code: str

class AnalyzeResponse(BaseModel):
    preprocessing: PreprocessResult
    tokens: List[Token]
    token_stats: TokenStats
    syntax_issues: List[SyntaxIssue]
    ast: Dict[str, Any]
    symbol_table: List[SymbolEntry]
    semantic_issues: List[SemanticIssue]
    memory_analysis: List[MemoryAllocation]
    duplication: List[DuplicateBlock]
    anomalies: List[Anomaly]
    suggestions: List[SuggestionItem]
    statistics: ReportStats
    complexity: List[FunctionComplexity] = []
