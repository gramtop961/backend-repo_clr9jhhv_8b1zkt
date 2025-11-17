import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="ChessReseller API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateOrderRequest(BaseModel):
    email: str
    asset_id: str


@app.get("/")
def read_root():
    return {"message": "ChessReseller Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Seed initial data for suppliers and assets if empty
@app.post("/seed")
def seed_data():
    try:
        suppliers = list(db["supplier"].find({})) if db else []
        assets = list(db["asset"].find({})) if db else []
        created = {"suppliers": 0, "assets": 0}
        if db is None:
            raise HTTPException(status_code=500, detail="Database not configured")
        if not suppliers:
            demo_suppliers = [
                {"name": "AromaHub", "category": "perfumes", "rating": 4.8, "description": "Bulk niche fragrances"},
                {"name": "SneakSupply", "category": "shoes", "rating": 4.6, "description": "Footwear B2B drops"},
                {"name": "WearWave", "category": "apparel", "rating": 4.5, "description": "Streetwear & basics"},
                {"name": "ElectraDepot", "category": "electronics", "rating": 4.7, "description": "Gadgets & accessories"},
            ]
            for s in demo_suppliers:
                create_document("supplier", s)
                created["suppliers"] += 1
        if not assets:
            demo_assets = [
                {
                    "title": "Perfume Reseller Pack 2025",
                    "category": "perfumes",
                    "supplier_names": ["AromaHub"],
                    "description": "Verified perfume suppliers, pricing sheets, outreach scripts",
                    "price": 9.99,
                    "file_path": "downloads/perfume-pack-2025.pdf",
                    "cover_image": "https://images.unsplash.com/photo-1541643600914-78b084683601?q=80&w=1200&auto=format&fit=crop"
                },
                {
                    "title": "Sneaker Plug Directory 2025",
                    "category": "shoes",
                    "supplier_names": ["SneakSupply"],
                    "description": "Top-tier sneaker wholesalers + import guide",
                    "price": 9.99,
                    "file_path": "downloads/sneaker-plug-2025.pdf",
                    "cover_image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop"
                },
                {
                    "title": "Apparel Supplier Pack 2025",
                    "category": "apparel",
                    "supplier_names": ["WearWave"],
                    "description": "Streetwear, basics e private label: contatti diretti e listini",
                    "price": 9.99,
                    "file_path": "downloads/apparel-pack-2025.pdf",
                    "cover_image": "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?q=80&w=1200&auto=format&fit=crop"
                },
                {
                    "title": "Electronics Supplier Pack 2025",
                    "category": "electronics",
                    "supplier_names": ["ElectraDepot"],
                    "description": "Gadget, accessori e small electronics per e-commerce",
                    "price": 9.99,
                    "file_path": "downloads/electronics-pack-2025.pdf",
                    "cover_image": "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?q=80&w=1200&auto=format&fit=crop"
                },
                {
                    "title": "All Suppliers Mega Bundle 2025",
                    "category": "mixed",
                    "supplier_names": ["AromaHub", "SneakSupply", "WearWave", "ElectraDepot"],
                    "description": "Bundle completo: profumi, scarpe, apparel, elettronica",
                    "price": 49.99,
                    "file_path": "downloads/mega-bundle-2025.zip",
                    "cover_image": "https://images.unsplash.com/photo-1515879218367-8466d910aaa4?q=80&w=1200&auto=format&fit=crop"
                }
            ]
            for a in demo_assets:
                create_document("asset", a)
                created["assets"] += 1
        return {"status": "ok", "created": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/suppliers")
def list_suppliers(category: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"category": category} if category else {}
    items = get_documents("supplier", filt)
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return items


@app.get("/assets")
def list_assets(category: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {"category": category} if category else {}
    items = get_documents("asset", filt)
    for it in items:
        it["_id"] = str(it["_id"])  # serialize
    return items


@app.post("/orders")
def create_order(payload: CreateOrderRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Check asset exists
    asset = db["asset"].find_one({"_id": __import__("bson").objectid.ObjectId(payload.asset_id)})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    order_doc = {
        "email": payload.email,
        "asset_id": str(asset["_id"]),
        "token": token,
        "expires_at": expires_at,
        "remaining_downloads": 3,
        "status": "paid"
    }
    oid = create_document("order", order_doc)
    return {"order_id": oid, "download_token": token, "expires_at": expires_at}


@app.get("/download/{token}")
def download_asset(token: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    order = db["order"].find_one({"token": token})
    if not order:
        raise HTTPException(status_code=404, detail="Invalid token")
    if order.get("status") != "paid":
        raise HTTPException(status_code=403, detail="Order not active")
    if order.get("expires_at") < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Link expired")
    if int(order.get("remaining_downloads", 0)) <= 0:
        raise HTTPException(status_code=403, detail="No downloads left")

    # Locate asset
    asset = db["asset"].find_one({"_id": __import__("bson").objectid.ObjectId(order["asset_id"])})
    if not asset:
        raise HTTPException(status_code=404, detail="Asset missing")

    file_path = asset.get("file_path")
    if not file_path:
        raise HTTPException(status_code=500, detail="File path not set for asset")

    abs_path = os.path.join(os.getcwd(), file_path)
    if not os.path.isfile(abs_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    # Decrement remaining downloads
    db["order"].update_one({"_id": order["_id"]}, {"$inc": {"remaining_downloads": -1}, "$set": {"updated_at": datetime.now(timezone.utc)}})

    filename = os.path.basename(abs_path)
    return FileResponse(abs_path, filename=filename)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
