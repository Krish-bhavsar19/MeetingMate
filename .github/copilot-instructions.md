<!-- Smart Meeting AI - AI-powered Meeting Assistant -->

## Project Overview
This is an AI-powered Smart Meeting Assistant that transforms meeting audio into actionable insights using:
- OpenAI Whisper for speech-to-text transcription
- Hugging Face Transformers (BART/T5) for summarization
- spaCy for action item extraction
- FastAPI backend with MongoDB database
- React.js frontend with TailwindCSS
- Docker containerization and Azure deployment

## Architecture
- Backend: FastAPI (Python) with ML/NLP processing
- Frontend: React.js with TailwindCSS
- Database: MongoDB for storing transcripts and summaries
- ML Models: Whisper, BART/T5, spaCy
- Deployment: Docker + Azure App Service

## Development Guidelines
- Follow REST API best practices for FastAPI endpoints
- Use async/await patterns for ML model processing
- Implement proper error handling for audio processing
- Use TypeScript for React components when possible
- Maintain clean separation between ML processing and API layers

## Key Features
- Real-time audio transcription
- Automatic meeting summarization
- Action item extraction
- User dashboard for meeting management
- Calendar integration capabilities