"""Pruebas del guard de la frontera de identidad.

Artículo VIII de la constitución de aleu: todo mecanismo de control automatizado lleva su
propio test. **Un guard sin test es un guard que un día deja de detectar y nadie se entera.**

Cada caso planta un archivo con una violación real en un directorio temporal y verifica que
el guard la encuentra con el código de regla correcto. El caso limpio verifica lo contrario:
que un sitio de marketing normal pasa sin ruido.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parents[1] / "scripts" / "ci" / "check_isolation.py"


def run_guard(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GUARD), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


# --- Casos que DEBEN fallar ---------------------------------------------------------

VIOLACIONES = [
    pytest.param(
        "sesion.js",
        "const t = document.cookie.split(';');",
        "ID-01",
        id="lee-cookies",
    ),
    pytest.param(
        "estado.js",
        "localStorage.setItem('aleu_session', token);",
        "ID-02",
        id="persiste-estado",
    ),
    pytest.param(
        "peticion.js",
        "fetch(url, { credentials: 'include' });",
        "ID-03",
        id="manda-credenciales",
    ),
    pytest.param(
        "cabecera.ts",
        "const h = { 'Authorization': `Bearer ${token}` };",
        "ID-04",
        id="cabecera-authorization",
    ),
    pytest.param(
        "cliente.ts",
        "import { getResources } from '@aleu/api-client';",
        "API-01",
        id="importa-cliente-api",
    ),
    pytest.param(
        "datos.js",
        "const r = await fetch('https://app.aleu.ai/api/v1/resources');",
        "API-02",
        id="llama-api-producto",
    ),
    pytest.param(
        "contacto.html",
        '<form method="POST" action="/contacto">',
        "DB-01",
        id="form-post-interno",
    ),
    pytest.param(
        "nav.html",
        '<a href="https://app.aleu.ai/settings/team">Equipo</a>',
        "APP-01",
        id="enlace-app-no-permitido",
    ),
]


@pytest.mark.parametrize("nombre,contenido,codigo", VIOLACIONES)
def test_detecta_violacion(tmp_path: Path, nombre: str, contenido: str, codigo: str) -> None:
    (tmp_path / nombre).write_text(contenido, encoding="utf-8")

    r = run_guard(tmp_path)

    assert r.returncode == 1, f"el guard NO detectó {codigo}:\n{r.stdout}"
    assert f"[{codigo}]" in r.stdout, f"se esperaba {codigo}, salida:\n{r.stdout}"
    assert nombre in r.stdout
    assert ":1:" in r.stdout, "el guard debe reportar el número de línea"


# --- Casos que DEBEN pasar ----------------------------------------------------------


def test_sitio_limpio_pasa(tmp_path: Path) -> None:
    """Un sitio de marketing normal, con el único enlace permitido, no dispara nada."""
    (tmp_path / "index.html").write_text(
        "<!doctype html>\n"
        "<h1>aleu</h1>\n"
        '<a href="https://app.aleu.ai/signup">Empezar</a>\n'
        '<a href="https://app.aleu.ai/login">Entrar</a>\n'
        '<form method="POST" action="https://newsletter.example.com/sub">'
        '<input name="email"></form>\n',
        encoding="utf-8",
    )
    (tmp_path / "app.js").write_text("document.querySelector('h1').classList.add('on');\n", "utf-8")

    r = run_guard(tmp_path)

    assert r.returncode == 0, f"un sitio limpio no debe fallar:\n{r.stdout}"
    assert "0 violaciones" in r.stdout


def test_ignora_directorios_excluidos(tmp_path: Path) -> None:
    """El propio guard y sus tests contienen los patrones: no pueden auto-delatarse."""
    for excluido in ("node_modules", "scripts", "tests", "dist"):
        d = tmp_path / excluido
        d.mkdir()
        (d / "x.js").write_text("document.cookie;\n", encoding="utf-8")

    r = run_guard(tmp_path)

    assert r.returncode == 0, f"los directorios excluidos no deben escanearse:\n{r.stdout}"


def test_ignora_extensiones_no_de_codigo(tmp_path: Path) -> None:
    (tmp_path / "notas.md").write_text("Aquí explicamos que document.cookie está prohibido.\n", "utf-8")

    r = run_guard(tmp_path)

    assert r.returncode == 0, f"la documentación puede nombrar los patrones:\n{r.stdout}"


def test_reporta_todas_las_violaciones_no_solo_la_primera(tmp_path: Path) -> None:
    (tmp_path / "malo.js").write_text(
        "document.cookie;\nlocalStorage.getItem('x');\n", encoding="utf-8"
    )

    r = run_guard(tmp_path)

    assert r.returncode == 1
    assert "[ID-01]" in r.stdout and "[ID-02]" in r.stdout
    assert "2 violación(es)" in r.stdout


def test_el_repositorio_real_esta_limpio() -> None:
    """El sitio tal como está hoy respeta su propia frontera."""
    r = run_guard(GUARD.resolve().parents[2])

    assert r.returncode == 0, f"el repositorio viola su propia frontera:\n{r.stdout}"
