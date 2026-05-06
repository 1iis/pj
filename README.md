# py
Template: Python

## File-by-file breakdown

### 1. `pyproject.toml` — the single source of truth

**Template feature**: when you spawn a new repo, the user must edit `name` and `[project.scripts]` at minimum. Everything else is good to go.

```toml
[project]
name = "my-package"                          # <-- EDIT THIS per project
dynamic = ["version"]
description = "One thing, done well."
readme = "README.md"
license = {text = "Apache-2.0"}
requires-python = ">=3.10"
dependencies = []

[tool.hatch.version]
path = "src/my_package/__init__.py"

[project.scripts]
my-package = "my_package:main"               # <-- EDIT THIS per project

[dependency-groups]
dev = [
    "pytest>=9.0",
    "ruff>=0.15",
    "fastship",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 160
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.fastship]
branch = "main"
```

---

### 2. `src/my_package/__init__.py` — version + entry point

**Template feature**: when spawning, the user renames `my_package/` to their package name. This is the only manual step (besides `pyproject.toml` edits).

```python
__version__ = "0.0.1"

def main() -> None:
    """CLI entry point. Replace with actual logic."""
    print(f"{__package__} v{__version__}")
```

**Why**: `__version__` as a simple literal is what `fastship`'s `ship-bump` expects — it rewrites this line directly. `main()` is what `[project.scripts]` points at.

---

### 3. `src/my_package/__main__.py` — `python -m` support

```python
from . import main

if __name__ == "__main__":
    main()
```

**Template feature**: zero-dep, zero-config. Every Python CLI should support this — it's the stdlib way. No action needed per project.

---

### 4. `src/my_package/py.typed` — type safety declaration

**Template feature**: empty marker file. One-touch, no content, never edited.

Empty file. Its existence tells `mypy` / `pyright` / `ty` that the package is typed, so when other projects import your package, the type checker trusts it.

---

### 5. `.python-version` — pin the interpreter

```
3.12
```

**Template feature**: `uv` reads this automatically — run `uv sync` and it downloads + uses exactly this Python version. Never edit per project unless you need a different version.

---

### 6. `tests/test_main.py` — smoke test

```python
from my_package import __version__, main

def test_version():
    assert __version__ is not None

def test_main_runs():
    """Doesn't crash, returns None (implicitly)."""
    main()
```

**Template feature**: the import path (`my_package`) is what the user changes. One smoke test is enough for a template — real tests come with the project.

---

### 7. `CHANGELOG.md` — fastship anchor

```markdown
<!-- do not remove -->
```

**Template feature**: fastship's `ship-changelog` and `ship-gh` look for this HTML comment as an insertion point. Without it, they refuse to run. One line, never touched.

---

### 8. `LICENSE` — Apache 2.0

**Template feature**: standard OSS license. GitHub auto-detects this by filename. No edits needed — but if you want MIT instead, swap the file.

---

### 9. `.gitignore` — keep it clean

```
__pycache__/
*.pyc
dist/
*.egg-info/
.atlas/
```

**Template feature**: `atlas/` excluded so `atlas .` doesn't recursively include its own output.

---

### 10. `.github/workflows/ci.yml` — the one "nice-to-have" worth including

**Template feature**: having CI from the start means every spawned repo has green checks on day one. No secret setup needed for `uv` + basic pytest.

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --group dev
      - run: uv run pytest
      - run: uv run ruff check src/
```

---

### How this plays with GitHub templates

When you `gh repo create new-project --template 1iis/my-python-template`:

1. **GitHub copies every file** — literally `git clone --bare` + push to new repo
2. **No git history** — the new repo starts with a single initial commit, no link to the template
3. **No branch protections, no webhooks, no Actions secrets** — those are repo-level settings, not file-level. Template only carries *file content*.
4. **`--clone` is optional** — without it, you `git clone` the new repo separately. With it, one command creates + clones.

So the workflow is:

```bash
# One-time template creation
gh repo create my-python-template --public --template
git clone git@github.com:1iis/my-python-template
# ... populate files, push ...

# Per-project, one command
gh repo create atlas --template 1iis/my-python-template --public --clone
# then edit pyproject.toml name, rename src/my_package/ → src/atlas/
```

Alright, makes sense on the missing files — those are standard enough to not need active management.

Here's the KISS `uv` lifecycle for the template, from zero to shipped.

---

## `uv` lifecycle — the short version

There's no `.venv` folder, no activation, no `pip`, no `pyenv`. `uv` handles everything implicitly.

### 🏁 Starting a new project (from template)

```bash
# Spawn from template
gh repo create atlas --template 1iis/py --public --clone
cd atlas

# Rename package directory
mv src/my_package src/atlas

# Install everything + create .venv
uv sync --group dev
```

That's it. `uv sync` reads `.python-version`, downloads the right Python if missing, creates `.venv/`, resolves all deps, writes `uv.lock`. No manual `python -m venv`, no `pip install`.

You'll see `.venv/` appear in the project root — but you never `source .venv/bin/activate`. Instead:

### 🏃 Running things

```bash
uv run pytest            # run tests
uv run ruff check src/   # lint
uv run ruff format src/  # format
uv run atlas             # run your CLI
```

`uv run` activates the venv automatically for that command. No shell state to manage.

### 📦 Adding dependencies

```bash
uv add requests              # runtime dep → pyproject.toml + uv.lock
uv add --group dev pytest    # dev dep → [dependency-groups] dev
uv sync                      # install everything
```

### 🚢 Shipping (with fastship)

```bash
ship-bump --part 2           # bump patch: 0.0.1 → 0.0.2
ship-pypi                    # build + upload to PyPI
```

These are already installed via `uv sync --group dev`. No activation needed.

### 🧹 When to `uv sync`

Run it after:
- `git pull` (someone changed deps)
- switching branches
- manually editing `pyproject.toml` deps

That's the whole daily loop. No venv juggling, no activation scripts, no `pip freeze`.
