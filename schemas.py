"""
Database Schemas for ChessReseller

Each Pydantic model represents a collection in MongoDB. Collection name is the lowercase of the class name.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Supplier(BaseModel):
    name: str = Field(..., description="Supplier brand or company name")
    category: str = Field(..., description="Primary category e.g. perfumes, shoes, apparel, electronics")
    rating: float = Field(4.5, ge=0, le=5, description="Average rating 0-5")
    description: Optional[str] = Field(None, description="Short blurb about what they offer")
    website: Optional[str] = Field(None, description="External site or contact link")
    logo_url: Optional[str] = Field(None, description="Optional logo image URL")

class Asset(BaseModel):
    title: str = Field(..., description="Name of the downloadable package")
    category: str = Field(..., description="perfumes | shoes | apparel | electronics | mixed")
    supplier_names: List[str] = Field(default_factory=list, description="Related suppliers included")
    description: Optional[str] = Field(None, description="What is inside the package")
    price: float = Field(..., ge=0)
    file_path: str = Field(..., description="Relative path under downloads/ served on purchase")
    cover_image: Optional[str] = None

class Order(BaseModel):
    email: str = Field(..., description="Purchaser email")
    asset_id: str = Field(..., description="Reference to Asset _id")
    token: str = Field(..., description="Secure token for download")
    expires_at: datetime = Field(..., description="UTC expiry timestamp")
    remaining_downloads: int = Field(3, ge=0, description="How many downloads left")
    status: str = Field("paid", description="paid | refunded | expired")

# Optional example user model from template retained for reference
class User(BaseModel):
    name: str
    email: str
    address: str
    age: Optional[int] = None
    is_active: bool = True

class Product(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    category: str
    in_stock: bool = True
