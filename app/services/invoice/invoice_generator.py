# app/invoices/invoice_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os
import time

INVOICE_DIR = "app/invoices/generated"
INVOICE_EXPIRATION_DAYS = 7  # Automatically delete invoices older than 7 days

def cleanup_old_invoices():
    """Deletes invoices older than the set expiration days to free up space."""
    now = time.time()
    expiration_time = INVOICE_EXPIRATION_DAYS * 86400  # Convert days to seconds

    if os.path.exists(INVOICE_DIR):
        for filename in os.listdir(INVOICE_DIR):
            file_path = os.path.join(INVOICE_DIR, filename)
            if os.path.isfile(file_path):
                file_age = now - os.path.getmtime(file_path)
                if file_age > expiration_time:
                    print(f"🗑️ Deleting old invoice: {file_path}")
                    os.remove(file_path)

def generate_invoice(transaction_details: dict, filename: str, user: dict) -> str:
    """
    Generates an invoice PDF and returns the file path.
    """
    os.makedirs(INVOICE_DIR, exist_ok=True)

    # ✅ Run cleanup before generating a new invoice
    cleanup_old_invoices()

    file_path = os.path.join(INVOICE_DIR, filename)

    print(f"📄 Generating invoice at: {file_path}")

    c = canvas.Canvas(file_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "RevouBank Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 750, f"Transaction ID: {transaction_details['id']}")
    c.drawString(50, 730, f"User: {user['username']}")
    c.drawString(50, 710, f"Transaction Type: {transaction_details.get('transaction_type', 'Unknown')}")
    c.drawString(50, 690, f"Amount: ${transaction_details['amount']}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 670, "Thank you for using RevouBank!")

    c.save()

    return file_path
