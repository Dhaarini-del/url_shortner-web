from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String, unique=True, index=True)
    custom_alias = Column(String, unique=True, nullable=True)
    domain_name = Column(String)  # Extracted domain
    website_ip = Column(String)   # Extracted IP
    is_safe = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    clicks = relationship("Click", back_populates="link")

class Click(Base):
    __tablename__ = "clicks"
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ip_address = Column(String)
    country = Column(String)
    user_agent = Column(String)
    link = relationship("Link", back_populates="clicks")
