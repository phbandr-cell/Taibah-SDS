from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import urllib.parse

app = FastAPI()

# المسار الدقيق بناءً على ما أرسلته
SDS_PATH = "static/pdfs/Safety Data Sheets"

# ربط المجلدات الاستاتيكية
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
    
    # التأكد من وجود المجلد في المسار المطلوب
    if not os.path.exists(SDS_PATH):
        return {"error": f"المجلد غير موجود في: {SDS_PATH}"}

    try:
        for file in os.listdir(SDS_PATH):
            if file.lower().endswith(".pdf") and query in file.lower():
                # إزالة الامتداد للعرض الجمالي
                clean_name = file.replace(".pdf", "").replace(".PDF", "")
                
                # تحويل اسم الملف لروابط آمنة (للمسافات وغيرها)
                safe_filename = urllib.parse.quote(file)
                
                results.append({
                    "name": clean_name,
                    # الرابط يمر عبر pdfs ثم المجلد الموحد
                    "url": f"/static/pdfs/Safety%20Data%20Sheets/{safe_filename}"
                })
        
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}