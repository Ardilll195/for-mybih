from flask import Flask, request, send_file
import os
import fitz  # PyMuPDF
import re
from datetime import datetime
from io import BytesIO

app = Flask(__name__)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    if file:
        # Simpan file sementara
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # Proses file PDF
        result = process_pdf(file_path)

        # Hapus file sementara
        os.remove(file_path)

        # Kembalikan hasil ke pengguna
        return send_file(
            BytesIO(result.encode()),
            mimetype='text/plain',
            as_attachment=True,
            download_name="hasil.txt"
        )


def process_pdf(file_path):
    """Fungsi untuk memproses file PDF dan mengembalikan hasil sebagai string"""
    info = {
        'inv_number': None,
        'name': None,
        'date': None
    }

    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()

                # Contoh: Ekstrak nomor invoice
                inv_match = re.search(r'INV\.?\s*(NO\.?\s*)?(\d{4})\s*/INV-', text, re.IGNORECASE)
                if inv_match:
                    info['inv_number'] = inv_match.group(2)

                # Contoh: Ekstrak nama
                name_match = re.search(r'Pembeli Barang Kena Pajak/Penerima Jasa Kena Pajak:\s*Nama\s*:\s*(.+)', text)
                if name_match:
                    info['name'] = name_match.group(1).strip()

                # Contoh: Ekstrak tanggal
                date_match = re.search(
                    r"KAB\. TANGERANG,\s+(\d{1,2})\s+(Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})",
                    text)
                if date_match:
                    day, month_str, year = date_match.groups()
                    months = {
                        "Januari": "01", "Februari": "02", "Maret": "03", "April": "04",
                        "Mei": "05", "Juni": "06", "Juli": "07", "Agustus": "08",
                        "September": "09", "Oktober": "10", "November": "11", "Desember": "12"
                    }
                    month = months[month_str]
                    info['date'] = f"{day}-{month}-{year}"

        # Format hasil
        result = f"Nomor Invoice: {info['inv_number']}\nNama: {info['name']}\nTanggal: {info['date']}"
        return result

    except Exception as e:
        return f"Error processing PDF: {str(e)}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))