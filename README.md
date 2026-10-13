# CodeGuard

CodeGuard is a web-based static analyzer for C programs that identifies memory-management bugs, semantic errors, and code-quality issues. It combines a custom C analysis pipeline with memory-safety checks and an interactive code editor to help developers understand potential problems before running their programs.

The application uses **React, Vite, and Monaco Editor** for the frontend and **Python and FastAPI** for the analysis backend.

**Live application:** [CodeGuard](https://codeguard-frontend-sage.vercel.app)  
**Backend API:** [CodeGuard Backend](https://codeguard-backend-six.vercel.app)  
**Source code:** [GitHub Repository](https://github.com/Swathi96-debug/CodeGuard)

## Features

- **Memory-safety analysis:** Detects memory leaks, invalid frees, use-after-free conditions, and double-frees.
- **Control-flow analysis:** Examines branches, loops, nested scopes, and early returns when analyzing memory operations.
- **Interprocedural analysis:** Tracks pointer aliases, memory escapes, and deallocation behavior across function boundaries.
- **Semantic checks:** Identifies undeclared variables, undeclared functions, and redeclarations within the supported C subset.
- **Code duplication detection:** Finds exact and structurally similar blocks of code.
- **Complexity metrics:** Calculates cyclomatic complexity, statement counts, and maximum control-flow nesting depth.
- **Interactive diagnostics:** Highlights findings in the editor and supports navigation to relevant source lines.
- **Safe-fix workflow:** Previews supported fixes and requires explicit confirmation before applying them.
- **Stale-preview protection:** Invalidates a proposed fix when the source code changes after its preview was generated.

## Architecture and analysis pipeline

CodeGuard uses a custom analysis engine rather than relying entirely on an external static-analysis tool.

1. **Preprocessing:** Removes single-line (`//`) and multi-line (`/* ... */`) comments while preserving source-line coordinates.
2. **Lexical analysis — `lexer.py`:** Converts source code into tokens representing keywords, identifiers, numeric constants, strings, operators, and separators.
3. **Syntax analysis — `parser.py`:** Uses a hand-written recursive-descent parser to build an Abstract Syntax Tree (AST) for the supported C grammar.
4. **Symbol table — `symbol_table.py`:** Tracks declarations across global, function, and nested block scopes.
5. **Semantic analysis — `semantic_analyzer.py`:** Checks for undeclared variables, undeclared functions, and scope-level redeclarations.
6. **Memory analysis — `memory_analyzer.py`:** Tracks heap allocations, pointer relationships, deallocations, and memory ownership across supported execution paths.
7. **Duplication detection — `duplication_detector.py`:** Identifies exact and structural duplicates while suppressing common boilerplate patterns.
8. **Complexity analysis — `complexity_analyzer.py`:** Calculates McCabe cyclomatic complexity, statement counts, and maximum nesting depth.
9. **Suggestion engine — `suggestion_engine.py`:** Produces structured diagnostics and conservative safe-fix proposals.
10. **Interactive frontend:** Presents findings through Monaco Editor and dedicated analysis panels, with source navigation and a confirmation-based fix workflow.

## Development history

CodeGuard was developed in stages. The initial work established the C analysis pipeline and interactive frontend; subsequent milestones extended the analyzer's memory-safety capabilities and added code-quality metrics.

### Initial development — Core analyzer and editor

The initial implementation established the foundation used by the later analysis milestones.

- **C language processing:** Built the preprocessing, lexical analysis, recursive-descent parser, AST, symbol table, and semantic-analysis components for the supported C subset.
- **Diagnostic pipeline:** Established the flow from source-code analysis to structured findings and frontend presentation.
- **Interactive editor:** Integrated Monaco Editor with the React/Vite application, analysis panels, diagnostic highlighting, and navigation to relevant source lines.
- **Fix workflow:** Implemented a preview-and-confirm approach for supported automated fixes, including protection against applying outdated previews.

These components provided the foundation for the more advanced memory-safety analysis introduced in Phase 3A.

### Phase 3A — Allocation and leak tracking

- Introduced structured allocation records and memory provenance tracking.
- Classified memory leaks as definite or possible based on the analyzed paths.
- Established the allocation lifecycle model used by subsequent memory-safety checks.

### Phase 3B — Memory-safety diagnostics

- Added invalid-free detection for stack variables, global objects, string literals, and interior pointers.
- Extended use-after-free tracking across expressions.
- Improved multi-hop pointer alias handling and path-sensitive double-free detection.
- Integrated findings with diagnostic presentation and safe-fix proposals.

### Phase 3C — Control flow, loops, and scopes

- Extended analysis across conditional branches and loop execution paths.
- Added handling for nested scopes and shadowed variables.
- Improved detection of repeated frees and overwrite leaks involving loops.
- Incorporated early-return paths into memory analysis.

### Phase 3D — Interprocedural analysis

- Added function-level memory summaries.
- Tracked allocations that escape through return values.
- Improved analysis of deallocation through function parameters and pointer alias propagation across function calls.

### Phase 3E — Duplication detection and complexity metrics

- Added Type 1 exact and Type 2 structural code-duplication detection.
- Introduced boilerplate suppression for duplication results.
- Implemented McCabe cyclomatic complexity, statement counts, and maximum nesting-depth metrics.

The repository preserves Git tags for the five milestones: `phase-3a-complete`, `phase-3b-complete`, `phase-3c-complete`, `phase-3d-complete`, and `phase-3e-complete`.

## Memory-safety analysis

Memory analysis is one of CodeGuard's main components. The analyzer models allocation lifecycles and pointer relationships to identify common heap-management errors.

| Analysis | Purpose |
|---|---|
| Memory leaks | Identifies allocations that remain unreleased on an analyzed execution path |
| Possible leaks | Identifies allocations that may remain unreleased on some paths |
| Invalid frees | Detects attempts to free stack variables, global objects, string literals, or interior pointers |
| Use-after-free | Detects accesses through pointers associated with deallocated memory |
| Double-free | Detects repeated deallocation, including supported cases involving aliases and control flow |
| Ownership across functions | Tracks returned allocations, parameter deallocation, and pointer aliases across function boundaries |

The analysis considers branches, bounded loop execution, nested scopes, and early returns. Function-level summaries extend memory tracking across supported function calls.

These checks are limited by the parser's supported grammar and the analyzer's execution model. They do not guarantee detection of every possible memory-safety defect.

## Interactive editor and safe fixes

The frontend is built with React, Vite, and Monaco Editor.

- **Source navigation:** Select a diagnostic to navigate to its corresponding location in the editor.
- **Diagnostic panels:** Inspect analysis findings through dedicated result panels.
- **Fix preview:** Review proposed source changes before applying them.
- **Explicit confirmation:** Confirm a proposed fix before the application modifies the source.
- **Stale-source protection:** Invalidate previews when the source changes, preventing outdated patches from being applied.

Automated fixes are intentionally conservative. Only supported patterns, such as missing semicolons and certain local, unescaped memory leaks, are eligible. Complex semantic or branching memory issues may require manual changes.

## Supported C grammar

CodeGuard implements a subset of C rather than the complete ISO C11/C17 language.

**Supported constructs include:**

- **Primitive types:** `int`, `float`, `double`, `char`, `void`, `long`, `short`, `unsigned`, and `signed`.
- **Pointers:** Single indirection (`type*`), address-of (`&`), and dereference (`*`).
- **Conditional statements:** `if`, `else if`, and `else`.
- **Loops:** `while`, `for`, and `do-while`.
- **Control flow:** `return`, `break`, and `continue`.
- **Memory functions:** `malloc`, `calloc`, `realloc`, and `free`.
- **Functions:** Function definitions, declarations, parameters, and return statements.

### Known limitations

- **Partial C grammar:** Unions, bitfields, function pointers, variable-length arrays, and complex preprocessor directives are outside the supported grammar.
- **Struct member tracking:** Allocations stored in struct members, such as `item->buffer`, are not tracked with field-sensitive precision.
- **Single translation unit:** Analysis operates on one source file. It does not link multiple `.c` files or resolve external header libraries.
- **Bounded loop simulation:** Loop analysis is limited to two simulated iterations for detecting certain repeated-free and overwrite-leak patterns. General loop invariants are not solved.
- **Conservative analysis:** Results depend on the supported syntax and execution model. Complex cases may require manual investigation.
- **Limited automated fixes:** Safe fixes are restricted to supported deterministic patterns; other findings require manual review.

## Technology stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| Code editor | Monaco Editor |
| Backend | Python, FastAPI |
| Language processing | Custom lexer, recursive-descent parser, AST, symbol table |
| Analysis | Semantic analysis, memory-safety analysis, duplication detection, complexity metrics |
| Testing | Python `unittest` |
| Version control | Git, GitHub |
| Deployment | Vercel |

## Local development

### Prerequisites

- Python 3.10 or later (Python 3.12 was used during verification).
- Node.js 18 or later.
- npm 9 or later.

### 1. Set up the backend

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

**Windows:**

```powershell
.\.venv\Scripts\activate
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

Install dependencies and start the FastAPI server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at `http://127.0.0.1:8000`.

### 2. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite starts the frontend at `http://localhost:5173`. The configured development proxy forwards `/analyze` requests to `http://127.0.0.1:8000`.

### Environment configuration

| Variable | Purpose |
|---|---|
| `VITE_API_URL` | Sets the frontend's API base URL. For separate deployments, use the backend URL. If unset, the frontend uses `/analyze`, suitable for the configured local proxy or a same-origin deployment. |
| `ALLOWED_ORIGINS` | Sets the comma-separated list of frontend origins permitted by backend CORS. Local development origins are included by default. |

For production deployments, configure environment variables in the hosting platform rather than committing environment-specific values to Git.

## Testing and verification

### Backend unit and regression tests

Run the backend test suite:

```bash
cd backend
python -m unittest test_analyzer -v
```

The stabilization milestone reported **185 passing tests**, including existing analyzer tests and additional request-validation tests.

### Frontend production build

```bash
cd frontend
npm run build
```

This produces optimized production assets in `frontend/dist/`.

## Deployment

CodeGuard is currently deployed through **two Vercel projects** connected to the same GitHub repository.

| Component | Vercel project | Root directory |
|---|---|---|
| Frontend | `codeguard-frontend` | `frontend` |
| Backend | `codeguard-backend` | `backend` |

**Live deployments**

- **Frontend:** [https://codeguard-frontend-sage.vercel.app](https://codeguard-frontend-sage.vercel.app)
- **Backend:** [https://codeguard-backend-six.vercel.app](https://codeguard-backend-six.vercel.app)

The frontend uses `VITE_API_URL` to send analysis requests to the backend. The backend uses `ALLOWED_ORIGINS` to permit requests from the deployed frontend.

The deployment verification reported successful frontend and backend responses, a successful CORS preflight, and an end-to-end analysis request that detected a memory leak in the submitted test program.

The repository also contains a `render.yaml` configuration for an alternative single-service Render deployment, where the frontend can be built into `frontend/dist` and served alongside FastAPI. The currently deployed application uses the two-project Vercel setup described above.

## Project status

CodeGuard includes the initial C analysis pipeline and interactive editor, followed by the Phase 3A–3E extensions for memory-safety analysis, interprocedural tracking, duplication detection, and complexity metrics.

The project is deployed and has passed the reported unit-test, build, and end-to-end API checks. Its analyzer remains scoped to a subset of C, so results should be treated as static-analysis findings rather than a formal proof of program correctness.

Contributions, bug reports, and suggestions for extending the supported grammar or analysis capabilities are welcome.
