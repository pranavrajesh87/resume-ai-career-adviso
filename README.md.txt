# 🧑‍💻 AI-Powered Career Advisor

This project allows users to upload their resume and select a tech career to get:

- **AI-generated resume summary** (falls back to regex parsing if AI fails)
- **Extracted information:** email, phone, education, experience, skills
- **Skill gap analysis** with recommendations for missing skills
- **Interactive visualizations** using pie charts

## Features

- Works with **PDF resumes**
- Supports multiple **tech careers** via a dropdown
- Uses **spaCy** for text parsing, **regex** for email/phone extraction
- **Gradio** provides a user-friendly web interface

## How to Use

1. Clone the repository or download the files.
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
pdfplumber
spacy
requests
gradio
matplotlib
openai 