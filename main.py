from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import urllib.parse

app = FastAPI(
    title="Taibah SDS Management",
    description="Search and browse Safety Data Sheets for Taibah University labs.",
    version="1.1.0",
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SDS_PATH = STATIC_DIR / "pdfs" / "Safety_Data_Sheets"
SDS_HAZARDS_PATH = STATIC_DIR / "data" / "sds_hazards.json"

# Static assets include the app shell and the SDS PDF library.
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


CATEGORY_RULES = (
    (
        "Acids",
        ("acid", "hydrochloric", "sulphuric", "sulfuric", "nitric", "acetic", "boric", "citric", "oxalic"),
    ),
    ("Bases", ("hydroxide", "ammonia")),
    (
        "Solvents",
        (
            "ethanol",
            "methanol",
            "propanol",
            "acetone",
            "chloroform",
            "xylene",
            "benzene",
            "ether",
            "acetonitrile",
            "dichloromethane",
            "formamide",
        ),
    ),
    (
        "Salts",
        (
            "sodium",
            "potassium",
            "chloride",
            "sulfate",
            "sulphate",
            "phosphate",
            "carbonate",
            "nitrate",
            "acetate",
            "iodide",
        ),
    ),
    (
        "Microbiology Media",
        ("agar", "broth", "medium", "peptone", "xld", "macconkey", "cetrimide", "baird", "tcbs"),
    ),
    (
        "Oils and Excipients",
        (
            "oil",
            "paraffin",
            "lanolin",
            "glycerol",
            "glycerine",
            "glycol",
            "starch",
            "cellulose",
            "gelatine",
            "talcum",
        ),
    ),
    (
        "Indicators and Dyes",
        ("indicator", "eosin", "methylene", "methyl", "phenol red", "fluorescein", "murexide", "violet"),
    ),
    (
        "Metals and Heavy Metals",
        ("cadmium", "mercury", "lead", "silver", "zinc", "barium", "chromium", "copper", "iron"),
    ),
    (
        "Alkaloids and Actives",
        (
            "nicotine",
            "atropine",
            "scopolamine",
            "quinine",
            "caffeine",
            "theophylline",
            "papaverine",
            "pilocarpine",
            "strychnine",
        ),
    ),
    (
        "Sugars and Nutrients",
        (
            "glucose",
            "fructose",
            "lactose",
            "sucrose",
            "saccharose",
            "maltose",
            "dextrose",
            "mannitol",
            "xylose",
        ),
    ),
)


HAZARD_DEFINITIONS = {
    "flammable": {
        "code": "GHS02",
        "label_ar": "قابل للاشتعال",
        "label_en": "Flammable",
        "symbol": "🔥",
    },
    "oxidizer": {
        "code": "GHS03",
        "label_ar": "مؤكسد",
        "label_en": "Oxidizer",
        "symbol": "O",
    },
    "corrosive": {
        "code": "GHS05",
        "label_ar": "آكل",
        "label_en": "Corrosive",
        "symbol": "⚗",
    },
    "toxic": {
        "code": "GHS06",
        "label_ar": "سام",
        "label_en": "Toxic",
        "symbol": "☠",
    },
    "irritant": {
        "code": "GHS07",
        "label_ar": "مهيج / ضار",
        "label_en": "Irritant",
        "symbol": "!",
    },
    "health": {
        "code": "GHS08",
        "label_ar": "خطر صحي مزمن",
        "label_en": "Health hazard",
        "symbol": "⚕",
    },
    "environment": {
        "code": "GHS09",
        "label_ar": "خطر بيئي",
        "label_en": "Environmental hazard",
        "symbol": "♒",
    },
    "review": {
        "code": "SDS",
        "label_ar": "راجع ملف SDS",
        "label_en": "Review SDS",
        "symbol": "SDS",
    },
}


HAZARD_RULES = (
    (
        "flammable",
        (
            "acetaldehyde",
            "acetone",
            "acetonitrile",
            "benzaldehyde",
            "benzene",
            "chloroform",
            "clove oil",
            "dichloromethane",
            "ethanol",
            "ethyl acetate",
            "ethyl alcohol",
            "isoamyl alcohol",
            "methanol",
            "methyl",
            "n hexane",
            "oil of",
            "petroleum ether",
            "propanol",
            "tert butyl",
            "xylene",
        ),
    ),
    (
        "oxidizer",
        (
            "chlorate",
            "chromate",
            "dichromate",
            "hydrogen peroxide",
            "nitric acid",
            "nitrate",
            "periodate",
            "permanganate",
            "sodium nitrite",
        ),
    ),
    (
        "corrosive",
        (
            "acid anhydride",
            "ammonia",
            "benzoyl chloride",
            "chloroplatinic",
            "formalin",
            "hydrochloric acid",
            "hydroxide",
            "nitric acid",
            "phthalic anhydride",
            "potassium hydroxide",
            "sodium hydroxide",
            "sulphuric acid",
            "sulfuric acid",
        ),
    ),
    (
        "toxic",
        (
            "aniline",
            "arsenite",
            "atropine",
            "barium chloride",
            "benzene",
            "brucine",
            "cadmium",
            "chloroform",
            "chromate",
            "dichloromethane",
            "formaldehyde",
            "mercur",
            "nicotine",
            "phenol",
            "scopolamine",
            "strychnine",
        ),
    ),
    (
        "health",
        (
            "benzene",
            "cadmium",
            "chloroform",
            "chromate",
            "dichloromethane",
            "dimethylformamide",
            "formaldehyde",
            "formamide",
            "lead",
            "mercur",
            "naphthol",
            "nicotine",
            "xylene",
        ),
    ),
    (
        "environment",
        (
            "cadmium",
            "chromate",
            "copper",
            "iodine",
            "lead",
            "mercur",
            "silver nitrate",
            "zinc",
        ),
    ),
    (
        "irritant",
        (
            "acid",
            "alcohol",
            "ammonium",
            "chloride",
            "citrate",
            "copper",
            "glycol",
            "iodine",
            "naphthol",
            "phenanthroline",
            "phosphate",
            "salicylate",
            "sulfate",
            "sulphate",
            "thiocyanate",
            "xylene",
        ),
    ),
)


def normalize_text(value: str) -> str:
    separators = "`'\"()[]{}_,.;:%+-/\\"
    normalized = value.lower().replace(".pdf", "")
    for separator in separators:
        normalized = normalized.replace(separator, " ")
    return " ".join(normalized.split())


def infer_category(name: str) -> str:
    normalized = normalize_text(name)
    for category, keywords in CATEGORY_RULES:
        if any(keyword in normalized for keyword in keywords):
            return category
    return "General SDS"


def infer_hazards(name: str, category: str) -> list[dict[str, str]]:
    normalized = normalize_text(name)
    hazard_ids: list[str] = []

    for hazard_id, keywords in HAZARD_RULES:
        if any(keyword in normalized for keyword in keywords):
            hazard_ids.append(hazard_id)

    if category in {"Acids", "Bases"} and "corrosive" not in hazard_ids:
        hazard_ids.append("corrosive")
    if category == "Solvents" and "flammable" not in hazard_ids:
        hazard_ids.append("flammable")
    if not hazard_ids:
        hazard_ids.append("review")

    return [
        {"id": hazard_id, **HAZARD_DEFINITIONS[hazard_id]}
        for hazard_id in hazard_ids[:4]
    ]


@lru_cache(maxsize=1)
def get_pdf_hazard_index() -> dict[str, Any]:
    if not SDS_HAZARDS_PATH.exists():
        return {}

    with SDS_HAZARDS_PATH.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return payload.get("records", {})


def get_pdf_hazard_record(filename: str) -> dict[str, Any] | None:
    record = get_pdf_hazard_index().get(filename)
    if not record or record.get("source") in {"error", "not_found"}:
        return None
    if not record.get("hazards"):
        return None
    return record


def build_item(file: Path) -> dict[str, Any]:
    encoded_name = urllib.parse.quote(file.name)
    display_name = file.stem.strip()
    normalized = normalize_text(display_name)
    category = infer_category(display_name)
    pdf_hazard_record = get_pdf_hazard_record(file.name)
    hazard_source = "pdf" if pdf_hazard_record else "filename"
    hazards = pdf_hazard_record["hazards"] if pdf_hazard_record else infer_hazards(display_name, category)
    words = [word for word in normalized.split() if len(word) > 1]
    return {
        "name": display_name,
        "filename": file.name,
        "url": f"/static/pdfs/Safety_Data_Sheets/{encoded_name}",
        "category": category,
        "initial": display_name[:1].upper() if display_name else "#",
        "size_kb": round(file.stat().st_size / 1024, 1),
        "keywords": words[:8],
        "hazards": hazards,
        "hazard_source": hazard_source,
        "hazard_evidence": {
            "source": pdf_hazard_record["source"] if pdf_hazard_record else "filename_rules",
            "pictogram_codes": pdf_hazard_record.get("pictogram_codes", []) if pdf_hazard_record else [],
            "mapped_codes": pdf_hazard_record.get("mapped_codes", []) if pdf_hazard_record else [],
            "h_codes": pdf_hazard_record.get("h_codes", [])[:10] if pdf_hazard_record else [],
        },
        "search_text": " ".join((normalized, normalize_text(category), file.name.lower())),
    }


@lru_cache(maxsize=1)
def get_sds_index() -> tuple[dict[str, Any], ...]:
    if not SDS_PATH.exists():
        return tuple()

    files = sorted(SDS_PATH.glob("*.pdf"), key=lambda item: item.name.lower())
    return tuple(build_item(file) for file in files)


def public_item(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if key != "search_text"}


def score_item(item: dict[str, Any], query: str) -> int:
    search_text = item["search_text"]
    name = normalize_text(item["name"])
    query_words = normalize_text(query).split()
    if not query_words:
        return 0

    score = 0
    if name == query:
        score += 100
    if name.startswith(query):
        score += 75
    if query in search_text:
        score += 45
    score += sum(18 for word in query_words if word in search_text)
    score += sum(12 for word in query_words if any(token.startswith(word) for token in name.split()))
    return score


def search_index(query: str, limit: int = 40) -> list[dict[str, Any]]:
    normalized_query = normalize_text(query)
    if len(normalized_query) < 2:
        return []

    scored = [
        (score_item(item, normalized_query), item)
        for item in get_sds_index()
    ]
    results = [
        item
        for score, item in sorted(scored, key=lambda pair: (-pair[0], pair[1]["name"].lower()))
        if score > 0
    ]
    return [public_item(item) for item in results[:limit]]


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/Taibah_Logo.png")
def get_logo():
    logo_path = BASE_DIR / "Taibah_Logo.png"
    if logo_path.exists():
        return FileResponse(logo_path)
    return {"error": "Logo not found"}


@app.get("/health")
def health():
    return {"status": "ok", "sds_count": len(get_sds_index())}


@app.get("/api/stats")
def stats():
    items = get_sds_index()
    categories: dict[str, int] = {}
    hazards: dict[str, int] = {}
    hazard_sources: dict[str, int] = {}
    initials: dict[str, int] = {}
    total_size_kb = 0.0

    for item in items:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
        hazard_sources[item["hazard_source"]] = hazard_sources.get(item["hazard_source"], 0) + 1
        for hazard in item["hazards"]:
            hazards[hazard["id"]] = hazards.get(hazard["id"], 0) + 1
        initials[item["initial"]] = initials.get(item["initial"], 0) + 1
        total_size_kb += item["size_kb"]

    return {
        "sds_count": len(items),
        "total_size_mb": round(total_size_kb / 1024, 1),
        "categories": dict(sorted(categories.items())),
        "hazards": {
            hazard_id: {
                **HAZARD_DEFINITIONS[hazard_id],
                "count": count,
            }
            for hazard_id, count in sorted(hazards.items())
        },
        "hazard_sources": dict(sorted(hazard_sources.items())),
        "initials": dict(sorted(initials.items())),
    }


@app.get("/api/sds")
def list_sds(limit: int = Query(60, ge=1, le=500), offset: int = Query(0, ge=0)):
    items = [public_item(item) for item in get_sds_index()]
    return {
        "total": len(items),
        "limit": limit,
        "offset": offset,
        "results": items[offset: offset + limit],
    }


@app.get("/api/search-sds")
def search_sds_query(q: str = Query("", min_length=0), limit: int = Query(40, ge=1, le=100)):
    return {"query": q, "results": search_index(q, limit)}


@app.get("/search-sds/{query}")
def search_sds(query: str):
    if not SDS_PATH.exists():
        return {"results": [], "error": f"Path {SDS_PATH} not found"}
    return {"results": search_index(query)}
