# app/invoices/invoice_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
import os

def generate_invoice(transaction_details: dict, filename: str, user: dict) -> str:
    """
    Generates an invoice PDF and returns the file path.
    """
    invoice_dir = "app/invoices/generated"
    os.makedirs(invoice_dir, exist_ok=True)

    file_path = os.path.join(invoice_dir, filename)
    c = canvas.Canvas(file_path, pagesize=A4)

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, 800, "RevouBank Invoice")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    c.drawString(50, 750, f"Transaction ID: {transaction_details['id']}")
    c.drawString(50, 730, f"User: {user['username']}")
    c.drawString(50, 710, f"Transaction Type: {transaction_details['transaction_type']}")
    c.drawString(50, 690, f"Amount: ${transaction_details['amount']}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, 670, "Thank you for using RevouBank!")

    c.save()

    return file_path
