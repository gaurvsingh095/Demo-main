# # File: app.py
# from flask import Flask, request, jsonify
# import io
# import contextlib
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(__name__)

# # Single-route serving inline HTML with embedded CSS & JS
# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#   <meta charset="UTF-8" />
#   <meta name="viewport" content="width=device-width, initial-scale=1.0" />
#   <title>Resume Rewriting Agent</title>
#   <style>
#     body { font-family: Arial, sans-serif; background: #f4f7f8; color: #333; padding: 20px; }
#     .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
#     h1 { text-align: center; margin-bottom: 20px; }
#     textarea, input[type="text"] { width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
#     button { padding: 10px 20px; margin: 5px; border: none; background: #007bff; color: #fff; border-radius: 4px; cursor: pointer; transition: background 0.3s; }
#     button:hover { background: #0056b3; }
#     .output { background: #eef; padding: 15px; border-radius: 4px; margin-top: 20px; display: none; }
#   </style>
# </head>
# <body>
#   <div class="container">
#     <h1>Resume Rewriting Agent</h1>
#     <div class="step" id="step1">
#       <label for="resume_text">Paste your resume:</label><br />
#       <textarea id="resume_text" rows="10"></textarea><br />
#       <button id="toStep2">Next</button>
#     </div>
#     <div class="step" id="step2" style="display:none;">
#       <label for="job_url">Enter job description URL:</label><br />
#       <input type="text" id="job_url" /><br />
#       <button id="toStep1">Back</button>
#       <button id="submitBtn">Submit</button>
#     </div>
#     <div class="output" id="output">
#       <h2>Result:</h2>
#       <pre id="outputText"></pre>
#     </div>
#   </div>
#   <script>
#     const step1 = document.getElementById('step1');
#     const step2 = document.getElementById('step2');
#     const toStep2 = document.getElementById('toStep2');
#     const toStep1 = document.getElementById('toStep1');
#     const submitBtn = document.getElementById('submitBtn');
#     const outputDiv = document.getElementById('output');
#     const outputText = document.getElementById('outputText');

#     toStep2.addEventListener('click', () => {
#       step1.style.display = 'none';
#       step2.style.display = 'block';
#     });
#     toStep1.addEventListener('click', () => {
#       step2.style.display = 'none';
#       step1.style.display = 'block';
#     });

#     submitBtn.addEventListener('click', async () => {
#       const resumeText = document.getElementById('resume_text').value;
#       const jobUrl = document.getElementById('job_url').value;
#       try {
#         const res = await fetch('/api/run', {
#           method: 'POST',
#           headers: { 'Content-Type': 'application/json' },
#           body: JSON.stringify({ resume_text: resumeText, job_url: jobUrl })
#         });
#         const data = await res.json();
#         outputText.textContent = data.output;
#         outputDiv.style.display = 'block';
#       } catch (err) {
#         outputText.textContent = 'Error: ' + err;
#         outputDiv.style.display = 'block';
#       }
#     });
#   </script>
# </body>
# </html>
# """

# @app.route('/', methods=['GET'])
# def index():
#     return HTML_PAGE

# @app.route('/api/run', methods=['POST'])
# def api_run_crew():
#     data = request.get_json() or {}
#     resume_text = data.get('resume_text', '')
#     job_url = data.get('job_url', '')

#     buf = io.StringIO()
#     with contextlib.redirect_stdout(buf):
#         inputs = {'resume_text': resume_text, 'job_description_url': job_url}
#         crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#         crew.kickoff(inputs=inputs)
#     return jsonify({'output': buf.getvalue()})

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
# yth
# File: app.py
# from flask import Flask, request, jsonify
# import io
# import contextlib
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(__name__)

# # Single-route serving inline HTML with embedded CSS & JS & Markdown support
# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang=\"en\">
# <head>
#   <meta charset=\"UTF-8\" />
#   <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
#   <title>Resume Rewriting Agent</title>
#   <style>
#     body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #333; margin: 0; padding: 0; }
#     .container { max-width: 700px; margin: 50px auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
#     h1 { text-align: center; margin-bottom: 30px; color: #222; }
#     textarea, input[type=\"text\"] { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }
#     button { padding: 12px 24px; margin: 5px; border: none; background: #28a745; color: #fff; font-size: 1rem; border-radius: 6px; cursor: pointer; transition: background 0.3s; }
#     button:hover { background: #218838; }
#     .spinner { width: 50px; height: 50px; border: 6px solid #eee; border-top: 6px solid #28a745; border-radius: 50%; animation: spin 1s linear infinite; margin: 20px auto; }
#     @keyframes spin { to { transform: rotate(360deg); } }
#     .status { text-align: center; font-weight: 500; margin-top: 10px; }
#     .output { background: #fafafa; padding: 20px; border-radius: 6px; margin-top: 30px; display: none; }
#   </style>
#   <script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>
# </head>
# <body>
#   <div class=\"container\">
#     <h1>Resume Rewriting Agent</h1>
#     <div class=\"step\" id=\"step1\">
#       <label for=\"resume_text\">Paste your resume:</label>
#       <textarea id=\"resume_text\" rows=\"8\"></textarea>
#       <button id=\"toStep2\">Next Step</button>
#     </div>
#     <div class=\"step\" id=\"step2\" style=\"display:none;\">
#       <label for=\"job_url\">Job description URL:</label>
#       <input type=\"text\" id=\"job_url\" placeholder=\"https://...\" />
#       <button id=\"toStep1\">Back</button>
#       <button id=\"submitBtn\">Submit</button>
#     </div>
#     <div id=\"loadingBox\" style=\"display:none; text-align:center;\">
#       <div class=\"spinner\"></div>
#       <div class=\"status\" id=\"statusText\">Initializing...</div>
#     </div>
#     <div class=\"output\" id=\"output\">
#       <h2>Result</h2>
#       <div id=\"outputMarkdown\"></div>
#     </div>
#   </div>
#   <script>
#     const steps = { step1: document.getElementById('step1'), step2: document.getElementById('step2') };
#     const toStep2 = document.getElementById('toStep2');
#     const toStep1 = document.getElementById('toStep1');
#     const submitBtn = document.getElementById('submitBtn');
#     const loadingBox = document.getElementById('loadingBox');
#     const statusText = document.getElementById('statusText');
#     const outputDiv = document.getElementById('output');
#     const outputMarkdown = document.getElementById('outputMarkdown');
#     let statusInterval;
#     const statuses = ['Extracting Resume...', 'Analyzing Job Description...', 'Crafting Your Resume'];

#     toStep2.onclick = () => { steps.step1.style.display='none'; steps.step2.style.display='block'; };
#     toStep1.onclick = () => { steps.step2.style.display='none'; steps.step1.style.display='block'; };

#     submitBtn.onclick = async () => {
#       // hide form, show loader
#       steps.step2.style.display = 'none';
#       loadingBox.style.display = 'block';
#       outputDiv.style.display = 'none';

#       // cycle status messages
#       let idx = 0;
#       statusText.textContent = statuses[idx];
#       statusInterval = setInterval(() => {
#         idx = (idx + 1) % statuses.length;
#         statusText.textContent = statuses[idx];
#       }, 1500);

#       const payload = { resume_text: document.getElementById('resume_text').value, job_url: document.getElementById('job_url').value };
#       try {
#         const res = await fetch('/api/run', { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify(payload) });
#         const data = await res.json();
#         outputMarkdown.innerHTML = marked.parse(data.output);
#       } catch (err) {
#         outputMarkdown.textContent = 'Error: ' + err;
#       } finally {
#         clearInterval(statusInterval);
#         loadingBox.style.display = 'none';
#         outputDiv.style.display = 'block';
#       }
#     };
#   </script>
# </body>
# </html>
# """

# @app.route('/', methods=['GET'])
# def index():
#     return HTML_PAGE

# @app.route('/api/run', methods=['POST'])
# def api_run_crew():
#     data = request.get_json() or {}
#     resume_text = data.get('resume_text', '')
#     job_url = data.get('job_url', '')

#     buf = io.StringIO()
#     with contextlib.redirect_stdout(buf):
#         inputs = {'resume_text': resume_text, 'job_description_url': job_url}
#         crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#         crew.kickoff(inputs=inputs)
#     return jsonify({'output': buf.getvalue()})

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
# File: app.py
# from flask import Flask, request, jsonify
# import io
# import contextlib
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew
# import PyPDF2

# app = Flask(__name__)

# # Single-route serving inline HTML with embedded CSS & JS & Markdown support
# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang=\"en\">    
# <head>
#   <meta charset=\"UTF-8\" />
#   <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
#   <title>Resume Rewriting Agent</title>
#   <style>
#     body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #333; margin: 0; padding: 0; }
#     .container { max-width: 700px; margin: 50px auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
#     h1 { text-align: center; margin-bottom: 30px; color: #222; }
#     input[type=\"file\"], input[type=\"text\"], textarea { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }
#     button { padding: 12px 24px; margin: 5px; border: none; background: #28a745; color: #fff; font-size: 1rem; border-radius: 6px; cursor: pointer; transition: background 0.3s; }
#     button:hover { background: #218838; }
#     .spinner { width: 50px; height: 50px; border: 6px solid #eee; border-top: 6px solid #28a745; border-radius: 50%; animation: spin 1s linear infinite; margin: 20px auto; }
#     @keyframes spin { to { transform: rotate(360deg); } }
#     .status { text-align: center; font-weight: 500; margin-top: 10px; }
#     .output { background: #fafafa; padding: 20px; border-radius: 6px; margin-top: 30px; display: none; }
#   </style>
#   <script src=\"https://cdn.jsdelivr.net/npm/marked/marked.min.js\"></script>
# </head>
# <body>
# <header>
#     <div class="logo">
#       <img src="{{ url_for('static', filename='cellanova_logo.png') }}" alt="CellaNova Tech" />
#       <h1>CellaNova Tech</h1>
#     </div>
#     <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
#       <svg id="themeIcon"><use xlink:href="#icon-moon" /></svg>
#     </button>
#   </header>
#   <main>
#   <div class=\"container\">
#     <h1>Resume Rewriting Agent</h1>
#     <div class=\"step\" id=\"step1\">
#       <label for=\"resume_pdf\">Upload your resume PDF:</label>
#       <input type=\"file\" id=\"resume_pdf\" accept=\"application/pdf\" />
#       <button id=\"toStep2\" disabled>Next Step</button>
#     </div>
#     <div class=\"step\" id=\"step2\" style=\"display:none;\">
#       <label for=\"job_url\">Job description URL:</label>
#       <input type=\"text\" id=\"job_url\" placeholder=\"https://...\" />
#       <button id=\"toStep1\">Back</button>
#       <button id=\"submitBtn\">Submit</button>
#     </div>
#     <div id=\"loadingBox\" style=\"display:none; text-align:center;\">
#       <div class=\"spinner\"></div>
#       <div class=\"status\" id=\"statusText\">Initializing...</div>
#     </div>
#     <div class=\"output\" id=\"output\">
#       <h2>Rewritten Resume</h2>
#       <div id=\"outputMarkdown\"></div>
#     </div>
#   </div>
#   </main>
#   <script>
#     const steps = { step1: document.getElementById('step1'), step2: document.getElementById('step2') };
#     const resumePdf = document.getElementById('resume_pdf');
#     const toStep2 = document.getElementById('toStep2');
#     const toStep1 = document.getElementById('toStep1');
#     const submitBtn = document.getElementById('submitBtn');
#     const loadingBox = document.getElementById('loadingBox');
#     const statusText = document.getElementById('statusText');
#     const outputDiv = document.getElementById('output');
#     const outputMarkdown = document.getElementById('outputMarkdown');
#     let extractedText = '';
#     // Enable Next when file chosen
#     resumePdf.onchange = () => { toStep2.disabled = !resumePdf.files.length; };
#     toStep2.onclick = async () => {
#       const file = resumePdf.files[0];
#       if (!file) return;
#       // Extract PDF text
#       loadingBox.style.display = 'block';
#       statusText.textContent = 'Extracting PDF text...';
#       const form = new FormData(); form.append('pdf', file);
#       const resp = await fetch('/api/extract', { method:'POST', body: form });
#       const j = await resp.json(); extractedText = j.text;
#       loadingBox.style.display = 'none';
#       steps.step1.style.display='none'; steps.step2.style.display='block';
#     };
#     toStep1.onclick = () => { steps.step2.style.display='none'; steps.step1.style.display='block'; };
#     submitBtn.onclick = async () => {
#       steps.step2.style.display = 'none'; loadingBox.style.display = 'block'; outputDiv.style.display = 'none';
#       // spinner statuses
#       const statuses = ['Analyzing Job Description...', 'Crafting Your Resume...']; let idx=0;
#       statusText.textContent = statuses[idx]; const interval = setInterval(() => { idx=(idx+1)%statuses.length; statusText.textContent = statuses[idx]; }, 1500);
#       try {
#         const res = await fetch('/api/run', { method:'POST', headers:{ 'Content-Type':'application/json' }, body: JSON.stringify({ resume_text: extractedText, job_url: document.getElementById('job_url').value }) });
#         const data = await res.json(); outputMarkdown.innerHTML = marked.parse(data.output);
#       } catch(err) { outputMarkdown.textContent = 'Error: '+err; }
#       clearInterval(interval); loadingBox.style.display='none'; outputDiv.style.display='block';
#     };
#   </script>
# </body>
# </html>
# """

# @app.route('/', methods=['GET'])
# def index():
#     return HTML_PAGE

# @app.route('/api/extract', methods=['POST'])
# def extract_pdf():
#     file = request.files.get('pdf')
#     if not file:
#         return jsonify({'text': ''})
#     reader = PyPDF2.PdfReader(file)
#     text = []
#     for page in reader.pages:
#         text.append(page.extract_text() or '')
#     return jsonify({'text': '\n'.join(text)})

# @app.route('/api/run', methods=['POST'])
# @app.route('/api/run', methods=['POST'])
# def api_run_crew():
#     data = request.get_json() or {}
#     resume_text = data.get('resume_text', '')
#     job_url = data.get('job_url', '')
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()

#     # Execute crew and normalize output
#     result = crew.kickoff(inputs={'resume_text': resume_text, 'job_description_url': job_url})
#     if isinstance(result, str): 
#         output = result
#     else:
#         output = str(result)

#     return jsonify({'output': output.strip()})

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)(debug=True, port=5000)
# app.py
import io
import PyPDF2
from flask import Flask, render_template, request, jsonify, send_file
from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew
# at top of app.py, add:
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, ListFlowable, ListItem
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(
    __name__,
    static_folder="assets",
    static_url_path="/assets",
    template_folder="templates"
)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>CellaNova Tech • Resume Builder</title>
  <style>
    /* ===========================================
   CellaNova Tech • Resume Builder - Styles
   Copy & paste this into your CSS file
   =========================================== */

/* ---- COLOR PALETTES & TYPOGRAPHY ---- */
:root {
  --color-bg: #121212;            /* dark page background */
  --color-surface: #0d1b2a;       /* card/panel background */
  --color-text: #E0E0E0;          /* main text */
  --color-muted: #757575;         /* secondary text */
  --color-primary: #1ABC9C;       /* brand green */
  --color-secondary: #FFC107;     /* accent gold */
  --color-accent: #FF5722;        /* highlight orange */
  --radius: 8px;                  /* border radius */
  --transition: 0.3s;             /* global transition */
  --font-stack: "Inter", -apple-system, BlinkMacSystemFont,
                "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --footer-height: 200px;         /* reserve space for footer */
}

/* light mode overrides */
html[data-theme="light"] {
  --color-bg: #f4f7fa;
  --color-surface: #ffffff;
  --color-text: #333333;
  --color-muted: #888888;
}

*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  width: 100%;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-stack);
  transition: background var(--transition),
              color var(--transition);
}

/* slim, dark scrollbars */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: var(--color-bg);
}
::-webkit-scrollbar-thumb {
  background: #111;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #333;
}

body {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ---- HEADER ---- */
header {
  background: var(--color-surface);
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 4px rgba(0,0,0,0.7);
  transition: background var(--transition);
}
.logo {
  display: flex;
  align-items: center;
}
.logo img {
  height: 36px;
  margin-right: 0.75rem;
}
.logo h1 {
  font-size: 1.25rem;
  letter-spacing: 0.05em;
  color: var(--color-text);
}
.theme-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--radius);
  transition: background var(--transition);
}
.theme-toggle:hover {
  background: rgba(0,0,0,0.1);
}
.theme-toggle svg {
  width: 24px;
  height: 24px;
  fill: var(--color-text);
  transition: fill var(--transition);
}

/* ---- MAIN BUILDER ---- */
main {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 6rem 2rem 2rem;
  padding-bottom: calc(var(--footer-height) + 2rem);
}

.builder-container {
  background: var(--color-surface);
  border-radius: var(--radius);
  box-shadow: 0 8px 24px rgba(0,0,0,0.7);
  width: 100%;
  max-width: 800px;
  overflow: hidden;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.builder-header {
  background: var(--color-primary);
  padding: 1rem;
  text-align: center;
  color: var(--color-surface);
  font-size: 1.5rem;
}

.builder-body {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* step inputs */
.step {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
label {
  color: var(--color-muted);
  font-size: 0.95rem;
}
input[type="file"],
input[type="text"] {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: var(--radius);
  background: #222;
  color: var(--color-text);
  transition: background var(--transition),
              transform var(--transition);
}
input:focus {
  outline: 2px solid var(--color-accent);
  background: #333;
  transform: scale(1.02);
}
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
button {
  padding: 0.6rem 1.2rem;
  background: var(--color-accent);
  color: var(--color-surface);
  border: none;
  border-radius: var(--radius);
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition),
              transform var(--transition);
}
button:disabled {
  background: var(--color-muted);
  opacity: 0.6;
  cursor: not-allowed;
}
button:hover:not(:disabled) {
  background: var(--color-secondary);
  transform: translateY(-2px) scale(1.03);
}

/* spinner & loader */
.spinner {
  width: 48px;
  height: 48px;
  border: 6px solid var(--color-muted);
  border-top: 6px solid var(--color-accent);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 1.5rem auto;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.status {
  text-align: center;
  font-style: italic;
  color: var(--color-muted);
}

/* ---- FULL-SCREEN MARKDOWN OUTPUT ---- */
#markdownOutputWrapper {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: var(--color-bg);
  overflow-y: auto;
  padding: 2rem;
  z-index: 100;
}
.markdown-toolbar {
  display: none;
  position: fixed;
  top: 1rem;
  right: 1rem;
  gap: 0.5rem;
  z-index: 110;
}
.markdown-toolbar button {
  background: var(--color-accent);
  color: var(--color-surface);
  border: none;
  border-radius: var(--radius);
  padding: 0.5rem 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--transition);
}
.markdown-toolbar button:hover {
  background: var(--color-secondary);
}
#renderedOutput {
  max-width: 800px;
  margin: auto;
  color: var(--color-text);
  line-height: 1.6;
}
#outputArea {
  display: none;
  width: 100%;
  height: calc(100vh - 4rem);
  margin-top: 1rem;
  background: var(--color-surface);
  color: var(--color-text);
  border: none;
  border-radius: var(--radius);
  padding: 1rem;
  font-family: monospace;
  font-size: 0.95rem;
}

/* ---- FOOTER ---- */
footer.site-footer {
  background: var(--color-surface);
  color: var(--color-text);
  padding: 2rem 1rem 1rem;
  margin-top: auto;
}
.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 2rem;
}
.footer-brand-social {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.footer-logo {
  width: 40px;
  height: 40px;
}
.footer-title {
  font-size: 1.25rem;
  color: var(--color-primary);
}
.footer-social {
  display: flex;
  gap: 1rem;
  margin-left: auto;
}
.footer-social svg {
  width: 24px;
  height: 24px;
  fill: var(--color-text);
  transition: fill var(--transition);
}
.footer-social a:hover svg {
  fill: var(--color-primary);
}
.footer-col h4 {
  color: var(--color-primary);
  margin-bottom: 0.5rem;
}
.footer-col ul {
  list-style: none;
  padding: 0;
  line-height: 1.6;
}
.footer-col ul li + li {
  margin-top: 0.3rem;
}
.footer-col ul li a {
  color: var(--color-text);
  text-decoration: none;
  transition: color var(--transition);
}
.footer-col ul li a:hover {
  color: var(--color-primary);
}
.footer-legal {
  grid-column: 1 / -1;
  font-size: 0.8rem;
  text-align: center;
  margin-top: 1rem;
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 1rem;
}
.footer-legal a {
  color: var(--color-text);
  text-decoration: none;
  margin: 0 0.25rem;
}
.footer-legal a:hover {
  color: var(--color-primary);
}

/* responsive adjustments */
@media (max-width: 768px) {
  .footer-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .footer-legal {
    text-align: center;
  }
}


  </style>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>

<body>

  <!-- HEADER -->
  <header>
    <div class="logo">
      <img src="/assets/cellanova_logo.png" alt="CellaNova Tech"/>
      <h1>CellaNova Tech</h1>
    </div>
    <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
      <svg id="themeIcon"><use xlink:href="#icon-moon"/></svg>
    </button>
  </header>

  <!-- BUILDER -->
  <main>
    <div class="builder-container">
      <div class="builder-header">Resume Builder</div>
      <div class="builder-body">
        <div id="step1" class="step">
          <label>Upload your resume (PDF)</label>
          <input type="file" id="fileInput" accept="application/pdf">
          <div class="actions"><button id="toStep2" disabled>Next</button></div>
        </div>
        <div id="step2" class="step" style="display:none;">
          <label>Job description URL</label>
          <input type="text" id="jobUrl" placeholder="https://example.com/job">
          <div class="actions">
            <button id="back">Back</button>
            <button id="run">Generate</button>
          </div>
        </div>
        <div id="loader" style="display:none; text-align:center;">
          <div class="spinner"></div>
          <div class="status" id="loaderText">Initializing…</div>
        </div>
      </div>
    </div>
  </main>

  <!-- FULL-SCREEN OUTPUT -->
  <section id="markdownOutputWrapper">
    <div class="markdown-toolbar">
      <button id="editBtn">Edit</button>
      <button id="copyBtn">Copy Text</button>
      <button id="downloadPdfBtn">Download PDF</button>
    </div>
    <div id="renderedOutput"></div>
    <textarea id="outputArea" readonly></textarea>
  </section>

  <!-- FOOTER -->
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand-social">
        <img src="/assets/cellanova_logo.png" class="footer-logo" alt="CellaNova Logo"/>
        <span class="footer-title">CellaNova Technologies</span>
        <div class="footer-social">
          <a href="#"><svg><use xlink:href="#icon-linkedin"/></svg></a>
          <a href="#"><svg><use xlink:href="#icon-instagram"/></svg></a>
          <a href="#"><svg><use xlink:href="#icon-twitter"/></svg></a>
        </div>
      </div>
      <div class="footer-col">
        <h4>Solutions</h4>
        <ul><li><a href="how-it-works.html">CustomCore</a></li><li><a href="agents.html">LaunchKit</a></li><li><a href="use-cases.html">PrecisionTasks</a></li></ul>
      </div>
      <div class="footer-col">
        <h4>Resources</h4>
        <ul><li><a href="how-it-works.html">How it Works</a></li><li><a href="agents.html">Agents</a></li><li><a href="use-cases.html">Use Cases</a></li><li><a href="developer-docs.html">Developer Docs</a></li></ul>
      </div>
      <div class="footer-col">
        <h4>Contact</h4>
        <ul><li><a href="mailto:contactcnt@cellanovatech.com">contactcnt@cellanovatech.com</a></li><li>5900 Balcones Dr Ste 100</li><li>Austin, TX 78731-4298</li></ul>
      </div>
      <div class="footer-legal">
        &copy; 2025 CellaNova Technologies — <a href="#">Terms</a> | <a href="#">Privacy</a>
      </div>
    </div>
  </footer>

  <!-- SVG ICONS -->
  <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
    <symbol id="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 0111.21 3 7 7 0 1012 21a9 9 0 009-8.21z"/></symbol>
    <symbol id="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><g stroke="#000" stroke-width="2"><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></g></symbol>
    <symbol id="icon-linkedin" viewBox="0 0 24 24"><path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zm.02 4.5H0V24h5V8zM8 8h4.218v2.234h.059c.587-1.116 2.023-2.234 4.164-2.234C22.49 8 24 10.334 24 14.133V24h-5v-9.867c0-2.351-.042-5.379-3.277-5.379-3.28 0-3.784 2.565-3.784 5.212V24H8V8z"/></symbol>
    <symbol id="icon-instagram" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 1.206.056 1.83.246 2.257.415a4.605 4.605 0 011.675 1.09 4.605 4.605 0 011.09 1.675c.169.427.359 1.051.415 2.257.058 1.266.07 1.645.07 4.85s-.012 3.584-.07 4.85c-.056 1.206-.246 1.83-.415 2.257a4.605 4.605 0 01-1.09 1.675 4.605 4.605 0 01-1.675 1.09c-.427.169-1.051.359-2.257.415-1.266.058-1.645.07-4.85.07s-3.584-.012-4.85-.07c-1.206-.056-1.83-.246-2.257-.415a4.605 4.605 0 01-1.675-1.09 4.605 4.605 0 01-1.09-1.675c-.169-.427-.359-1.051-.415-2.257C2.175 15.747 2.163 15.368 2.163 12s.012-3.584.07-4.85c.056-1.206.246-1.83.415-2.257a4.605 4.605 0 011.09-1.675A4.605 4.605 0 015.342.632C5.769.463 6.393.273 7.599.217 8.865.159 9.245.147 12 .147c2.755 0 3.135.012 4.401.07z"/><circle cx="12" cy="12" r="3.6"/></symbol>
    <symbol id="icon-twitter" viewBox="0 0 24 24"><path d="M23.954 4.569a10 10 0 01-2.825.775 4.932 4.932 0 002.163-2.723 9.864 9.864 0 01-3.127 1.195 4.916 4.916 0 00-8.384 4.482A13.944 13.944 0 01 1.671 3.149a4.902 4.902 0 001.523 6.549 4.903 4.903 0 01-2.229-.616v.061a4.914 4.914 0 003.946 4.809 4.996 4.996 0 01-2.224.084 4.922 4.922 0 004.6 3.417A9.867 9.867 0 010 19.54a13.94 13.94 0 007.548 2.212c9.056 0 14.009-7.496 14.009-13.986 0-.21-.005-.423-.015-.633A10.012 10.012 0 0024 4.59z"/></symbol>
  </svg>

  <script>
  // THEME TOGGLE
  const htmlEl = document.documentElement,
        btn    = document.getElementById('themeToggle'),
        icon   = document.querySelector('#themeIcon use');
  let theme  = localStorage.getItem('theme') || 'dark';
  htmlEl.setAttribute('data-theme', theme);
  icon.setAttribute('xlink:href', theme === 'dark' ? '#icon-moon' : '#icon-sun');
  btn.onclick = () => {
    theme = theme === 'dark' ? 'light' : 'dark';
    htmlEl.setAttribute('data-theme', theme);
    icon.setAttribute('xlink:href', theme === 'dark' ? '#icon-moon' : '#icon-sun');
    localStorage.setItem('theme', theme);
  };

  // BUILDER LOGIC
  const fileInput   = document.getElementById('fileInput'),
        toStep2     = document.getElementById('toStep2'),
        backBtn     = document.getElementById('back'),
        runBtn      = document.getElementById('run'),
        step1       = document.getElementById('step1'),
        step2       = document.getElementById('step2'),
        loader      = document.getElementById('loader'),
        loaderText  = document.getElementById('loaderText'),
        jobUrl      = document.getElementById('jobUrl'),
        builder     = document.querySelector('.builder-container'),
        wrap        = document.getElementById('markdownOutputWrapper'),
        toolbar     = document.querySelector('.markdown-toolbar'),
        rendered    = document.getElementById('renderedOutput'),
        textarea    = document.getElementById('outputArea'),
        editBtn     = document.getElementById('editBtn'),
        copyBtn     = document.getElementById('copyBtn'),
        downloadBtn = document.getElementById('downloadPdfBtn');
  let resumeText = '';

  // Enable Next when a file is selected
  fileInput.onchange = () => toStep2.disabled = !fileInput.files.length;

  // Step 1 → Step 2 (extract PDF)
  toStep2.onclick = async () => {
    const f = fileInput.files[0];
    if (!f) return;
    step1.style.display  = 'none';
    loader.style.display = 'block';
    loaderText.textContent = 'Extracting PDF…';
    const form = new FormData();
    form.append('pdf', f);
    const res = await fetch('/api/extract', { method: 'POST', body: form });
    const j   = await res.json();
    resumeText = j.text || '';
    loader.style.display = 'none';
    step2.style.display  = 'flex';
  };

  // Back button
  backBtn.onclick = () => {
    step2.style.display = 'none';
    step1.style.display = 'flex';
  };

  // Run Crew → show output
  runBtn.onclick = async () => {
    step2.style.display  = 'none';
    loader.style.display = 'block';
    const statuses = ['Analyzing…', 'Rewriting…'];
    let idx = 0;
    const iv = setInterval(() => {
      loaderText.textContent = statuses[idx];
      idx = (idx + 1) % statuses.length;
    }, 800);

    try {
      const resp = await fetch('/api/run', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_text:         resumeText,
          job_description_url: jobUrl.value
        })
      });
      const { output } = await resp.json();
      textarea.value     = output || '';
      rendered.innerHTML = marked.parse(output || '');
    } catch (e) {
      textarea.value    = 'Error: ' + e.message;
      rendered.textContent = textarea.value;
    } finally {
      clearInterval(iv);
      loader.style.display  = 'none';
      builder.style.display = 'none';
      wrap.style.display    = 'block';
      toolbar.style.display = 'flex';
      rendered.style.display = 'block';
      textarea.style.display = 'none';
    }
  };

  // EDIT / VIEW toggle
  editBtn.onclick = () => {
    const isEditing = textarea.style.display === 'block';
    textarea.style.display  = isEditing ? 'none' : 'block';
    rendered.style.display  = isEditing ? 'block' : 'none';
    editBtn.textContent     = isEditing ? 'Edit' : 'View';
  };

  // COPY to clipboard
  copyBtn.onclick = () => {
    const text = (textarea.style.display === 'block')
      ? textarea.value
      : rendered.innerText;
    navigator.clipboard.writeText(text);
  };

  // DOWNLOAD PDF of the polished markdown
  downloadBtn.onclick = async () => {
    const blob = await fetch('/api/download-pdf', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ resume_markdown: textarea.value })
    }).then(r => r.blob());
    const url = URL.createObjectURL(blob);
    const a   = document.createElement('a');
    a.href    = url;
    a.download = 'resume.pdf';
    a.click();
    URL.revokeObjectURL(url);
  };
</script>


</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return HTML_PAGE

@app.route('/api/extract', methods=['POST'])
def extract_pdf():
    f = request.files.get('pdf')
    if not f:
        return jsonify({'text': ''})
    reader = PyPDF2.PdfReader(f)
    text = [p.extract_text() or "" for p in reader.pages]
    return jsonify({'text': "\n".join(text)})

@app.route('/api/run', methods=['POST'])
def api_run():
    data = request.get_json() or {}
    resume_text = data.get('resume_text', '')
    job_url     = data.get('job_description_url', '')
    crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
    result = crew.kickoff(inputs={
        'resume_text': resume_text,
        'job_description_url': job_url
    })
    output = result if isinstance(result, str) else str(result)
    return jsonify({'output': output.strip()})
@app.route("/how-it-works")
def how_it_works():
    return render_template("how-it-works.html")

@app.route("/agents")
def agents():
    return render_template("agents.html")

@app.route("/use-cases")
def use_cases():
    return render_template("use-cases.html")

@app.route("/developer-docs")
def developer_docs():
    return render_template("developer-docs.html")

@app.route('/api/download-pdf', methods=['POST'])
def download_pdf():
    data = request.get_json() or {}
    md = data.get('resume_markdown', '')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=40, rightMargin=40,
                            topMargin=40, bottomMargin=40)

    # grab the base stylesheet
    styles = getSampleStyleSheet()

    # only add our “CustomBullet” if it isn’t already there:
    if 'CustomBullet' not in styles:
        styles.add(ParagraphStyle(
            name='CustomBullet',
            parent=styles['Normal'],
            bulletIndent=0,
            leftIndent=12,
            spaceAfter=6,
            bulletFontName='Helvetica',
            bulletFontSize=10,
        ))

    elements = []
    for line in md.split('\n'):
        stripped = line.lstrip()
        # very naive: if it starts with “- ”, treat as bullet
        if stripped.startswith('- '):
            txt = stripped[2:].strip()
            elements.append(
                ListFlowable(
                    [ListItem(Paragraph(txt, styles['Normal']), bulletText='•')],
                    style=styles['CustomBullet']
                )
            )
        else:
            elements.append(Paragraph(line, styles['Normal']))
        elements.append(Spacer(1,4))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name='resume.pdf'
    )



if __name__ == '__main__':
    app.run(debug=True, port=5000)




