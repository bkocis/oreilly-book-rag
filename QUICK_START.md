# 🚀 O'Reilly RAG Quiz App - Quick Start Guide

This guide will help you get the O'Reilly RAG Quiz application up and running in just a few steps!

## Prerequisites

Before running the application, make sure you have:

- ✅ **Docker** - For running Qdrant vector database
- ✅ **Python 3.8+** - With virtual environment at `~/venv/oreilly-rag`
- ✅ **Node.js & npm** - For the React frontend
- ✅ **curl** - For health checks (usually pre-installed)

## 🎯 Quick Start

### Option 1: One-Command Start (Recommended)

```bash
./run.sh
```

This single command will:
- Start Qdrant vector database (Docker container)
- Start the FastAPI backend on port 8000
- Start the React frontend on port 5173
- Show you all the service URLs and status

### Option 2: Manual Start

If you prefer to start services manually:

```bash
# 1. Start Qdrant
docker run -d --name qdrant-oreilly -p 6333:6333 -p 6334:6334 qdrant/qdrant

# 2. Start Backend
cd backend
source ~/venv/oreilly-rag/bin/activate
python -m app.main

# 3. Start Frontend (in another terminal)
cd frontend
npm run dev
```

## 🌐 Access Your Application

Once running, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend App** | http://localhost:5173 | Main React application |
| **API Documentation** | http://localhost:8000/docs | Interactive API docs |
| **API Health Check** | http://localhost:8000/health | Backend status |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | Vector database UI |

## 📋 Available Features

### Document Processing API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/documents/upload` | POST | Upload PDF documents |
| `/api/v1/documents/list` | GET | List all documents |
| `/api/v1/documents/processing-status/{task_id}` | GET | Check processing status |
| `/api/v1/documents/metadata/{file_name}` | GET | Get document metadata |
| `/api/v1/documents/delete/{file_name}` | DELETE | Remove documents |
| `/api/v1/documents/extract-topics` | POST | Extract topics from text |

## 🛑 Stopping the Application

### Option 1: Stop All Services

```bash
./stop.sh
```

### Option 2: Stop Everything Including Database

```bash
./stop.sh --with-qdrant
```

### Option 3: Manual Stop

- Press `Ctrl+C` in each terminal running the services
- Stop Qdrant: `docker stop qdrant-oreilly`

## 📂 Project Structure

```
oreilly-rag/
├── run.sh              # 🚀 Start script
├── stop.sh             # 🛑 Stop script
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── services/   # Core services
│   │   └── main.py     # FastAPI app
│   └── requirements.txt
├── frontend/           # React frontend
│   ├── src/
│   └── package.json
└── logs/              # Application logs
    ├── backend.log
    └── frontend.log
```

## 🧪 Testing the API

### Upload a PDF Document

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your-document.pdf"
```

### Check Processing Status

```bash
curl "http://localhost:8000/api/v1/documents/processing-status/{task-id}"
```

### Extract Topics from Text

```bash
curl -X POST "http://localhost:8000/api/v1/documents/extract-topics" \
     -H "Content-Type: application/json" \
     -d '{"text": "Your text here", "max_topics": 5}'
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check what's using the port
lsof -i :8000  # For backend
lsof -i :5173  # For frontend
lsof -i :6333  # For Qdrant

# Kill the process if needed
kill -9 <PID>
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
python -m venv ~/venv/oreilly-rag
source ~/venv/oreilly-rag/bin/activate
pip install -r backend/requirements.txt
```

### Docker Issues
```bash
# Check Docker status
docker ps
docker logs qdrant-oreilly

# Remove and recreate Qdrant container
docker rm -f qdrant-oreilly
docker run -d --name qdrant-oreilly -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### Frontend Build Issues
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## 📊 Log Files

Application logs are stored in the `logs/` directory:

- `logs/backend.log` - Backend API logs
- `logs/frontend.log` - Frontend build logs

View logs in real-time:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

## 🎯 Current Status

✅ **Phase 1-2**: Environment setup and document processing - **COMPLETED**
✅ **Step 7**: Document Processing API - **COMPLETED**

### What's Working:
- PDF document upload and processing
- Background document parsing and indexing
- Vector database storage with Qdrant
- Real-time processing status tracking
- Topic and concept extraction
- Document metadata extraction
- Comprehensive API with interactive docs

### Next Steps:
- Step 8: Quiz Generation Service
- Quiz question generation from indexed documents
- Frontend quiz interface
- Learning analytics and progress tracking

## 💡 Tips

1. **Use the run script** - It handles all the complexity for you
2. **Check the logs** - If something goes wrong, check `logs/backend.log`
3. **API Documentation** - Visit `/docs` for interactive API testing
4. **Health Checks** - All services have health check endpoints
5. **Background Processing** - Document uploads return immediately with a task ID

---

🎉 **Happy Learning with Your RAG Quiz App!** 🎉 