# File Upload & AI Analysis App

A full-stack application that allows users to upload files, extract information, and analyze content using Ollama AI.

## Features

- 📤 **File Upload**: Support for TXT, PDF, DOC, DOCX, JPG, PNG files (up to 16MB)
- 🤖 **AI Analysis**: Automatic content extraction and analysis using Ollama
- 💾 **Local Storage**: Files and processed data stored locally
- 📊 **Results Display**: View extracted information and AI analysis
- 📁 **File Management**: Browse previously uploaded files
- 🎨 **Modern UI**: Responsive design with drag-and-drop support

## Tech Stack

### Backend
- **Python 3.8+**
- **Flask**: Web framework
- **Ollama**: AI model integration
- **Flask-CORS**: Cross-origin resource sharing

### Frontend
- **HTML5**
- **CSS3**: Modern styling with animations
- **JavaScript**: Vanilla JS (no frameworks)

## Prerequisites

1. **Python 3.8 or higher**
2. **Ollama**: [Install Ollama](https://ollama.ai/)
3. **Ollama Model**: Pull a model (e.g., llama3.2)
   ```bash
   ollama pull llama3.2
   ```

## Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create environment file (optional):
   ```bash
   copy .env.example .env
   ```

### Frontend Setup

No build process required! The frontend uses vanilla HTML, CSS, and JavaScript.

## Running the Application

### 1. Start Ollama

Make sure Ollama is running:
```bash
ollama serve
```

### 2. Start Backend Server

From the `backend` directory with virtual environment activated:
```bash
python app.py
```

The backend API will start on `http://localhost:3000`

### 3. Start Frontend

Simply open `frontend/index.html` in your web browser, or use a local server:

**Option 1: Direct File Open**
- Navigate to `frontend` folder
- Double-click `index.html`

**Option 2: Python HTTP Server**
```bash
cd frontend
python -m http.server 8000
```
Then visit `http://localhost:8000`

**Option 3: VS Code Live Server**
- Install "Live Server" extension
- Right-click `index.html` → "Open with Live Server"

## Usage

1. **Upload a File**
   - Drag and drop a file onto the upload area, or click to browse
   - Supported formats: TXT, PDF, DOC, DOCX, JPG, PNG
   - Maximum size: 16MB

2. **View Results**
   - After upload, the file is automatically processed
   - View extracted text and AI analysis
   - Results appear in the "Analysis Results" section

3. **Browse Files**
   - See all previously uploaded files in "Recent Files"
   - Click "View Details" to see full analysis
   - Click "Refresh" to update the list

## API Endpoints

### `GET /`
Health check and API info

### `POST /upload`
Upload and process a file
- **Body**: `multipart/form-data` with `file` field
- **Returns**: Processed data with AI analysis

### `GET /files`
List all processed files
- **Returns**: Array of file metadata

### `GET /files/<id>`
Get specific file details
- **Returns**: Complete file data and analysis

### `GET /health`
Check API and Ollama status
- **Returns**: Service health status

## Project Structure

```
Car-Lease/
├── backend/
│   ├── app.py              # Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   ├── .gitignore         # Git ignore file
│   ├── uploads/           # Uploaded files (auto-created)
│   └── processed/         # Processed data (auto-created)
│
└── frontend/
    ├── index.html         # Main HTML page
    ├── styles.css         # Styling
    └── script.js          # JavaScript logic
```

## Configuration

### Backend Configuration

Edit `.env` file or modify `app.py`:

- **Upload folder**: `UPLOAD_FOLDER = 'uploads'`
- **Processed folder**: `PROCESSED_FOLDER = 'processed'`
- **Max file size**: `MAX_CONTENT_LENGTH = 16 * 1024 * 1024` (16MB)
- **Allowed extensions**: `ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}`
- **Ollama model**: Change in `process_with_ollama()` function (default: `llama3.2`)

### Frontend Configuration

Edit `script.js`:

- **API URL**: `const API_URL = 'http://localhost:3000'`

## Troubleshooting

### Ollama Not Connected
- Ensure Ollama is running: `ollama serve`
- Check if the model is pulled: `ollama list`
- Pull a model if needed: `ollama pull llama3.2`

### CORS Errors
- Make sure Flask-CORS is installed
- Check that the backend is running on port 3000
- Update `API_URL` in `script.js` if using different port

### File Upload Fails
- Check file size (max 16MB)
- Verify file format is supported
- Check console for detailed error messages

### Port Already in Use
- Change the port in `app.py`: `app.run(port=5001)`
- Update `API_URL` in `script.js` accordingly

## Development

### Adding New File Types

1. Add extension to `ALLOWED_EXTENSIONS` in `app.py`
2. Update `extract_text_from_file()` function to handle new type
3. Add appropriate parsing library to `requirements.txt`

### Customizing AI Analysis

Modify the `process_with_ollama()` function in `app.py`:
- Change the prompt to extract different information
- Switch to a different Ollama model
- Adjust response format

## License

MIT License - feel free to use this project for your own purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
