import os
import io
import subprocess
import uuid
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Mime-Types für E-Books und Dokumente
MIME_TYPES = {
    'epub': 'application/epub+zip',
    'mobi': 'application/x-mobipocket-ebook',
    'azw3': 'application/vnd.amazon.mobi8-ebook',
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'txt': 'text/plain'
}

@app.route('/convert', methods=['POST'])
def convert_ebook():
    if 'file' not in request.files:
        return jsonify({"error": "Keine Datei hochgeladen"}), 400
    
    file = request.files['file']
    target_format = request.form.get('target_format', '').lower().strip()
    
    if file.filename == '' or not target_format:
        return jsonify({"error": "Ungültige Parameter"}), 400

    filename, file_extension = os.path.splitext(file.filename)
    source_format = file_extension.lower().replace('.', '')

    if source_format == target_format:
        return jsonify({"error": "Quell- und Zielformat sind identisch."}), 400

    unique_id = uuid.uuid4().hex
    input_path = f"/tmp/input_{unique_id}.{source_format}"
    output_path = f"/tmp/output_{unique_id}.{target_format}"

    try:
        # 1. Quelldatei temporär zwischenspeichern
        file.save(input_path)

        # 2. Calibre's ebook-convert ausführen
        # Syntax: ebook-convert input_file output_file
        cmd = ["ebook-convert", input_path, output_path]
        
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if process.returncode != 0:
            raise Exception(f"Calibre Fehler: {process.stderr}")

        # 3. Konvertierte Datei in den Speicher laden
        with open(output_path, 'rb') as f:
            converted_bytes = f.read()

        # 4. Temporäre Dateien löschen
        os.remove(input_path)
        os.remove(output_path)

        mime = MIME_TYPES.get(target_format, 'application/octet-stream')

        return send_file(
            io.BytesIO(converted_bytes),
            mimetype=mime,
            as_attachment=True,
            download_name=f"{filename}.{target_format}"
        )

    except Exception as e:
        # Aufräumen im Fehlerfall
        for path in [input_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
        return jsonify({"error": f"Konvertierungsfehler: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=8080)
