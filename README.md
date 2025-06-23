# O'Reilly Book RAG - Interactive Learning Platform

[![Build in Public](https://img.shields.io/badge/Build%20in%20Public-🚀-blue.svg)](https://buildinpublic.xyz/)
[![Built with Cursor](https://img.shields.io/badge/Built%20with-Cursor-blueviolet.svg)](https://cursor.sh/)

Learn from your PDF books - build quizzes, Q&A, and chat for learning from your books.

## Overview

This project implements a Retrieval-Augmented Generation (RAG) solution for creating an interactive quiz-based learning platform from O'Reilly books. The system transforms static PDF content into dynamic, engaging learning experiences through AI-powered quiz generation, adaptive learning paths, and comprehensive progress tracking.

## Key Features

### 📚 Document Processing
- **PDF Parsing**: Extract text, metadata, and structure from O'Reilly books
- **Smart Chunking**: Optimized content segmentation for quiz generation
- **Vector Indexing**: Fast semantic search using embeddings and vector databases

### 🎯 Quiz Generation
- **Multiple Question Types**: Multiple choice, true/false, fill-in-the-blank, short answer
- **Concept-Based Questions**: Focus on key concepts, definitions, and examples
- **Application Questions**: Real-world scenarios and practical applications
- **Code Questions**: Programming-specific questions for technical books
- **Adaptive Difficulty**: Questions adjust based on user performance

### 🧠 Learning Intelligence
- **Progress Tracking**: Detailed analytics and learning insights
- **Spaced Repetition**: Optimized review scheduling for better retention
- **Knowledge Gap Analysis**: Identify areas needing improvement
- **Personalized Recommendations**: Customized learning paths

### 🎮 Gamification
- **Points & Badges**: Reward system for achievements
- **Learning Streaks**: Daily study motivation
- **Leaderboards**: Social learning competition
- **Study Groups**: Collaborative learning features

### 📊 Analytics Dashboard
- **Performance Visualization**: Charts and graphs showing learning progress
- **Mastery Tracking**: Subject and topic proficiency levels
- **Study Insights**: Detailed learning analytics and recommendations
- **Export Reports**: Share progress with instructors or peers

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for APIs
- **LlamaIndex**: Document processing and RAG implementation
- **SentenceTransformers**: High-quality text embeddings
- **ChromaDB/FAISS**: Vector database for semantic search
- **PostgreSQL**: User data, quizzes, and progress storage
- **SQLAlchemy**: Database ORM and migrations

### Frontend
- **React**: Modern UI framework with Vite build tool
- **Tailwind CSS**: Utility-first styling
- **React Query**: Server state management
- **Framer Motion**: Smooth animations and transitions
- **Chart.js/Recharts**: Data visualization

## Project Structure

```
oreilly-rag/
├── backend/          # FastAPI backend with RAG services
├── frontend/         # React frontend application
├── data/            # Processed documents and embeddings
├── resources/       # PDF books and source materials
└── docs/           # Documentation and guides
```

## Getting Started

*Coming soon - Setup instructions and installation guide*

## Development Status

This project is currently in planning phase with a comprehensive implementation roadmap covering:

- **Phase 1-2**: Environment setup and document processing pipeline
- **Phase 3-4**: Quiz generation core and backend API development  
- **Phase 5**: Frontend development with modern UI/UX
- **Phase 6**: Advanced features (adaptive learning, social features)
- **Phase 7-8**: Integration, testing, and deployment

## Contributing

*Coming soon - Contribution guidelines and development setup*

## License

*Coming soon - License information*

---

Transform your static PDF books into dynamic, interactive learning experiences with AI-powered quizzes and personalized learning paths.
