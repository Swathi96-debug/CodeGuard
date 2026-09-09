from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models import AnalyzeRequest, AnalyzeResponse, PreprocessResult, ReportStats
from preprocessor import Preprocessor
from lexer import Lexer
from parser import Parser
from symbol_table import SymbolTableBuilder
from semantic_analyzer import SemanticAnalyzer
from memory_analyzer import MemoryAnalyzer
from duplication_detector import DuplicationDetector
from suggestion_engine import SuggestionEngine

app = FastAPI(title="CodeGuard C Compiler Analysis API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def read_root():
        return {"status": "online", "system": "CodeGuard Backend Server"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_code(req: AnalyzeRequest):
    code = req.code
    if not code or not code.strip():
        raise HTTPException(status_code=400, detail="No C code provided.")

    # 1. Preprocessing (Comment removal)
    processed_code = Preprocessor.process(code)

    # 2. Lexical Analysis
    lexer = Lexer(processed_code)
    tokens = lexer.tokenize()
    token_stats = lexer.stats

    # 3. Syntax Analysis & AST Generation
    parser = Parser(tokens)
    ast = parser.parse()
    syntax_issues = parser.syntax_issues

    # 4. Symbol Table Construction
    sym_builder = SymbolTableBuilder(tokens, ast)
    symbol_table = sym_builder.build()

    # 5. Semantic Analysis
    sem_analyzer = SemanticAnalyzer(tokens, symbol_table)
    semantic_issues = sem_analyzer.analyze()

    # 6. Memory Leak Analysis
    mem_analyzer = MemoryAnalyzer(tokens)
    memory_analysis = mem_analyzer.analyze()

    # 7. Code Duplication Detection
    dup_detector = DuplicationDetector(code, tokens)
    duplications = dup_detector.detect()

    # 8. Suggestion Engine & Anomaly Center
    sugg_engine = SuggestionEngine(code, syntax_issues, semantic_issues, memory_analysis, duplications)
    anomalies, suggestions = sugg_engine.generate()

    # 9. Statistics & Report Calculation
    lines_count = len(code.splitlines())
    syntax_errs_count = len(syntax_issues)
    sem_errs_count = len(semantic_issues)
    mem_issues_count = len([m for m in memory_analysis if m.status != "SAFE"])
    dup_blocks_count = len(duplications)
    warn_count = len([a for a in anomalies if a.severity == "warning"])

    if syntax_errs_count > 0 or sem_errs_count > 0:
        overall_status = "ERRORS FOUND"
    elif mem_issues_count > 0 or dup_blocks_count > 0 or warn_count > 0:
        overall_status = "NEEDS ATTENTION"
    else:
        overall_status = "CLEAN"

    report_stats = ReportStats(
        lines_of_code=lines_count,
        tokens_count=len(tokens),
        syntax_errors=syntax_errs_count,
        semantic_errors=sem_errs_count,
        warnings_count=warn_count,
        memory_issues=mem_issues_count,
        duplicate_blocks=dup_blocks_count,
        variables_count=len(symbol_table),
        overall_status=overall_status
    )

    return AnalyzeResponse(
        preprocessing=PreprocessResult(original_code=code, processed_code=processed_code),
        tokens=tokens,
        token_stats=token_stats,
        syntax_issues=syntax_issues,
        ast=ast,
        symbol_table=symbol_table,
        semantic_issues=semantic_issues,
        memory_analysis=memory_analysis,
        duplication=duplications,
        anomalies=anomalies,
        suggestions=suggestions,
        statistics=report_stats
    )

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
