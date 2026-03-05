from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String,default="non renseignée")
    purchase_price = Column(Float, nullable=False)
    sale_price = Column(Float,nullable= False)
    quantity = Column(Integer, default=0)
    expiration_date = Column(Date)
    rupture_threshold = Column(Integer, default=5)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"))

    supplier = relationship("Supplier", back_populates="products")
