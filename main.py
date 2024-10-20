from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import or_
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

@app.get("/expenses/user/{user_id}", response_model=List[schemas.UserExpenseResponse])
def get_user_expenses(user_id: int, db: Session = Depends(get_db)):
    user_paid_expenses = db.query(models.Expense).filter(models.Expense.payer_id == user_id).all()
    user_splits = db.query(models.Split).filter(models.Split.user_id == user_id).all()
    
    user_expenses = []
    
    for expense in user_paid_expenses:
        user_expenses.append({
            "expense_id": expense.id,
            "amount": expense.amount,
            "description": expense.description,
            "split_method": expense.split_method,
            "type": "paid",
            "share_amount": 0
        })
        
    for split in user_splits:
        user_expenses.append({
            "expense_id": split.expense.id,
            "amount": split.expense.amount,
            "description": split.expense.description,
            "split_method": split.expense.split_method,
            "type": "owed",
            "share_amount": split.amount
        })
    
    return user_expenses

@app.get("/expenses/", response_model=List[schemas.Expense])
def get_all_expenses(db: Session = Depends(get_db)):
    expenses = db.query(models.Expense).all()
    return expenses

@app.get("/balance-sheet/")
def get_balance_sheet(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    balance_sheet = []
    
    for user in users:
        paid_expenses = []
        owed_expenses = []
        
        expenses_paid = db.query(models.Expense).filter(models.Expense.payer_id == user.id).all()
        for expense in expenses_paid:
            expense_details = {
                "id": expense.id,
                "amount": expense.amount,
                "description": expense.description,
                "split_method": expense.split_method,
                "splits": [{
                    "user_id": split.user_id,
                    "amount": split.amount,
                    "percentage": split.percentage
                } for split in expense.splits]
            }
            paid_expenses.append(expense_details)
            
        expenses_owed = db.query(models.Split).filter(models.Split.user_id == user.id).all()
        for split in expenses_owed:
            expense = split.expense
            expense_details = {
                "id": expense.id,
                "amount": expense.amount,
                "description": expense.description,
                "split_method": expense.split_method,
                "owed_amount": split.amount,
                "payer_id": expense.payer_id
            }
            owed_expenses.append(expense_details)
            
        total_paid = sum(expense["amount"] for expense in paid_expenses)
        total_owed = sum(expense["owed_amount"] for expense in owed_expenses)
        
        user_balance = {
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "total_paid": total_paid,
            "total_owed": total_owed,
            "net_balance": total_paid - total_owed,
            "paid_expenses": paid_expenses,
            "owed_expenses": owed_expenses
        }
        
        balance_sheet.append(user_balance)
    
    return JSONResponse(content={"balance_sheet": balance_sheet})

@app.get("/balance-sheet/download/")
def download_balance_sheet(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, newline='', suffix='.csv') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["User ID", "Name", "Email", "Total Paid", "Total Owed", "Net Balance"])
        
        for user in users:
            expenses_paid = db.query(models.Expense).filter(models.Expense.payer_id == user.id).all()
            total_paid = sum(expense.amount for expense in expenses_paid)
            
            expenses_owed = db.query(models.Split).filter(models.Split.user_id == user.id).all()
            total_owed = sum(split.amount for split in expenses_owed)
            
            net_balance = total_paid - total_owed
            
            csv_writer.writerow([
                user.id,
                user.name,
                user.email,
                round(total_paid, 2),
                round(total_owed, 2),
                round(net_balance, 2)
            ])
        
        csvfile.flush()
        return FileResponse(
            csvfile.name,
            media_type="text/csv",
            filename="balance_sheet.csv"
        )