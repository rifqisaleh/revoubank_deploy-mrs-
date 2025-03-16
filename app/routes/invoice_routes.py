from flask import Blueprint, request, send_file, jsonify
from app.services.invoice.invoice_generator import generate_invoice

invoice_bp = Blueprint('invoice', __name__)

@invoice_bp.route('/generate-invoice', methods=['POST'])
def generate_invoice_route():
    try:
        data = request.json
        transaction_details = data.get('transaction_details')
        filename = data.get('filename', 'invoice.pdf')
        user = data.get('user')

        if not transaction_details or not user:
            return jsonify({"error": "Missing required fields"}), 400

        file_path = generate_invoice(transaction_details, filename, user)
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
