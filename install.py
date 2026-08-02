#!/usr/bin/env python3
"""Instalador multiplataforma para Transcriptor v2.0.0.

Uso:
    python install.py

Este script no requiere dependencias previas.
Crea un entorno virtual, instala las dependencias Python y
verifica las dependencias del sistema (FFmpeg, Tesseract, Poppler).
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON_MIN = (3, 10)
REQUIREMENTS_FILE = "requirements.txt"
VENV_DIR = "venv"

INSTALL_HINTS = {
    "windows": {
        "ffmpeg": (
            "winget install ffmpeg",
            "https://ffmpeg.org/download.html",
        ),
        "tesseract": (
            "winget install tesseract-ocr",
            "https://github.com/UB-Mannheim/tesseract/wiki",
        ),
        "poppler": (
            'Descargar poppler y agregar bin\\ al PATH',
            "https://github.com/oschwartz10612/poppler-windows/releases",
        ),
    },
    "linux": {
        "ffmpeg": ("sudo apt install ffmpeg", ""),
        "tesseract": ("sudo apt install tesseract-ocr tesseract-ocr-spa", ""),
        "poppler": ("sudo apt install poppler-utils", ""),
    },
    "macos": {
        "ffmpeg": ("brew install ffmpeg", ""),
        "tesseract": ("brew install tesseract tesseract-lang", ""),
        "poppler": ("brew install poppler", ""),
    },
}

COLORS = {
    "green": "\033[92m",
    "red": "\033[91m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}


def _color(text: str, color_name: str) -> str:
    if os.name == "nt":
        return text
    return f"{COLORS.get(color_name, '')}{text}{COLORS['reset']}"


def green(text: str) -> str:
    return _color(text, "green")


def red(text: str) -> str:
    return _color(text, "red")


def yellow(text: str) -> str:
    return _color(text, "yellow")


def bold(text: str) -> str:
    return _color(text, "bold")


def print_banner() -> None:
    print()
    print(bold("=" * 55))
    print(bold("  Transcriptor v2.0.0 — Instalador multiplataforma"))
    print(bold("=" * 55))
    print(f"  SO detectado: {_detect_os()}  |  Python {sys.version.split()[0]}")
    print()


def _detect_os() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    else:
        return "linux"


def get_venv_python() -> str:
    if os.name == "nt":
        return str(Path(VENV_DIR) / "Scripts" / "python.exe")
    return str(Path(VENV_DIR) / "bin" / "python")


def get_venv_pip() -> str:
    if os.name == "nt":
        return str(Path(VENV_DIR) / "Scripts" / "pip.exe")
    return str(Path(VENV_DIR) / "bin" / "pip")


def step(msg: str) -> None:
    print(f"  {msg}...", end=" ", flush=True)


def ok(msg: str = "") -> None:
    print(f"{green('OK')} {msg}")


def fail(msg: str = "") -> None:
    print(f"{red('FALLO')} {msg}")


def warn(msg: str = "") -> None:
    print(f"{yellow('ADVERTENCIA')} {msg}")


def check_python() -> bool:
    step(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    if sys.version_info >= PYTHON_MIN:
        ok()
        return True
    fail(f"Se requiere Python >= {PYTHON_MIN[0]}.{PYTHON_MIN[1]}")
    return False


def create_venv() -> bool:
    step("Entorno virtual (venv/)")
    venv_path = Path(VENV_DIR)

    if venv_path.exists():
        ok("ya existe, se reutiliza")
        return True

    try:
        subprocess.run(
            [sys.executable, "-m", "venv", VENV_DIR],
            check=True,
            capture_output=True,
            text=True,
        )
        ok("creado")
        return True
    except subprocess.CalledProcessError as exc:
        fail(f"\n    {exc.stderr.strip()}")
        return False


def install_pip_deps() -> bool:
    step("Dependencias pip")
    req_path = Path(REQUIREMENTS_FILE)

    if not req_path.exists():
        fail(f"\n    No se encontró {REQUIREMENTS_FILE}")
        return False

    pip = get_venv_pip()
    try:
        result = subprocess.run(
            [pip, "install", "-r", REQUIREMENTS_FILE],
            check=True,
            capture_output=True,
            text=True,
        )
        ok(f"{len(_get_installed_lines(result.stdout))} paquetes instalados")
        return True
    except subprocess.CalledProcessError as exc:
        last_line = exc.stderr.strip().split("\n")[-1] if exc.stderr else str(exc)
        fail(f"\n    {last_line}")
        return False


def _get_installed_lines(output: str) -> list[str]:
    return [l for l in output.split("\n") if "Successfully installed" in l or "Requirement already satisfied" in l]


def check_system_deps() -> dict[str, bool]:
    os_name = _detect_os()
    results: dict[str, bool] = {}

    checks = {
        "FFmpeg": "ffmpeg",
        "Tesseract OCR": "tesseract",
    }
    optional = {
        "Poppler (PDFs)": ["pdftoppm", "pdfinfo"],
    }

    for name, cmd in checks.items():
        step(name)
        found = shutil.which(cmd) is not None
        if found:
            ok()
        else:
            hint_cmd, hint_url = INSTALL_HINTS.get(os_name, {}).get(cmd.lower(), ("", ""))
            hint = f"  → {hint_cmd}"
            if hint_url:
                hint += f"\n     {hint_url}"
            fail(f"\n{hint}")
        results[name] = found

    for name, cmds in optional.items():
        step(name)
        found = any(shutil.which(c) is not None for c in cmds)
        if found:
            ok()
        else:
            hint_cmd, hint_url = INSTALL_HINTS.get(os_name, {}).get(cmds[0].lower().replace("pdftoppm", "poppler"), ("", ""))
            hint = f"  → {hint_cmd}" if hint_cmd else ""
            if hint_url:
                hint += f"\n     {hint_url}"
            warn(f"(opcional)\n{hint}")
        results[name] = found

    return results


def print_instructions() -> None:
    print()
    print(bold("=" * 55))
    print(bold("  Para ejecutar Transcriptor:"))
    print("=" * 55)
    if os.name == "nt":
        print(f"    {VENV_DIR}\\Scripts\\activate")
    else:
        print(f"    source {VENV_DIR}/bin/activate")
    print("    python app.py")
    print()
    print(yellow("  Nota: La primera ejecución con whisper descargará"))
    print(yellow("  el modelo base (~140 MB). Requiere conexión a internet."))
    print()


def main() -> int:
    print_banner()

    steps_passed = 0
    steps_total = 4

    if not check_python():
        print(red("\n  Abortando: versión de Python no compatible."))
        return 1
    steps_passed += 1

    if not create_venv():
        print(red("\n  Abortando: no se pudo crear el entorno virtual."))
        return 1
    steps_passed += 1

    if not install_pip_deps():
        print(red("\n  Falló la instalación de dependencias Python."))
        return 1
    steps_passed += 1

    sys_results = check_system_deps()
    steps_passed += 1

    print()
    print(bold("=" * 55))
    print(bold("  RESUMEN"))
    print("=" * 55)
    all_ok = True
    for name, found in sys_results.items():
        if found:
            print(f"  {green('[OK]')}  {name}")
        else:
            is_optional = "PDF" in name
            symbol = yellow("[--]") if is_optional else red("[!!]")
            print(f"  {symbol}  {name}")

    print(f"\n  Dependencias Python: completadas ({steps_passed}/{steps_total})")
    print_instructions()

    return 0


if __name__ == "__main__":
    sys.exit(main())
