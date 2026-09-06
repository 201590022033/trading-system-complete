# Local data and transfer manifest — 2026-09-06

No local-only research data is required to run the safe suite or resume HR11
engineering. The required baselines are tracked. Before environment work, 54
tracked artifacts/reports (170,864,043 bytes total) were hashed; their exact paths,
sizes and SHA256 values are in `handoffs/2026-09-06-ARTIFACT-CHECKSUMS.json`.
The original HR11 immutable manifest separately protects 39 daily files/code hashes.
No research output was regenerated for this handoff.

| Location | Category / purpose | Required? | Git? | Recreate / transfer |
|---|---|---|---|---|
| `analysis/data/hr2/*.csv` | F: frozen daily market observations | Yes for existing regression/research | Yes | Clone/pull; preserve exact versions |
| `analysis/data/hr3/`, `hr7/`, `hr9/` | F: derived historical features/decisions/baselines | Yes for relevant research | Yes | Clone/pull; do not casually regenerate |
| `analysis/results/`, root `*report*.json`, `*report*.md` | A/F: historical evaluation/robustness evidence | Yes as checkpoint evidence | Yes | Clone/pull |
| `analysis/results/hr11/` | F: HR11 default report, empty decision/trade streams, manifests | Yes | Yes | Clone/pull; no actual 5m history exists here |
| HR12 artifacts | No files or commits found | Not applicable | No | Nothing to copy; do not invent a milestone |
| `.env` | E: optional local provider configuration | Only for those configured providers | No, ignored | Recreate using .env.example or securely transfer privately; contents not read |
| `.venv/` | B: local Python packages/interpreter | Rebuild required | No, ignored | Run bootstrap; never copy Linux venv to Windows |
| `__pycache__/` | D: bytecode | No | No, ignored | Regenerates automatically |
| `analysis/cache/` | D: optional cache location | No | No, ignored | Regenerate if needed; no required local content found |
| Dashboard market/news cache | D: process memory | No | No | Starts empty; public providers refill when available |
| `.ost-browser-profile/`, `ost_page_sample.html` | E: optional sensitive browser state locations | No for safe workflow | No, ignored | Not present in accessible project; do not copy cookies into Git |
| SQLite / parquet stores | C only if populated by future research | None currently found in project | No local store found | ReliabilityStore/feature-store callers supply paths; no DB server needed |
| Home-directory Ollama models | B/D: optional local AI model | No for offline work | No | Re-pull llama3.2:3b if desired; do not commit blobs |
| Empty root file with quoted Windows Downloads prompt pathname | Pre-existing untracked accidental filename, **0 bytes** | No | No | Preserved untouched; original prompt is already in docs/roadmap/HR11_REQUEST.md |

Required manual copy for offline development: **none**. Optional credentials must
be transferred through a secure method or recreated. Git authentication and editor
AI-tool sessions are separate machine setup, not project data. Windows-only files,
user databases and MCP registrations could not be inventoried from Codespaces.
Do not assume their absence on the Windows desktop.

Use `git status --short --ignored` to distinguish local files; do not stage broad
folders. The repository is roughly 171 MB of the protected artifacts listed above,
not an empty source-only checkout. Allow a full clone/pull to finish.
