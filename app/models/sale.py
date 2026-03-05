from sqlalchemy import Boolean, Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    total_amount = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_cancelled = Column(Boolean, default=False)

    items = relationship(
        "SaleItem",
        back_populates="sale",
        cascade="all, delete-orphan" )
