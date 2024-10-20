from pydantic import BaseModel, validator
from typing import List, Optional

class UserBase(BaseModel):
    email: str
    name: str
    mobile: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class SplitBase(BaseModel):
    user_id: int
    amount: Optional[float] = None
    percentage: Optional[float] = None

class SplitCreate(SplitBase):
    pass

class Split(SplitBase):
    id: int
    expense_id: int

    class Config:
        orm_mode = True

class ExpenseBase(BaseModel):
    amount: float
    description: str
    split_method: str
    payer_id: int

class ExpenseCreate(ExpenseBase):
    splits: List[SplitCreate]

    @validator('split_method')
    def validate_split_method(cls, v):
        if v not in ["equal", "exact", "percentage"]:
            raise ValueError("Split method must be 'equal', 'exact', or 'percentage'")
        return v

    @validator('splits')
    def validate_splits(cls, v, values):
        split_method = values.get('split_method')
        if split_method == "percentage":
            total_percentage = sum(split.percentage for split in v if split.percentage is not None)
            if total_percentage != 100:
                raise ValueError("Percentages must add up to 100%")
        elif split_method == "exact":
            total_amount = sum(split.amount for split in v if split.amount is not None)
            if total_amount != values.get('amount'):
                raise ValueError("Sum of split amounts must equal the total expense amount")
        return v

class Expense(ExpenseBase):
    id: int
    splits: List[Split]

    class Config:
        orm_mode = True