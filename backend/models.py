from datetime import datetime
from typing import Optional, List, Dict
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON

class NewsItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    summary: str
    url: str
    source: str
    sector: str
    agency: Optional[str] = Field(default=None)
    published_at: datetime = Field(default_factory=datetime.utcnow)
    is_circular: bool = Field(default=False)
    is_manual: bool = Field(default=False) 
    impact_rating: str = Field(default="Medium") # High, Medium, Low
    is_hidden: bool = Field(default=False)
    is_saved: bool = Field(default=False)
    
    # Store other sources for same article
    # Format: [{"source": "CNA", "url": "..."}]
    related_sources: Optional[List[Dict]] = Field(default=None, sa_column=Column(JSON))
    
    # Metadata for the system
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    # feedback: list["Feedback"] = Relationship(back_populates="news_item")


class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    news_item_id: int = Field(foreign_key="newsitem.id")
    liked: bool  # True for Like, False for Dislike
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserInterest(SQLModel, table=True):
    keyword: str = Field(primary_key=True)
    score: float = Field(default=1.0) # Base score
    last_active: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(default="search") # search, saved_item
