from sqlalchemy import Column, Integer, String, Text, ForeignKey,Float
from database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="Draft")

class Scope(Base):
    __tablename__ = "scopes"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        unique=True,
        nullable=False
    )

    scope_details = Column(Text, nullable=False)

    deliverables = Column(Text)

    timeline = Column(String)

    status = Column(String, default="Draft")

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    deliverables = Column(Text)
    timeline = Column(String)
    exclusions = Column(Text)

    revision_limit = Column(Integer, default=2)

    price = Column(Float, nullable=False)

    status = Column(String, default="Draft")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    quotation_id = Column(
        Integer,
        ForeignKey("quotations.id"),
        nullable=False
    )

    amount = Column(Float, nullable=False)

    payment_method = Column(String, default="Manual")

    status = Column(String, default="Pending")

    transaction_reference = Column(String, nullable=True)
