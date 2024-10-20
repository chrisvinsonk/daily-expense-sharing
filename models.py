from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    mobile = Column(String)

    expenses = relationship("Expense", back_populates="payer")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    description = Column(String)
    split_method = Column(String)
    payer_id = Column(Integer, ForeignKey("users.id"))

    payer = relationship("User", back_populates="expenses")
    splits = relationship("Split", back_populates="expense")

class Split(Base):
    __tablename__ = "splits"

    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    percentage = Column(Float, nullable=True)

    expense = relationship("Expense", back_populates="splits")
    user = relationship("User")