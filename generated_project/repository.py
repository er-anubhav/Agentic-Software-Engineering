from models import UrlMapping, UsageStats
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

engine = sa.create_engine('sqlite:///url_shortener.db')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

class URLRepository:
    def save(self, short_code: str, long_url: str):
        url_mapping = UrlMapping(short_code=short_code, long_url=long_url)
        session.add(url_mapping)
        session.commit()
        session.refresh(url_mapping)

    def get(self, short_code: str) -> str:
        return session.query(UrlMapping.long_url).filter_by(short_code=short_code).first()

class UsageStatsRepository:
    def initialize(self, short_code: str):
        usage_stats = UsageStats(short_code=short_code)
        session.add(usage_stats)
        session.commit()
        session.refresh(usage_stats)

    def increment(self, short_code: str):
        usage_stats = session.query(UsageStats).filter_by(short_code=short_code).first()
        if usage_stats:
            usage_stats.access_count += 1
            usage_stats.last_accessed = sa.func.now()
            session.commit()