from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class UrlMapping(Base):
    __tablename__ = 'url_mappings'
    id = Column(Integer, primary_key=True)
    short_code = Column(String(10), unique=True, nullable=False)
    long_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UsageStats(Base):
    __tablename__ = 'usage_stats'
    id = Column(Integer, primary_key=True)
    short_code = Column(String(10), ForeignKey('url_mappings.short_code'), nullable=False)
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime)