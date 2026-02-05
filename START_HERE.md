# 🚀 ONE-CLICK STARTUP FILES

This folder contains everything you need to start the Car Lease Review AI Assistant with **one click**!

## 📋 Files Overview

```
golive.bat              ← Double-click this (Windows)
golive.ps1              ← PowerShell script (advanced users)
golive.sh               ← Linux/Mac startup script
create-shortcut.ps1     ← Creates desktop shortcut
GOLIVE_GUIDE.md         ← Detailed documentation
```

## ⚡ Quick Start

### For Windows Users:
**Just double-click `golive.bat`** in File Explorer!

### For Linux/Mac Users:
```bash
chmod +x golive.sh
./golive.sh
```

## 🎁 Want a Desktop Shortcut?

**Windows Only:**
1. Right-click `create-shortcut.ps1`
2. Select "Run with PowerShell"
3. Find "Car Lease AI Assistant" shortcut on your desktop!

## 📍 What Happens?

When you run `golive.bat`, it will:

1. ✅ Check if Docker is running
2. ✅ Start PostgreSQL database
3. ✅ Create Python virtual environment (first time only)
4. ✅ Install all required packages
5. ✅ Initialize database with sample data
6. ✅ Start the web server

Then you can access:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Database UI**: http://localhost:5050

## ⏱️ How Long Does It Take?

- **First run**: 2-5 minutes (downloads & installs everything)
- **Subsequent runs**: 10-15 seconds

## 🛑 How to Stop?

Press `Ctrl+C` in the terminal window.

The database will keep running in the background. To stop it:
```bash
docker-compose down
```

## ❓ Need Help?

See [GOLIVE_GUIDE.md](GOLIVE_GUIDE.md) for:
- Detailed troubleshooting
- Advanced configuration
- System requirements
- FAQ

## 🔧 Requirements

- **Docker Desktop** (Windows/Mac) or Docker Engine (Linux)
- **Python 3.8+**
- ~500MB free disk space

That's it! Happy coding! 🎉
