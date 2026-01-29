from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import urllib.parse

app = FastAPI()

# المسار الجديد بدون مسافات لضمان التوافق مع السيرفرات
SDS_PATH = "static/pdfs/Safety_Data_Sheets"

# ربط المجلدات الاستاتيكية
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.get("/Taibah_Logo.png")
def get_logo():
    if os.path.exists("Taibah_Logo.png"):
        return FileResponse("Taibah_Logo.png")
    return {"error": "Logo not found"}

@app.get("/search-sds/{query}")
def search_sds(query: str):
    query = query.lower().strip()
    results = []
    
    # التأكد من وجود المجلد قبل البحث
    if not os.path.exists(SDS_PATH):
        return {"results": [], "error": f"Path {SDS_PATH} not found"}

    for file in os.listdir(SDS_PATH):
        if file.lower().endswith(".pdf") and query in file.lower():
            # تحويل المسار إلى رابط متوافق مع المتصفح
            encoded_name = urllib.parse.quote(file)
            results.append({
                "name": file.replace(".pdf", ""),
                "url": f"/static/pdfs/Safety_Data_Sheets/{encoded_name}"
            })
    
    return {"results": results}