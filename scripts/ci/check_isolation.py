#!/usr/bin/env python3
"""Guard de la frontera de identidad — Artículo XV de la constitución de aleu.

La ley vive en `aleu`, no aquí:
  https://github.com/aleu-ai/aleu/blob/main/.specify/memory/constitution.md
  (Artículo XV — Un solo dueño de la identidad)

Este script es su mecanismo de verificación. `aleu-site` es marketing puro: no lee sesión,
no manda credenciales, no consume la API de producto y no escribe en la base de datos. Su
única acción vecina a la autenticación es un enlace a `app.aleu.ai/signup`.

Uso:
    python3 scripts/ci/check_isolation.py [raíz]

Salida:
    exit 0 — el sitio respeta la frontera
    exit 1 — una o más violaciones, con archivo, línea, regla y el texto que las dispara
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# --- Qué se revisa -----------------------------------------------------------------

# Extensiones de código que puede contener una violación.
SCANNED_SUFFIXES = frozenset(
    {".html", ".htm", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".vue", ".svelte", ".astro"}
)

# Directorios que nunca son código del sitio. `scripts` y `tests` se excluyen porque este
# mismo guard y sus pruebas contienen los patrones prohibidos como literales.
EXCLUDED_DIRS = frozenset(
    {".git", ".github", "node_modules", "scripts", "tests", "dist", "build", ".next", ".astro"}
)

# Rutas de `app.aleu.ai` que el Artículo XV permite enlazar. Un enlace es navegación del
# usuario, no una llamada del sitio: no cruza credenciales ni datos.
ALLOWED_APP_PATHS = frozenset({"", "/", "/signup", "/login"})


# --- Las reglas --------------------------------------------------------------------


@dataclass(frozen=True)
class Rule:
    code: str
    pattern: re.Pattern[str]
    reason: str


RULES: tuple[Rule, ...] = (
    Rule(
        "ID-01",
        re.compile(r"document\s*\.\s*cookie"),
        "el sitio no lee ni escribe cookies: la sesión es exclusiva del shell de la app",
    ),
    Rule(
        "ID-02",
        re.compile(r"localStorage|sessionStorage", re.IGNORECASE),
        "el sitio no persiste estado de usuario en el navegador",
    ),
    Rule(
        "ID-03",
        re.compile(r"credentials\s*[:=]\s*['\"]include['\"]|withCredentials"),
        "el sitio no envía credenciales en ninguna petición",
    ),
    Rule(
        "ID-04",
        re.compile(r"['\"]Authorization['\"]\s*:|Bearer\s+\$?\{?[\w.]+"),
        "el sitio no construye cabeceras de autorización",
    ),
    Rule(
        "API-01",
        re.compile(r"@aleu/api-client|from\s+['\"][^'\"]*contracts/"),
        "el sitio no importa el cliente de API generado ni los contratos de producto",
    ),
    Rule(
        "API-02",
        re.compile(
            r"(?:fetch|axios(?:\.\w+)?|XMLHttpRequest|EventSource)\s*\(.*(?:aleu\.ai|['\"]/api/)",
        ),
        "el sitio no llama a la API de producto",
    ),
    Rule(
        "DB-01",
        re.compile(r"<form\b(?![^>]*\baction\s*=\s*['\"]https://)[^>]*method\s*=\s*['\"]post", re.IGNORECASE),
        "el sitio no envía formularios a destinos propios: un POST sin action externa "
        "declarada escribe en la plataforma",
    ),
)


# --- Motor -------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    path: Path
    line_no: int
    code: str
    reason: str
    excerpt: str


APP_HOST_RE = re.compile(r"app\.aleu\.ai(?P<path>/[\w\-./]*)?")


def check_app_host(line: str) -> str | None:
    """Devuelve la ruta ofensiva si la línea referencia app.aleu.ai fuera de lo permitido."""
    for match in APP_HOST_RE.finditer(line):
        path = (match.group("path") or "").rstrip("/") or "/"
        if path not in ALLOWED_APP_PATHS:
            return path
    return None


def scan_line(path: Path, line_no: int, line: str) -> list[Violation]:
    found: list[Violation] = []
    excerpt = line.strip()[:120]
    for rule in RULES:
        if rule.pattern.search(line):
            found.append(Violation(path, line_no, rule.code, rule.reason, excerpt))
    offending_path = check_app_host(line)
    if offending_path is not None:
        found.append(
            Violation(
                path,
                line_no,
                "APP-01",
                f"solo se puede enlazar a app.aleu.ai en {sorted(ALLOWED_APP_PATHS - {''})}; "
                f"esta referencia apunta a '{offending_path}'",
                excerpt,
            )
        )
    return found


def iter_source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        if EXCLUDED_DIRS & set(path.relative_to(root).parts):
            continue
        yield path


def scan(root: Path) -> tuple[list[Violation], int]:
    violations: list[Violation] = []
    scanned = 0
    for path in iter_source_files(root):
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            violations.extend(scan_line(path, line_no, line))
    return violations, scanned


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=Path(__file__).resolve().parents[2],
        type=Path,
        help="raíz del sitio a revisar (por defecto, la raíz del repositorio)",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    violations, scanned = scan(root)

    if not violations:
        print(f"frontera de identidad: OK — {scanned} archivo(s) revisado(s), 0 violaciones")
        return 0

    print(f"frontera de identidad: {len(violations)} violación(es) en {scanned} archivo(s)\n")
    for v in violations:
        print(f"  {v.path.relative_to(root)}:{v.line_no}: [{v.code}] {v.reason}")
        print(f"      → {v.excerpt}\n")
    print(
        "Artículo XV de la constitución de aleu — un solo dueño de la identidad:\n"
        "  https://github.com/aleu-ai/aleu/blob/main/.specify/memory/constitution.md\n"
        "Si crees que el sitio necesita de verdad esta capacidad, el camino es enmendar el\n"
        "artículo con Max, no saltarse el check."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
