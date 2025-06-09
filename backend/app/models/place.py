from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    city_id = Column(Integer, ForeignKey("cities.id"))
    
    # Relationship with City
    city = relationship("City", back_populates="places") 