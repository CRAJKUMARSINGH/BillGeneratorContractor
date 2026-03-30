"""
Services Layer - Business Logic

This package contains the core business logic separated from HTTP handlers.
"""
from backend.services.bill_generation_service import generate_documents

__all__ = ["generate_documents"]
