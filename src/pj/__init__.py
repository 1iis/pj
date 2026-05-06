"""pj — language-agnostic project dispatcher.

Usage:
    pj init my-lib --py
    cd my-lib
    pj ship "Added feature X"

Backend modules (pj-py, pj-nb, ...) auto-register via:
    from pj import register
    register("py", "pj_py")
"""

__version__ = "0.1.0"

import importlib
import sys
from pathlib import Path
from typing import Optional

_BACKENDS: dict[str, str] = {}


class PjError(Exception):
    """Base error for pj operations."""


def register(lang: str, module_name: str) -> None:
    """Register a language backend.

    Called by pj-{lang} at import time, e.g.::

        from pj import register
        register("py", "pj_py")

    Args:
        lang: Short language key (e.g. "py", "nb").
        module_name: Importable module name (e.g. "pj_py").

    Raises:
        PjError: If a backend for this lang is already registered
                 with a different module.
    """
    existing = _BACKENDS.get(lang)
    if existing and existing != module_name:
        raise PjError(
            f"Backend for '{lang}' already registered as '{existing}'; "
            f"cannot override with '{module_name}'"
        )
    _BACKENDS[lang] = module_name


def _resolve_backend(path: Optional[Path] = None, lang: Optional[str] = None) -> str:
    """Resolve which language backend applies to a project.

    Args:
        path: Project root (default: cwd).
        lang: Explicit language key to bypass auto-detection.

    Returns:
        Language key (e.g. "py", "nb").

    Raises:
        PjError: If no backend can be resolved.
    """
    if lang:
        if lang not in _BACKENDS:
            raise PjError(
                f"Unknown language: {lang!r}. "
                f"Available: {', '.join(_BACKENDS)}"
            )
        return lang

    path = path or Path.cwd()
    for key, mod_name in _BACKENDS.items():
        mod = importlib.import_module(mod_name)
        if getattr(mod, "detect", lambda _: False)(path):
            return key
    raise PjError(
        f"Could not detect project language at {path}. "
        f"Use --lang or --py/--nb to specify "
        f"(available: {', '.join(_BACKENDS)})"
    )


def _lang_from_template(template: str) -> str:
    """Infer language from template short name or owner/repo."""
    if template in _BACKENDS:
        return template
    if "/" in template:
        repo = template.rsplit("/", 1)[-1]
        if repo in _BACKENDS:
            return repo
    raise PjError(
        f"Cannot infer language from template {template!r}. "
        f"Use --lang or a known template alias "
        f"(available: {', '.join(_BACKENDS)})"
    )


def init(
    name: str,
    *,
    desc: str = "",
    template: str = "py",
    org: str = "1iis",
    private: bool = True,
    path: Optional[Path] = None,
    token: Optional[str] = None,
    lang: Optional[str] = None,
) -> object:
    """Spawn a new project in any registered language.

    Dispatches to the appropriate backend's ``init()``.

    Args:
        name: Project/repo name.
        desc: Short project description.
        template: Template alias (e.g. "py") or "owner/repo" (e.g. "1iis/py").
        org: GitHub org/owner for the new repo.
        private: Whether the new repo is private.
        path: Parent directory for local clone (default: cwd).
        token: GitHub token (default: $GITHUB_TOKEN env).
        lang: Override language detection for ambiguous template names.

    Returns:
        Backend-specific Project object.
    """
    _lang = lang if lang else _lang_from_template(template)
    if _lang not in _BACKENDS:
        raise PjError(f"No backend registered for language {_lang!r}")
    mod = importlib.import_module(_BACKENDS[_lang])
    return mod.init(
        name,
        desc=desc,
        template=template,
        org=org,
        private=private,
        path=path,
        token=token,
    )


def ship(
    msg: str = "",
    bump: str = "patch",
    path: Optional[Path] = None,
    lang: Optional[str] = None,
) -> str:
    """Release a new version of the current project.

    Auto-detects language, then dispatches to the backend's ``ship()``.

    Args:
        msg: Changelog entry text. Empty → boilerplate.
        bump: "patch" (default), "minor", or "major".
        path: Project root (default: cwd).
        lang: Override language detection.

    Returns:
        New version string (e.g. "0.1.0").
    """
    _lang = _resolve_backend(path=path, lang=lang)
    mod = importlib.import_module(_BACKENDS[_lang])
    return mod.ship(msg=msg, bump=bump, path=path)


def main() -> None:
    """CLI entry point for ``pj``."""
    if len(sys.argv) < 2:
        print(
            f"pj v{__version__} — project dispatcher",
            file=sys.stderr,
        )
        print(f"Backends: {', '.join(_BACKENDS) if _BACKENDS else '(none registered)'}", file=sys.stderr)
        print(file=sys.stderr)
        print("Usage:", file=sys.stderr)
        print("  pj init <name> [--py|--nb] [-d desc] [--lang <lang>]", file=sys.stderr)
        print("  pj ship [msg] [--bump patch|minor|major] [--lang <lang>]", file=sys.stderr)
        sys.exit(1)

    cmd = sys.argv[1]
    try:
        if cmd == "init":
            if len(sys.argv) < 3:
                print("Usage: pj init <name> [options]", file=sys.stderr)
                sys.exit(1)
            p = init(sys.argv[2])
            print(f"Created {p.owner}/{p.repo} at {p.path}")

        elif cmd == "ship":
            # First positional non-flag arg is the msg
            msg = ""
            for a in sys.argv[2:]:
                if not a.startswith("-"):
                    msg = a
                    break
            v = ship(msg=msg)
            print(f"Shipped v{v}")

        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)

    except PjError as e:
        print(f"pj error: {e}", file=sys.stderr)
        sys.exit(1)
