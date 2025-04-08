def send_invoice_with_email(transaction, user, account):
    from app.services.invoice.invoice_generator import generate_invoice
    from app.services.email.utils import send_email_async

    invoice_filename = f"invoice_{transaction.id}.pdf"
    invoice_path = generate_invoice(
        transaction_details={
            "id": transaction.id,
            "transaction_type": transaction.type,
            "amount": str(transaction.amount),
            "timestamp": transaction.timestamp.isoformat()
        },
        filename=invoice_filename,
        user=user
    )

    subject = {
        "deposit": "Deposit Confirmation & Invoice",
        "withdrawal": "Withdrawal Confirmation & Invoice",
        "transfer": "Transfer Confirmation & Invoice",
        "external_deposit": "External Deposit Confirmation & Invoice",
        "external_withdrawal": "External Withdrawal Confirmation & Invoice",
        "bill_payment": "Bill Payment Confirmation & Invoice"
    }.get(transaction.type, "Transaction Confirmation & Invoice")

    template = {
        "deposit": f"""
            Dear {user['username']},

            Your deposit of ${transaction.amount} has been processed.
            Transaction ID: {transaction.id}
            New Balance: ${account.balance}

            Invoice attached.

            Thank you for using RevouBank.
        """,
        "withdrawal": f"""
            Dear {user['username']},

            Your withdrawal of ${transaction.amount} has been processed.
            Transaction ID: {transaction.id}
            New Balance: ${account.balance}

            Invoice attached.

            Thank you for using RevouBank.
        """,
        "bill_payment": f"""
            Dear {user['username']},

            Your bill payment of ${transaction.amount} has been processed.
            Transaction ID: {transaction.id}
            New Balance: ${account.balance}

            Invoice attached.

            Thank you for using RevouBank.
        """,
        # Add other types as needed...
    }.get(transaction.type, f"""
        Dear {user['username']},

        Your transaction of ${transaction.amount} has been processed.
        Transaction ID: {transaction.id}
        New Balance: ${account.balance}

        Invoice attached.

        Thank you for using RevouBank.
    """)

    if user.get("email"):
        send_email_async(
            subject=subject,
            recipient=user["email"],
            body=template,
            attachment_path=invoice_path
        )
