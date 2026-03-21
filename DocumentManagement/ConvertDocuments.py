"""
Convert PDF and DOCX files to text for RAG ingestion.

Text PDFs: PyMuPDF → pdfminer.six, optional per-word Arabic fix.
Image / scan PDFs: Tesseract OCR (Arabic + English) via pdf2image + pytesseract.

See PDF_TOOLS.md for packages (pdfminer.rtl, OCRmyPDF, EasyOCR, etc.).
"""
from __future__ import annotations

import os
import re
import argparse
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

from docx import Document

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:
    pdfminer_extract_text = None

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pdf2image import convert_from_path
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False

# Optional: Poppler path on Windows (set env POPPLER_PATH or edit here)
POPPLER_PATH = os.environ.get("POPPLER_PATH") or None


def _is_arabic_char(c):
    return '\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' or '\u08A0' <= c <= '\u08FF'


def _arabic_ratio(text):
    if not text:
        return 0
    arabic_count = sum(1 for c in text if _is_arabic_char(c))
    return arabic_count / len(text)


def _fix_reversed_arabic(text):
    if not text or _arabic_ratio(text) < 0.2:
        return text
    result = []
    for part in re.split(r'(\s+)', text):
        if re.match(r'^\s+$', part):
            result.append(part)
        elif _arabic_ratio(part) >= 0.5:
            result.append(part[::-1])
        else:
            result.append(part)
    return ''.join(result)


def _normalize_arabic(text):
    return unicodedata.normalize('NFC', text) if text else ""


def _is_arabic_presentation_form(c: str) -> bool:
    """Glyphs often produced by PDF extractors in wrong reading order."""
    o = ord(c)
    return 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF


def _arabic_script_char_count(text: str) -> int:
    """Letters in Arabic blocks including presentation forms."""
    n = 0
    for c in text:
        if _is_arabic_char(c) or _is_arabic_presentation_form(c):
            n += 1
    return n


def analyze_text_quality(text: str, used_ocr: bool) -> List[str]:
    """
    Heuristic flags for empty or likely-broken Arabic (not proof — review manually).
    OCR output skips presentation-form checks (Tesseract usually emits standard letters).
    """
    warnings: List[str] = []
    s = text.strip()
    n = len(s)

    if n == 0:
        warnings.append("empty file")
        return warnings
    if n < 30:
        warnings.append(f"nearly empty ({n} chars)")
    elif n < 100:
        warnings.append(f"very short ({n} chars)")

    replacement = s.count("\ufffd")
    if replacement >= 3:
        warnings.append(f"many replacement characters (U+FFFD ×{replacement})")

    # Bidirectional / embedding controls — often garbage from bad extraction
    bidi_controls = sum(1 for c in s if "\u202a" <= c <= "\u202e" or "\u2066" <= c <= "\u2069")
    if bidi_controls >= 2:
        warnings.append(f"bidirectional control characters (×{bidi_controls}) — possible corruption")

    arabic_total = _arabic_script_char_count(s)
    if arabic_total < 50:
        return warnings

    if not used_ocr:
        pres = sum(1 for c in s if _is_arabic_presentation_form(c))
        ratio = pres / arabic_total
        # PDF text layer often dumps presentation forms when order is wrong
        if ratio >= 0.35:
            warnings.append(
                f"high Arabic presentation-form ratio ({ratio:.0%}) — often reversed/wrong PDF order"
            )
        elif ratio >= 0.20 and arabic_total >= 500:
            warnings.append(
                f"elevated presentation-form ratio ({ratio:.0%}) — review Arabic readability"
            )

    # Unusually low spaces vs Arabic letters (one long glued run) — sometimes broken
    if arabic_total > 200:
        spaces = s.count(" ") + s.count("\n")
        if spaces < arabic_total * 0.02:
            warnings.append("very few spaces vs Arabic text — possible missing word breaks")

    return warnings


@dataclass
class ConversionReport:
    source_path: str
    output_path: str
    char_count: int
    used_ocr: bool
    warnings: List[str] = field(default_factory=list)


def print_run_summary(reports: List[ConversionReport]) -> None:
    """End-of-run checklist: empty files and suspicious Arabic."""
    if not reports:
        print("\n=== Conversion summary: no files processed ===")
        return

    def _failed(r: ConversionReport) -> bool:
        return any(
            "failed" in w.lower() or "skipped" in w.lower() or "missing" in w.lower()
            for w in r.warnings
        )

    empty = [r for r in reports if r.char_count == 0 and not _failed(r)]
    failed = [r for r in reports if r.char_count == 0 and _failed(r)]
    with_warnings = [r for r in reports if r.warnings]

    print("\n" + "=" * 60)
    print("CONVERSION SUMMARY")
    print("=" * 60)
    print(f"  Files processed: {len(reports)}")

    if failed:
        print(f"\n  FAILED / SKIPPED ({len(failed)}):")
        for r in failed:
            print(f"    - {r.output_path}")
            for w in r.warnings:
                print(f"        • {w}")

    if empty:
        print(f"\n  EMPTY OUTPUT ({len(empty)}):")
        for r in empty:
            print(f"    - {r.output_path}")
    elif not failed:
        print("\n  Empty output files: none")

    serious = [r for r in with_warnings if r.char_count > 0]
    if serious:
        print(f"\n  NEEDS REVIEW — heuristics only, not proof ({len(serious)}):")
        for r in serious:
            print(f"    - {r.output_path}")
            for w in r.warnings:
                print(f"        • {w}")
    elif empty or failed:
        print("\n  Non-empty files with quality flags: none")
    else:
        print("\n  Heuristic quality flags: none (spot-check long docs anyway)")

    print("=" * 60 + "\n")


def extract_text_layer(pdf_path):
    """Extract embedded text (no OCR)."""
    text = None
    if HAS_PYMUPDF:
        try:
            doc = fitz.open(pdf_path)
            parts = [page.get_text() for page in doc]
            doc.close()
            text = '\n'.join(parts)
        except Exception as e:
            print(f"  PyMuPDF failed ({e}), trying pdfminer...")
    if text is None and pdfminer_extract_text:
        try:
            text = pdfminer_extract_text(pdf_path)
        except Exception as e:
            print(f"  pdfminer failed ({e})")
            return None
    return text or ""


def ocr_pdf_to_text(pdf_path, dpi=300, lang="ara+eng"):
    """
    OCR each page with Tesseract. Arabic + English for mixed PAL48-style PDFs.
    Requires: tesseract with 'ara' (and 'eng'), poppler for pdf2image.
    """
    if not HAS_OCR:
        return None
    kwargs = {"dpi": dpi}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH
    try:
        images = convert_from_path(pdf_path, **kwargs)
    except Exception as e:
        print(f"  OCR: pdf2image failed ({e}). Install Poppler; on Windows set POPPLER_PATH.")
        return None
    parts = []
    for i, img in enumerate(images):
        try:
            page_text = pytesseract.image_to_string(img, lang=lang)
            parts.append(page_text)
        except Exception as e:
            print(f"  OCR: page {i + 1} failed ({e}). Check Tesseract and lang '{lang}' (tesseract --list-langs).")
    return "\n\n".join(parts).strip() or None


def convert_pdf_to_txt(pdf_path, txt_path, ocr=False, ocr_only=False, ocr_threshold=80, ocr_dpi=300):
    """
    ocr: also run OCR when text layer is shorter than ocr_threshold (chars).
    ocr_only: skip text layer, OCR only.
    Returns ConversionReport.
    """
    text = ""
    if not ocr_only:
        text = extract_text_layer(pdf_path) or ""
        if text is None:
            text = ""

    used_ocr = False
    if ocr_only:
        if not HAS_OCR:
            print(f"Error: --ocr-only needs pdf2image and pytesseract. pip install pdf2image pytesseract")
            return ConversionReport(
                source_path=pdf_path,
                output_path=txt_path,
                char_count=0,
                used_ocr=False,
                warnings=["skipped: OCR dependencies missing"],
            )
        text = ocr_pdf_to_text(pdf_path, dpi=ocr_dpi) or ""
        used_ocr = True
    elif ocr and HAS_OCR:
        stripped_len = len(text.strip())
        if stripped_len < ocr_threshold:
            ocr_text = ocr_pdf_to_text(pdf_path, dpi=ocr_dpi)
            if ocr_text:
                if len(ocr_text.strip()) > stripped_len:
                    text = ocr_text
                    used_ocr = True
                    print(f"  Using OCR (text layer was {stripped_len} chars)")
                elif stripped_len < 30:
                    text = ocr_text
                    used_ocr = True
                    print(f"  Using OCR (text layer nearly empty)")
    elif (ocr or ocr_only) and not HAS_OCR:
        print("  Tip: pip install pdf2image pytesseract for OCR")

    if not ocr_only and not used_ocr:
        if not text.strip() and HAS_OCR:
            ocr_text = ocr_pdf_to_text(pdf_path, dpi=ocr_dpi)
            if ocr_text:
                text = ocr_text
                used_ocr = True
                print(f"  Fallback OCR (no embedded text)")

    if not text.strip():
        print(f"  WARNING: {pdf_path} — empty output (image PDF without OCR setup?)")

    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    if not used_ocr:
        text = _fix_reversed_arabic(text)
    text = _normalize_arabic(text)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)

    warnings = analyze_text_quality(text, used_ocr=used_ocr)
    mode = "OCR" if used_ocr else "text"
    status = "OK" if len(text) >= 50 else "SHORT"
    print(f"  {pdf_path} -> {txt_path} [{mode}, {status}, {len(text)} chars]")

    return ConversionReport(
        source_path=pdf_path,
        output_path=txt_path,
        char_count=len(text),
        used_ocr=used_ocr,
        warnings=warnings,
    )


def convert_docx_to_txt(docx_path, txt_path):
    try:
        doc = Document(docx_path)
        text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        text = _normalize_arabic(text.strip())
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  {docx_path} -> {txt_path} [OK, {len(text)} chars]")
        warnings = analyze_text_quality(text, used_ocr=False)
        return ConversionReport(
            source_path=docx_path,
            output_path=txt_path,
            char_count=len(text),
            used_ocr=False,
            warnings=warnings,
        )
    except Exception as e:
        print(f"Error converting {docx_path}: {str(e)}")
        return ConversionReport(
            source_path=docx_path,
            output_path=txt_path,
            char_count=0,
            used_ocr=False,
            warnings=[f"conversion failed: {e}"],
        )


def process_file(input_path, output_dir, pdf_options) -> Optional[ConversionReport]:
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return None
    filename = os.path.basename(input_path)
    name, ext = os.path.splitext(filename)
    output_path = os.path.join(output_dir, f"{name}.txt")
    if ext.lower() == '.pdf':
        return convert_pdf_to_txt(input_path, output_path, **pdf_options)
    if ext.lower() == '.docx':
        return convert_docx_to_txt(input_path, output_path)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert PDF and DOCX to UTF-8 text")
    parser.add_argument("input", type=str, help="Input file or directory")
    parser.add_argument("output_dir", type=str, help="Output directory")
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Run Tesseract OCR when embedded text is shorter than --ocr-threshold",
    )
    parser.add_argument(
        "--ocr-only",
        action="store_true",
        help="Skip embedded text; OCR every page (slow)",
    )
    parser.add_argument(
        "--ocr-threshold",
        type=int,
        default=80,
        help="Min chars from text layer before trying OCR (with --ocr)",
    )
    parser.add_argument(
        "--ocr-dpi",
        type=int,
        default=300,
        help="DPI for PDF→image (higher = slower, often better OCR)",
    )
    args = parser.parse_args()

    if not HAS_PYMUPDF:
        print("Tip: pip install pymupdf for better PDF text extraction")
    if not pdfminer_extract_text:
        print("Error: pip install pdfminer.six")
        raise SystemExit(1)

    pdf_options = {
        "ocr": args.ocr or args.ocr_only,
        "ocr_only": args.ocr_only,
        "ocr_threshold": args.ocr_threshold,
        "ocr_dpi": args.ocr_dpi,
    }

    os.makedirs(args.output_dir, exist_ok=True)
    reports: List[ConversionReport] = []
    for root, dirs, files in os.walk(args.input):
        for file in files:
            input_path = os.path.join(root, file)
            rep = process_file(input_path, args.output_dir, pdf_options)
            if rep is not None:
                reports.append(rep)

    print_run_summary(reports)
