from flask import Flask, request, render_template_string
import os
from ocr import extract_text



app = Flask(__name__)

UPLOAD_FOLDER = "../uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return "Car Lease AI Backend is Running"

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file selected"

        file = request.files["file"]

        if file.filename == "":
            return "No file selected"

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        extracted_text = extract_text(file_path)

        return render_template_string("""
            <h3>Contract Uploaded Successfully</h3>
            <h4>Extracted Text:</h4>
            <pre>{{ text }}</pre>
            <br>
            <a href="/upload">Upload another file</a>
        """, text=extracted_text)

    return render_template_string("""
        <h2>Upload Car Lease / Loan Contract</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <br><br>
            <button type="submit">Upload Contract</button>
        </form>
    """)

if __name__ == "__main__":
    app.run(debug=True)
