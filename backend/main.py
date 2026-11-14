
import os
import requests
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

import models
from database import engine, Base, SessionLocal

# Create database tables
Base.metadata.create_all(bind=engine)

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv(
    "PAYPAL_BASE_URL",
    "https://api-m.sandbox.paypal.com"
)


def get_paypal_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="PayPal credentials are not configured"
        )

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=20
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="PayPal authentication failed"
        )

    return response.json()["access_token"]

# Initialize FastAPI
app = FastAPI(title="Scope2Pay API")

app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "https://scope2pay-frontend.onrender.com"
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# PYDANTIC SCHEMAS
# -------------------------

class BriefRequest(BaseModel):
    description: str


class ProjectCreate(BaseModel):
    client_name: str
    project_name: str
    description: str = ""


class ProjectUpdate(BaseModel):
    client_name: str
    project_name: str
    description: str = ""


class ScopeCreate(BaseModel):
    scope_details: str
    deliverables: str = ""
    timeline: str = ""


class QuotationCreate(BaseModel):
    deliverables: str
    timeline: str
    exclusions: str = ""
    revision_limit: int = 2
    price: float = Field(gt=0)


class QuotationUpdate(BaseModel):
    deliverables: str
    timeline: str
    exclusions: str = ""
    revision_limit: int = 2
    price: float = Field(gt=0)


class PaymentCreate(BaseModel):
    quotation_id: int
    amount: float = Field(gt=0)
    payment_method: str = "Manual"


class PaymentUpdate(BaseModel):
    status: str


# -------------------------
# HOME
# -------------------------

@app.get("/")
def home():
    return {"message": "Welcome to Scope2Pay"}


# -------------------------
# PROJECT APIs
# -------------------------

@app.post("/projects")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
):

    new_project = models.Project(
        client_name=project.client_name,
        project_name=project.project_name,
        description=project.description
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return {
        "message": "Project created successfully",
        "id": new_project.id,
        "client_name": new_project.client_name,
        "project_name": new_project.project_name,
        "description": new_project.description,
        "status": new_project.status
    }


@app.get("/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


@app.get("/projects/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    return project


@app.put("/projects/{project_id}")
def update_project(
    project_id: int,
    updated_data: ProjectUpdate,
    db: Session = Depends(get_db)
):

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    project.client_name = updated_data.client_name
    project.project_name = updated_data.project_name
    project.description = updated_data.description

    db.commit()
    db.refresh(project)

    return project


@app.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return {"message": "Project deleted successfully"}


# -------------------------
# SCOPE API
# -------------------------

@app.post("/projects/{project_id}/scope")
def create_scope(
    project_id: int,
    scope: ScopeCreate,
    db: Session = Depends(get_db)
):

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    existing_scope = db.query(models.Scope).filter(
        models.Scope.project_id == project_id
    ).first()

    if existing_scope:
        raise HTTPException(
            status_code=409,
            detail="Scope already exists for this project"
        )

    new_scope = models.Scope(
        project_id=project_id,
        scope_details=scope.scope_details,
        deliverables=scope.deliverables,
        timeline=scope.timeline
    )

    db.add(new_scope)
    db.commit()
    db.refresh(new_scope)

    return new_scope


# -------------------------
# QUOTATION APIs
# -------------------------

@app.post("/projects/{project_id}/quotations")
def create_quotation(
    project_id: int,
    quotation: QuotationCreate,
    db: Session = Depends(get_db)
):

    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    new_quotation = models.Quotation(
        project_id=project_id,
        deliverables=quotation.deliverables,
        timeline=quotation.timeline,
        exclusions=quotation.exclusions,
        revision_limit=quotation.revision_limit,
        price=quotation.price
    )

    db.add(new_quotation)
    db.commit()
    db.refresh(new_quotation)

    return {
        "message": "Quotation created successfully",
        "quotation_id": new_quotation.id,
        "project_id": new_quotation.project_id,
        "deliverables": new_quotation.deliverables,
        "timeline": new_quotation.timeline,
        "exclusions": new_quotation.exclusions,
        "revision_limit": new_quotation.revision_limit,
        "price": new_quotation.price,
        "status": new_quotation.status
    }


@app.get("/quotations")
def get_all_quotations(db: Session = Depends(get_db)):
    return db.query(models.Quotation).all()


@app.get("/quotations/{quotation_id}")
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db)
):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    return quotation


@app.put("/quotations/{quotation_id}")
def update_quotation(
    quotation_id: int,
    updated_data: QuotationUpdate,
    db: Session = Depends(get_db)
):

    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    quotation.deliverables = updated_data.deliverables
    quotation.timeline = updated_data.timeline
    quotation.exclusions = updated_data.exclusions
    quotation.revision_limit = updated_data.revision_limit
    quotation.price = updated_data.price

    db.commit()
    db.refresh(quotation)

    return {
        "message": "Quotation updated successfully",
        "quotation_id": quotation.id,
        "project_id": quotation.project_id,
        "deliverables": quotation.deliverables,
        "timeline": quotation.timeline,
        "exclusions": quotation.exclusions,
        "revision_limit": quotation.revision_limit,
        "price": quotation.price,
        "status": quotation.status
    }


# -------------------------
# AI BRIEF ANALYSER
# -------------------------

# -------------------------
# AI BRIEF ANALYSER
# -------------------------

@app.post("/analyze-brief")
def analyze_brief(data: BriefRequest):

    brief = data.description.lower()

    if "ecommerce" in brief or "shopping cart" in brief:
        project_type = "Ecommerce Website"

    elif "website" in brief:
        project_type = "Website Development"

    elif "mobile app" in brief or "application" in brief:
        project_type = "Mobile Application"

    else:
        project_type = "General Project"

    keywords = [
        "product listings",
        "shopping cart",
        "payment integration",
        "user login",
        "dashboard",
        "database",
        "admin panel",
        "delivery integration"
    ]

    requirements = [
        item for item in keywords if item in brief
    ]

    missing = []

    if "budget" not in brief and "price" not in brief:
        missing.append("Project budget")

    if "timeline" not in brief and "days" not in brief:
        missing.append("Project completion timeline")

    if "design" not in brief:
        missing.append("Design preferences")

    if "hosting" not in brief:
        missing.append("Hosting requirements")

    questions = [
        f"What is your expected {item.lower()}?"
        for item in missing
    ]

    return {
        "project_type": project_type,
        "requirements": requirements,
        "missing_information": missing,
        "clarification_questions": questions
    }


# -------------------------
# PAYMENT APIs
# -------------------------

@app.post("/payments")
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db)
):

    # Check quotation
    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == payment.quotation_id
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    # Calculate existing pending and paid payments
    existing_payments = db.query(models.Payment).filter(
        models.Payment.quotation_id == payment.quotation_id,
        models.Payment.status.in_(["Pending", "Paid"])
    ).all()

    total_recorded = sum(
        p.amount for p in existing_payments
    )

    # Check remaining quotation balance
    if total_recorded + payment.amount > quotation.price:
        raise HTTPException(
            status_code=400,
            detail="Payment exceeds the remaining quotation amount"
        )

    # Create payment
    new_payment = models.Payment(
        quotation_id=payment.quotation_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        status="Pending"
    )

    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)

    return {
        "message": "Payment record created successfully",
        "payment_id": new_payment.id,
        "quotation_id": new_payment.quotation_id,
        "amount": new_payment.amount,
        "payment_method": new_payment.payment_method,
        "status": new_payment.status
    }


@app.get("/payments")
def get_payments(db: Session = Depends(get_db)):

    payments = (
        db.query(
            models.Payment,
            models.Quotation,
            models.Project
        )
        .join(
            models.Quotation,
            models.Payment.quotation_id == models.Quotation.id
        )
        .join(
            models.Project,
            models.Quotation.project_id == models.Project.id
        )
        .all()
    )

    return [
        {
            "id": payment.id,
            "quotation_id": quotation.id,
            "client_name": project.client_name,
            "project_name": project.project_name,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "status": payment.status
        }
        for payment, quotation, project in payments
    ]

@app.get("/payments/{payment_id}")
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    return payment


@app.put("/payments/{payment_id}")
def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    db: Session = Depends(get_db)
):

    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Payment not found"
        )

    if payment_data.status not in ["Pending", "Paid", "Failed"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment status"
        )

    payment.status = payment_data.status

    db.commit()
    db.refresh(payment)

    return {
        "message": "Payment status updated successfully",
        "payment_id": payment.id,
        "status": payment.status
    }


@app.get("/payment-progress")
def get_payment_progress(db: Session = Depends(get_db)):

    quotations = db.query(models.Quotation).all()

    progress_data = []

    for quotation in quotations:

        project = db.query(models.Project).filter(
            models.Project.id == quotation.project_id
        ).first()

        payments = db.query(models.Payment).filter(
            models.Payment.quotation_id == quotation.id
        ).all()

        paid_amount = sum(
            p.amount for p in payments if p.status == "Paid"
        )

        pending_amount = sum(
            p.amount for p in payments if p.status == "Pending"
        )

        remaining_balance = quotation.price - paid_amount

        progress_percentage = (
            paid_amount / quotation.price * 100
            if quotation.price > 0 else 0
        )

        progress_data.append({
            "quotation_id": quotation.id,
            "client_name": project.client_name if project else "Unknown",
            "project_name": project.project_name if project else "Unknown",
            "quotation_total": quotation.price,
            "paid_amount": paid_amount,
            "pending_amount": pending_amount,
            "remaining_balance": remaining_balance,
            "progress_percentage": round(progress_percentage, 2)
        })

    return progress_data



@app.post("/paypal/create-order/{quotation_id}")
def create_paypal_order(
    quotation_id: int,
    return_url: str,
    cancel_url: str,
    db: Session = Depends(get_db)
):
    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    access_token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={
            "intent": "CAPTURE",
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "purchase_units": [
                {
                    "reference_id": str(quotation.id),
                    "description": "Scope2Pay Sandbox Demo",
                    "amount": {
                        "currency_code": "USD",
                        "value": "10.00"
                    }
                }
            ]
        },
        timeout=20
    )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail="PayPal order creation failed"
        )

    data = response.json()

    approval_link = next(
        (
            link["href"]
            for link in data.get("links", [])
            if link.get("rel") == "approve"
        ),
        None
    )

    if not approval_link:
        raise HTTPException(
            status_code=502,
            detail="PayPal approval link not returned"
        )

    return {
        "order_id": data["id"],
        "approval_url": approval_link,
        "quotation_id": quotation.id,
        "demo_amount": "10.00",
        "currency": "USD"
    }

@app.post("/paypal/capture-order/{order_id}")
def capture_paypal_order(
    order_id: str,
    quotation_id: int,
    db: Session = Depends(get_db)
):
    quotation = db.query(models.Quotation).filter(
        models.Quotation.id == quotation_id
    ).first()

    if not quotation:
        raise HTTPException(
            status_code=404,
            detail="Quotation not found"
        )

    access_token = get_paypal_access_token()

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        json={},
        timeout=20
    )

    if response.status_code not in (200, 201):
        raise HTTPException(
            status_code=502,
            detail="PayPal capture failed"
        )

    data = response.json()

    purchase_units = data.get("purchase_units", [])

    if not purchase_units or purchase_units[0].get(
        "reference_id"
    ) != str(quotation_id):
        raise HTTPException(
            status_code=400,
            detail="Order does not match this quotation"
        )

    if data.get("status") != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail="PayPal payment is not completed"
        )

    captures = (
        purchase_units[0]
        .get("payments", {})
        .get("captures", [])
    )

    return {
        "message": "PayPal Sandbox payment captured successfully",
        "order_id": data["id"],
        "capture_id": captures[0]["id"] if captures else None,
        "quotation_id": quotation_id,
        "status": data["status"],
        "currency": "USD",
        "demo_amount": "10.00",
        "note": "Sandbox transaction only. INR quotation ledger unchanged."
    }
