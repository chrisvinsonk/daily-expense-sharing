from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import SessionLocal, engine
import csv
import tempfile

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/expenses/", response_model=schemas.Expense)
def add_expense(expense: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = models.Expense(
        amount=expense.amount,
        description=expense.description,
        split_method=expense.split_method,
        payer_id=expense.payer_id
    )
    db.add(db_expense)
    db.flush()

    if expense.split_method == "equal":
        split_amount = expense.amount / len(expense.splits)
        for split in expense.splits:
            db_split = models.Split(
                expense_id=db_expense.id,
                user_id=split.user_id,
                amount=split_amount
            )
            db.add(db_split)
    elif expense.split_method == "exact":
        for split in expense.splits:
            db_split = models.Split(
                expense_id=db_expense.id,
                user_id=split.user_id,
                amount=split.amount
            )
            db.add(db_split)
    elif expense.split_method == "percentage":
        for split in expense.splits:
            split_amount = expense.amount * (split.percentage / 100)
            db_split = models.Split(
                expense_id=db_expense.id,
                user_id=split.user_id,
                amount=split_amount,
                percentage=split.percentage
            )
            db.add(db_split)

    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses/user/{user_id}", response_model=List[schemas.Expense])
def get_user_expenses(user_id: int, db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).filter(
        (models.Expense.payer_id == user_id) | 
        (models.Expense.splits.any(models.Split.user_id == user_id))
    ).all()
    return expenses

@app.get("/expenses/", response_model=List[schemas.Expense])
def get_all_expenses(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    return expenses

@app.get("/balance-sheet/")
def get_balance_sheet(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    expenses = db.query(models.Expense).all()
    
    balances = {user.id: 0 for user in users}
    
    for expense in expenses:
        balances[expense.payer_id] += expense.amount
        for split in expense.splits:
            balances[split.user_id] -= split.amount
    
    balance_sheet = [
        {"user_id": user.id, "name": user.name, "balance": balances[user.id]}
        for user in users
    ]
    
    return JSONResponse(content={"balance_sheet": balance_sheet})

@app.get("/balance-sheet/download/")
def download_balance_sheet(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    expenses = db.query(models.Expense).all()
    
    balances = {user.id: 0 for user in users}
    
    for expense in expenses:
        balances[expense.payer_id] += expense.amount
        for split in expense.splits:
            balances[split.user_id] -= split.amount
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, newline='', suffix='.csv') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["User ID", "Name", "Balance"])
        
        for user in users:
            csv_writer.writerow([user.id, user.name, balances[user.id]])
        
        csvfile.flush()
        return FileResponse(
            csvfile.name,
            media_type="text/csv",
            filename="balance_sheet.csv",
        )