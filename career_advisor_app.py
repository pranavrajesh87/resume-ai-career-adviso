import pdfplumber
import spacy
import re
import requests
import gradio as gr
import matplotlib.pyplot as plt
from openai import OpenAI
import os

nlp = spacy.load("en_core_web_sm")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def parse_resume(file):
    text = ""
    with pdfplumber.open(file.name) as pdf:
        for page in pdf.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    if not text.strip():
        text = "No extractable text found in resume."
    doc = nlp(text)
    email = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone = re.findall(r"\+?\d[\d -]{8,}\d", text)
    predefined_skills = [
        "Python","SQL","Machine Learning","Java","Pandas","Numpy",
        "PyTorch","Excel","AWS","Docker","Deep Learning",
        "Data Analysis","HTML","CSS","JavaScript","C++","C",
        "TensorFlow","Keras","Tableau","PowerBI","Flask","Django"
    ]
    skills = [token.text for token in doc if token.text in predefined_skills]
    education_keywords = [
        "B.Tech","BSc","MSc","Bachelor","Master","University",
        "College","Institute","School","PhD"
    ]
    education = [line for line in text.split("\n") if any(kw in line for kw in education_keywords)]
    experience = []
    exp_section = False
    for line in text.split("\n"):
        if "experience" in line.lower() or "internship" in line.lower() or "work" in line.lower():
            exp_section = True
        elif exp_section and line.strip() == "":
            exp_section = False
        elif exp_section:
            experience.append(line.strip())
    return {
        "email": email,
        "phone": phone,
        "skills": list(set(skills)),
        "education": education,
        "experience": experience
    }

def generate_resume_summary_with_llm(resume_data):
    if not client:
        return "⚠️ AI summary unavailable. Please add your OpenAI API key as an environment variable."
    try:
        context = f"""
Email: {resume_data.get('email', ['Not found'])[0] if resume_data.get('email') else 'Not found'}
Phone: {resume_data.get('phone', ['Not found'])[0] if resume_data.get('phone') else 'Not found'}
Education: {', '.join(resume_data.get('education', [])) or 'Not found'}
Experience: {', '.join(resume_data.get('experience', [])) or 'Not found'}
Skills: {', '.join(resume_data.get('skills', [])) or 'Not detected'}
"""
        prompt = f"""
You are a career advisor AI. Write a professional 3–4 line summary 
of the following candidate's resume. Highlight strengths and suggest
one improvement area if possible.

Resume Data:
{context}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "AI summary unavailable. Resume parsed successfully, but GPT service failed."

APP_ID = "06a78f1f"
APP_KEY = "c4daf87273bf98bdc54736335124c156"
COUNTRY = "in"

def fetch_job_skills(title="Data Scientist"):
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
    params = {"app_id": APP_ID, "app_key": APP_KEY, "what": title, "results_per_page": 50}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        descriptions = " ".join([job["description"] for job in data.get("results", [])])
        doc = nlp(descriptions)
        predefined_skills = [
            "Python","SQL","Machine Learning","Java","Pandas","Numpy",
            "PyTorch","Excel","AWS","Docker","Deep Learning",
            "Data Analysis","HTML","CSS","JavaScript","C++","C",
            "TensorFlow","Keras","Tableau","PowerBI","Flask","Django"
        ]
        return list(set([token.text for token in doc if token.text in predefined_skills]))
    return []

def skill_gap(resume_file, job_title):
    resume_data = parse_resume(resume_file)
    market_skills = fetch_job_skills(job_title)
    matched = list(set(resume_data["skills"]) & set(market_skills))
    missing = list(set(market_skills) - set(resume_data["skills"]))
    recommendations = [
        f"[Learn {skill} on Coursera](https://www.coursera.org/search?query={skill})"
        for skill in missing
    ]
    sizes = [len(matched), len(missing)]
    if sum(sizes) == 0:
        sizes = [1, 0]
        labels = ['No Skills Found', '']
        colors = ['#FF6347','#00CED1']
    else:
        labels = ['Matched Skills', 'Missing Skills']
        colors = ['#FF6347','#00CED1']
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
    ax.set_title("Skill Gap Analysis")
    ax.axis('equal')
    ai_summary = generate_resume_summary_with_llm(resume_data)
    summary = f"""
<style>
body {{background-color: #001f3f; color: white; font-family: Arial, sans-serif;}}
a {{color: #00FF00; text-decoration: none;}}
</style>

## 🤖 AI Resume Summary
{ai_summary}

## 📄 Resume Extracted Info
- **Email:** {resume_data['email'][0] if resume_data['email'] else "Not found"}
- **Phone:** {resume_data['phone'][0] if resume_data['phone'] else "Not found"}
- **Education:** {"<br>".join(resume_data['education']) if resume_data['education'] else "Not found"}
- **Experience:** {"<br>".join(resume_data['experience']) if resume_data['experience'] else "Not found"}

## 💡 Skills 
- **Resume Skills:** {", ".join(resume_data['skills']) if resume_data['skills'] else "None detected"}
- **Market Skills for '{job_title}':** {", ".join(market_skills) if market_skills else "None found"}

## 📊 Skill Gap Analysis
- **Matched Skills:** {", ".join(matched) if matched else "None"}
- **Missing Skills:** {"; ".join(missing) if missing else "None"}

## 🎯 Recommendations
{''.join(f"- {r}<br>" for r in recommendations) if recommendations else 'You match all key skills!'}
"""
    return summary, fig

career_options = [
    "Data Scientist","Machine Learning Engineer","AI Engineer","Web Developer",
    "Backend Developer","Frontend Developer","Full Stack Developer",
    "DevOps Engineer","Cloud Engineer","Data Analyst","Business Intelligence Analyst",
    "Software Engineer","Mobile App Developer","Cybersecurity Analyst"
]

iface = gr.Interface(
    fn=skill_gap,
    inputs=[
        gr.File(label="Upload Resume (PDF)"),
        gr.Dropdown(choices=career_options, label="Select Target Career")
    ],
    outputs=[
        gr.Markdown(),
        gr.Plot()
    ],
    title="🧑‍💻 AI-Powered Career Advisor",
    description="Upload your resume and select your target career to see AI-written summary, skill gaps, and recommendations.",
    theme="default"
)

if __name__ == "__main__":
    iface.launch()
