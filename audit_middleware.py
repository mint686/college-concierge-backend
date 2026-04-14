from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal
from models import AuditLog
import json

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else None
        
        # Process request
        response = await call_next(request)
        
        # Log if it's a modifying request
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            try:
                db = SessionLocal()
                # Try to get current user (if authenticated)
                auth_header = request.headers.get("Authorization")
                user_id = None
                if auth_header:
                    # Extract user from token (simplified for now)
                    # You can implement proper token extraction here
                    pass
                
                audit = AuditLog(
                    user_id=user_id,
                    action=f"{request.method}_{request.url.path}",
                    table_name="unknown",
                    ip_address=client_ip
                )
                db.add(audit)
                db.commit()
                db.close()
            except Exception as e:
                print(f"Audit log error: {e}")
        
        return response


# ========== HELPER FUNCTION (Outside the class) ==========
def log_action(db: Session, user_id: int, action: str, table_name: str, record_id: int = None, old_value: dict = None, new_value: dict = None, ip: str = None):
    """Helper function to manually log actions"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip
    )
    db.add(audit)
    db.commit()
    return audit