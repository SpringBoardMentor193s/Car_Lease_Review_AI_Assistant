from fastapi import FastAPI, UploadFile
from fastapi.responses import HTMLResponse
from app.ocr import extract_text  # Your OCR function

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <html>
        <head>
            <title>Contract-AI PDF Upload</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 40px;">
            <h2>Upload a PDF to extract text</h2>
            <form action="/upload" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept=".pdf">
                <input type="submit" value="Upload PDF">
            </form>
        </body>
    </html>
    """

@app.post("/upload", response_class=HTMLResponse)
async def upload_pdf(file: UploadFile):
    if file.content_type != "application/pdf":
        return HTMLResponse(content="Error: Only PDF files are supported.", status_code=400)
    
    try:
        text = extract_text(file)  # Extract text using your OCR function
        
        # Display text in a scrollable, styled container
        return f"""
        <html>
            <head>
                <title>Extracted Text</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 40px;
                    }}
                    .text-container {{
                        white-space: pre-wrap;
                        background-color: #f5f5f5;
                        border: 1px solid #ccc;
                        padding: 20px;
                        max-height: 500px;
                        overflow-y: scroll;
                    }}
                    a {{
                        display: inline-block;
                        margin-top: 20px;
                        text-decoration: none;
                        color: #007BFF;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <h2>Extracted Text from PDF</h2>
                <div class="text-container">{text}</div>
                <a href="/">Upload another PDF</a>
            </body>
        </html>
        """
    except Exception as e:
        return HTMLResponse(content=f"Error extracting text: {e}", status_code=500)
