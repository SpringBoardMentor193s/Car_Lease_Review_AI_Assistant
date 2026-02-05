from flask import Flask, render_template, request, jsonify
import os
import PyPDF2
import random

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


def extract_text_from_pdf(path):
    text = ""
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.lower()


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files["file"]
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)

    text = extract_text_from_pdf(path)

    analysis = {
        "score": random.randint(75, 90),
        "terms": {
            "Monthly Payment": "$450",
            "Term": "36 months",
            "APR": "4.9%",
            "Down Payment": "$2,500",
            "Mileage Allowance": "12,000/yr",
            "Total Cost": "$18,700"
        },
        "red_flags": [],
        "recommendations": []
    }

    if "disposition fee" in text:
        analysis["red_flags"].append(
            "Disposition fee is higher than industry average."
        )

    if "wear and tear" in text:
        analysis["red_flags"].append(
            "Wear and tear clause may cause extra charges."
        )

    analysis["recommendations"] = [
        "Negotiate to reduce acquisition or disposition fees.",
        "Verify APR matches the quoted rate.",
        "Ask if fees are waived for repeat customers."
    ]

    return jsonify(analysis)


if __name__ == "__main__":
    app.run(debug=True)
