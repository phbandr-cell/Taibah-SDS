from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SDS_DIR = ROOT / "static" / "pdfs" / "Safety_Data_Sheets"
OUTPUT_PATH = ROOT / "static" / "data" / "sds_hazards.json"


GHS_DEFINITIONS = {
    "GHS01": {"id": "explosive", "code": "GHS01", "label_ar": "متفجر", "label_en": "Explosive", "symbol": "✸"},
    "GHS02": {"id": "flammable", "code": "GHS02", "label_ar": "قابل للاشتعال", "label_en": "Flammable", "symbol": "🔥"},
    "GHS03": {"id": "oxidizer", "code": "GHS03", "label_ar": "مؤكسد", "label_en": "Oxidizer", "symbol": "O"},
    "GHS04": {"id": "gas", "code": "GHS04", "label_ar": "غاز مضغوط", "label_en": "Gas under pressure", "symbol": "◯"},
    "GHS05": {"id": "corrosive", "code": "GHS05", "label_ar": "آكل", "label_en": "Corrosive", "symbol": "⚗"},
    "GHS06": {"id": "toxic", "code": "GHS06", "label_ar": "سام", "label_en": "Toxic", "symbol": "☠"},
    "GHS07": {"id": "irritant", "code": "GHS07", "label_ar": "مهيج / ضار", "label_en": "Irritant", "symbol": "!"},
    "GHS08": {"id": "health", "code": "GHS08", "label_ar": "خطر صحي مزمن", "label_en": "Health hazard", "symbol": "⚕"},
    "GHS09": {"id": "environment", "code": "GHS09", "label_ar": "خطر بيئي", "label_en": "Environmental hazard", "symbol": "♒"},
}


REVIEW_HAZARD = {
    "id": "review",
    "code": "SDS",
    "label_ar": "راجع ملف SDS",
    "label_en": "Review SDS",
    "symbol": "SDS",
}


H_CODE_TO_GHS = {
    "H200": "GHS01",
    "H201": "GHS01",
    "H202": "GHS01",
    "H203": "GHS01",
    "H204": "GHS01",
    "H205": "GHS01",
    "H220": "GHS02",
    "H221": "GHS02",
    "H222": "GHS02",
    "H223": "GHS02",
    "H224": "GHS02",
    "H225": "GHS02",
    "H226": "GHS02",
    "H228": "GHS02",
    "H240": "GHS01",
    "H241": "GHS01",
    "H242": "GHS02",
    "H250": "GHS02",
    "H251": "GHS02",
    "H252": "GHS02",
    "H260": "GHS02",
    "H261": "GHS02",
    "H270": "GHS03",
    "H271": "GHS03",
    "H272": "GHS03",
    "H280": "GHS04",
    "H281": "GHS04",
    "H290": "GHS05",
    "H300": "GHS06",
    "H301": "GHS06",
    "H310": "GHS06",
    "H311": "GHS06",
    "H330": "GHS06",
    "H331": "GHS06",
    "H302": "GHS07",
    "H312": "GHS07",
    "H315": "GHS07",
    "H317": "GHS07",
    "H319": "GHS07",
    "H332": "GHS07",
    "H335": "GHS07",
    "H336": "GHS07",
    "H304": "GHS08",
    "H334": "GHS08",
    "H340": "GHS08",
    "H341": "GHS08",
    "H350": "GHS08",
    "H351": "GHS08",
    "H360": "GHS08",
    "H361": "GHS08",
    "H362": "GHS08",
    "H370": "GHS08",
    "H371": "GHS08",
    "H372": "GHS08",
    "H373": "GHS08",
    "H400": "GHS09",
    "H410": "GHS09",
    "H411": "GHS09",
    "H412": "GHS09",
    "H413": "GHS09",
}


GHS_PRIORITY = ("GHS01", "GHS02", "GHS03", "GHS04", "GHS05", "GHS06", "GHS08", "GHS09", "GHS07")
GHS_RE = re.compile(r"\bGHS0[1-9]\b", re.IGNORECASE)
H_CODE_RE = re.compile(r"\bH(?:2\d{2}|3\d{2}|4\d{2})(?:[A-Z]{1,3})?\b")


def extract_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages[:6]:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def normalize_h_code(code: str) -> str:
    return code[:4].upper()


def sorted_codes(codes: set[str]) -> list[str]:
    priority = {code: index for index, code in enumerate(GHS_PRIORITY)}
    return sorted(codes, key=lambda code: (priority.get(code, 99), code))


def build_record(path: Path) -> dict[str, Any]:
    text = extract_text(path)
    pictogram_codes = {match.upper() for match in GHS_RE.findall(text)}
    h_codes = sorted({match.upper() for match in H_CODE_RE.findall(text)})
    mapped_codes = {
        H_CODE_TO_GHS[normalize_h_code(code)]
        for code in h_codes
        if normalize_h_code(code) in H_CODE_TO_GHS
    }
    final_codes = sorted_codes(pictogram_codes or mapped_codes)
    hazards = [GHS_DEFINITIONS[code] for code in final_codes]
    source = "pdf_pictograms" if pictogram_codes else "pdf_h_statements" if mapped_codes else "not_found"

    if not hazards:
        hazards = [REVIEW_HAZARD]

    return {
        "filename": path.name,
        "source": source,
        "pictogram_codes": sorted_codes(pictogram_codes),
        "mapped_codes": sorted_codes(mapped_codes),
        "h_codes": h_codes,
        "hazards": hazards,
        "text_extract_length": len(text),
    }


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    records: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for path in sorted(SDS_DIR.glob("*.pdf"), key=lambda item: item.name.lower()):
        try:
            records[path.name] = build_record(path)
        except Exception as exc:  # noqa: BLE001 - we want a complete report for a batch scan.
            errors[path.name] = str(exc)
            records[path.name] = {
                "filename": path.name,
                "source": "error",
                "pictogram_codes": [],
                "mapped_codes": [],
                "h_codes": [],
                "hazards": [REVIEW_HAZARD],
                "text_extract_length": 0,
            }

    payload = {
        "generated_by": "scripts/build_sds_hazards.py",
        "description": "GHS hazard indicators extracted from SDS PDF text. Review official SDS before safety decisions.",
        "total_files": len(records),
        "errors": errors,
        "records": records,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    source_counts: dict[str, int] = {}
    for record in records.values():
        source_counts[record["source"]] = source_counts.get(record["source"], 0) + 1

    print(json.dumps({"output": str(OUTPUT_PATH), "total": len(records), "sources": source_counts, "errors": len(errors)}, indent=2))


if __name__ == "__main__":
    main()
