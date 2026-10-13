# CodeGuard

CodeGuard is a static analysis web application for C source code that combines front-end compiler phases with path-sensitive safety analysis to detect memory leaks, invalid frees, use-after-free conditions, double-frees, code duplications, and complexity metrics.

---

## Architecture & Analysis Pipeline

CodeGuard uses a decoupled architecture with a Python / FastAPI backend and a React / Vite / Monaco Editor frontend:

1. **Preprocessing**: Strips single-line (`//`) and multi-line (`/* */`) comments while preserving source line coordinates.
2. **Lexical Analysis (`lexer.py`)**: Tokenizes C keywords, identifiers, numeric constants, strings, operators, and separators.
3. **Syntax Analysis & AST (`parser.py`)**: Hand-written recursive descent parser for the supported C subset that builds an Abstract Syntax Tree (AST) with line-level source mapping.
4. **Symbol Table (`symbol_table.py`)**: Tracks variable and function declarations across global, function, and nested block scopes.
5. **Semantic Analysis (`semantic_analyzer.py`)**: Identifies undeclared variables, undeclared functions, and scope-level redeclarations.
6. **Memory Safety Analysis (`memory_analyzer.py`)**: Tracks heap memory provenance (`malloc`, `calloc`, `realloc`, `free`), detects definite vs. possible leaks, invalid frees (stack, global, string literal, interior pointer), use-after-free, and path-sensitive double-frees across loops, scopes, and function boundaries.
7. **Code Duplication Detector (`duplication_detector.py`)**: Identifies Type 1 (exact) and Type 2 (structural/renamed) duplicated statement blocks with boilerplate suppression.
8. **Complexity Analyzer (`complexity_analyzer.py`)**: Computes McCabe Cyclomatic Complexity (including logical decision operators `&&`, `||`), statement counts, and maximum control-flow nesting depth.
9. **Suggestion Engine (`suggestion_engine.py`)**: Generates structured anomalies and conservative safe-fix proposals.
10. **Interactive IDE Frontend (`frontend/`)**: Monaco code editor with real-time diagnostic squiggles, multi-tab analysis panels, jump-to-line navigation, and a safe-fix diff preview modal with stale-source invalidation guards.

---

## Features Implemented (Phases 3A–3E)

- **Structured Memory Pipeline (Phase 3A)**: Lifecycle allocation records, provenance tracking, and classification of definite vs. possible leaks.
- **Enhanced Safety Diagnostics (Phase 3B)**: Detection of invalid frees on non-heap addresses (stack variables, globals, string literals, interior pointer offsets), extended use-after-free tracking across expressions, multi-hop pointer aliasing, and path-sensitive double-frees.
- **Control Flow, Loops & Scopes (Phase 3C)**: Branching path exploration, shadowed variable scopes, loop-carried repeated frees, and early exit (`return`) paths.
- **Interprocedural Analysis (Phase 3D)**: Function-level memory summaries tracking heap memory escapes via return (`ESCAPED`), parameter deallocation, and alias propagation.
- **Duplication & Complexity Metrics (Phase 3E)**: Structural code duplication detection, McCabe Cyclomatic Complexity ratings, and statement count metrics.
- **Safe-Fix & Stale-Preview Safeguards**: Explicit user confirmation workflow for proposed fixes with drift detection that disables stale fix application when source code is modified.

---

## Supported C Grammar & Known Limitations

### Supported Constructs
- Primitive data types: `int`, `float`, `double`, `char`, `void`, `long`, `short`, `unsigned`, `signed`.
- Pointers: Single indirection (`type*`), address-of (`&`), and dereference (`*`).
- Control flow: `if` / `else if` / `else`, `while`, `for`, `do-while`, `return`, `break`, `continue`.
- Memory functions: Standard POSIX/C heap primitives (`malloc`, `calloc`, `realloc`, `free`).
- Functions: Function definitions, declarations, parameters, and return statements.

### Known Limitations
- **Grammar Subset**: Does not parse full ISO C11/C17 grammars (unions, bitfields, function pointers, variable-length arrays, or complex preprocessor directives).
- **Struct Member Tracking**: Heap allocations stored within struct members (e.g., `item->buffer`) are not tracked with field sensitivity.
- **Single Translation Unit**: Operates on a single source file; does not link multiple `.c` files or resolve external header libraries.
- **Bounded Loop Iterations**: Loop simulation is bounded to 2 iterations to capture loop-carried double-frees and overwrite leaks; unbounded loop invariants are not solved.
- **Safe-Fix Policy**: Automated fixes are intentionally conservative and restricted to deterministic patterns (missing semicolons and local unescaped leaks). Semantic errors and complex branching memory issues require manual review.

---

## Prerequisites

- **Python**: 3.10 or higher (tested on Python 3.12)
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher

---

## Environment Configuration

| Variable | Target | Description | Default |
| :--- | :--- | :--- | :--- |
| `VITE_API_URL` | Frontend | Full base URL of the backend API (e.g., `https://api.example.com`). Leave unset when deploying frontend and backend together on the same origin or when using the local dev proxy. | `/analyze` |
| `ALLOWED_ORIGINS` | Backend | Comma-separated list of allowed CORS origins (e.g., `https://app.example.com,https://staging.example.com`). Local development origins (`localhost:5173`, `localhost:4173`, `localhost:3000`) are included automatically. | Local dev origins |

---

## Local Setup & Development

### 1. Backend Setup

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

The backend API will be available at `http://127.0.0.1:8000`.

### 2. Frontend Setup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend development server starts at `http://localhost:5173`. The Vite development server automatically proxies `/analyze` requests to `http://127.0.0.1:8000`.

---

## Testing & Verification

### Running Backend Unit & Regression Tests

```bash
cd backend
python -m unittest test_analyzer -v
```

All 185 unit and regression tests run using Python's standard `unittest` framework with zero external test runners required.

### Building the Frontend

```bash
cd frontend
npm run build
```

This generates production-optimized assets in `frontend/dist/`.

---

## Deployment

### Single-Port Deployment (e.g. Render)

CodeGuard includes a `render.yaml` configuration that builds the frontend into `frontend/dist` and serves both the static UI and the `/analyze` API from FastAPI on a single port:

- **Build Command**: `cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### Separate Frontend & Backend Deployment (e.g. Vercel + Render)

1. Deploy the backend to Render, Railway, or AWS. Set `ALLOWED_ORIGINS=https://your-frontend.vercel.app`.
2. Deploy the frontend to Vercel or Netlify. Set `VITE_API_URL=https://your-backend.onrender.com`.

