"""Bounded PDF extraction, preview, and optional local Tesseract OCR."""

import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


MAX_PDF_BYTES = 50 * 1024 * 1024
MAX_PAGES = 100


def guess_label(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in (lines[-2:] + lines[:2]):
        if re.fullmatch(r"[0-9]{1,4}", line):
            return line
    return ""


def _worker(operation, path, extra=(), timeout=90):
    command = [sys.executable, str(Path(__file__).resolve()), operation, str(path), *map(str, extra)]
    try:
        result = subprocess.run(command, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        raise ValueError("Pemrosesan PDF terlalu lama. Coba PDF lebih kecil atau halaman lain.") from error
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(detail[-800:] or "PDF gagal diproses. Periksa berkas dan coba lagi.")
    return result.stdout


def inspect_pdf(data):
    if len(data) > MAX_PDF_BYTES:
        raise ValueError("Ukuran PDF maksimal 50 MB. Pecah dokumen menjadi beberapa bab.")
    if not data or b"%PDF-" not in data[:1024]:
        raise ValueError("Berkas ini tidak memiliki format PDF yang valid.")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "input.pdf"
        path.write_bytes(data)
        return json.loads(_worker("extract", path))


def preview_page(path, position, rotation=0):
    return _worker("render", path, (position, rotation), timeout=45)


def tesseract_path():
    override = os.environ.get("TESSERACT_CMD")
    candidates = [override, shutil.which("tesseract"), r"C:\Program Files\Tesseract-OCR\tesseract.exe"]
    return next((path for path in candidates if path and Path(path).is_file()), None)


def ocr_languages():
    executable = tesseract_path()
    if executable is None:
        return []
    try:
        result = subprocess.run([executable, "--list-langs"], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line for line in result.stdout.decode("utf-8", errors="replace").splitlines()
            if re.fullmatch(r"[a-zA-Z0-9_/]+", line) and line != "osd"]


def ocr_page(path, position, language, rotation=0):
    if language not in ocr_languages():
        raise ValueError("Bahasa OCR belum terpasang. Pasang paket bahasa Tesseract lalu coba lagi.")
    return _worker("ocr", path, (position, rotation, language), timeout=150).decode("utf-8").strip()


def _render(document, position, rotation, max_edge):
    if position < 1 or position > len(document) or rotation not in (0, 90, 180, 270):
        raise ValueError("Nomor halaman atau rotasi tidak valid.")
    page = document[position - 1]
    try:
        width, height = page.get_size()
        if not all(math.isfinite(x) and x > 0 for x in (width, height)):
            raise ValueError("Ukuran halaman PDF tidak valid.")
        bitmap = page.render(scale=min(3, max_edge / max(width, height)), rotation=rotation)
        try:
            image = bitmap.to_pil().convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()
        finally:
            bitmap.close()
    finally:
        page.close()


def _run_worker():
    # Keep malformed documents in a separate process with a wall-clock timeout.
    if sys.platform != "win32":
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    import pypdfium2 as pdfium

    operation, filename, *extra = sys.argv[1:]
    try:
        document = pdfium.PdfDocument(filename)
    except pdfium.PdfiumError as error:
        raise ValueError("PDF rusak atau memakai password. Buka salinan PDF tanpa password.") from error
    try:
        if not 1 <= len(document) <= MAX_PAGES:
            raise ValueError("PDF harus memiliki 1–100 halaman. Pecah dokumen yang lebih panjang.")
        if operation == "extract":
            pages = []
            for index in range(len(document)):
                page = document[index]
                textpage = page.get_textpage()
                try:
                    if textpage.count_chars() > 100_000:
                        raise ValueError("Satu halaman memiliki terlalu banyak teks. Gunakan salinan PDF yang lebih sederhana.")
                    text = textpage.get_text_range().replace("\r\n", "\n").replace("\x00", "")
                    pages.append({"position": index + 1, "printed_label": guess_label(text), "text": text})
                finally:
                    textpage.close()
                    page.close()
            sys.stdout.buffer.write(json.dumps(pages, ensure_ascii=False).encode())
        elif operation == "render":
            sys.stdout.buffer.write(_render(document, int(extra[0]), int(extra[1]), 1400))
        elif operation == "ocr":
            position, rotation, language = int(extra[0]), int(extra[1]), extra[2]
            executable = tesseract_path()
            if not executable or not re.fullmatch(r"[a-zA-Z0-9_/]+", language):
                raise ValueError("Tesseract atau bahasa OCR belum tersedia.")
            with tempfile.TemporaryDirectory() as directory:
                image = Path(directory) / "page.png"
                image.write_bytes(_render(document, position, rotation, 3000))
                result = subprocess.run(
                    [executable, str(image), "stdout", "-l", language, "--psm", "3"],
                    capture_output=True, timeout=120,
                )
                if result.returncode:
                    raise ValueError("OCR gagal. Periksa rotasi, kualitas foto, dan paket bahasa.")
                if len(result.stdout) > 400_000:
                    raise ValueError("Hasil OCR terlalu besar untuk satu halaman.")
                sys.stdout.buffer.write(result.stdout)
        else:
            raise ValueError("Operasi PDF tidak dikenal.")
    finally:
        document.close()


if __name__ == "__main__":
    try:
        _run_worker()
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
