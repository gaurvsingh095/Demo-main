from flask import Flask, request, jsonify
import io
import contextlib
from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew
import PyPDF2

app = Flask(__name__)

# Single-route serving inline HTML with embedded CSS & JS & Markdown support
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>CellaNova Tech • Resume Builder</title>
  <style>
    /* Base palettes & typography */
    :root {
      --color-bg: #121212;
      --color-surface: #0d1b2a;
      --color-text: #E0E0E0;
      --color-muted: #757575;
      --color-primary: #1ABC9C;
      --color-secondary: #FFC107;
      --color-accent: #FF5722;
      --radius: 8px;
      --transition: 0.3s;
      --font-stack: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      --footer-height: 320px;
    }
    html[data-theme="light"] {
      --color-bg: #f4f7fa;
      --color-surface: #ffffff;
      --color-text: #333333;
      --color-muted: #888888;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      height: 100%;
      background: var(--color-bg);
      color: var(--color-text);
      font-family: var(--font-stack);
      transition: background var(--transition), color var(--transition);
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--color-bg); }
    ::-webkit-scrollbar-thumb {
      background: #111; border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover { background: #333; }
    body { display: flex; flex-direction: column; min-height: 100vh; }

    /* Header */
    header {
      background: var(--color-surface);
      padding: 1rem 2rem;
      display: flex; align-items: center; justify-content: space-between;
      box-shadow: 0 2px 4px rgba(0,0,0,0.7);
    }
    .logo { display: flex; align-items: center; }
    .logo img { height: 36px; margin-right: .75rem; }
    .logo h1 {
      font-size: 1.25rem; letter-spacing: .05em;
      color: var(--color-text);
    }

    /* Main builder */
    main {
      flex: 1;
      display: flex; align-items: flex-start; justify-content: center;
      padding: 6rem 2rem 2rem;
      padding-bottom: calc(var(--footer-height) + 2rem);
    }
    .builder-container {
      background: var(--color-surface);
      border-radius: var(--radius);
      box-shadow: 0 8px 24px rgba(0,0,0,0.7);
      width: 100%; max-width: 1000px; overflow: visible;
      height: auto;   
      animation: fadeInUp .6s ease-out;
    }
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px) }
      to   { opacity: 1; transform: translateY(0) }
    }
    .builder-header {
      background: var(--color-primary);
      padding: 1rem; text-align: center;
      cursor: pointer; color: var(--color-surface);
    }
    .builder-body {
      padding: 1.5rem;
      display: flex; flex-direction: column; gap: 1.5rem;
    }

    /* Two-step inputs */
    .step { display: flex; flex-direction: column; gap: .5rem; }
    label { color: var(--color-muted); font-size: .95rem; }
    input[type="file"], input[type="text"] {
      width: 100%; padding: .75rem;
      border: none; border-radius: var(--radius);
      background: #222; color: var(--color-text);
      transition: background var(--transition), transform var(--transition);
    }
    input:focus { outline: 2px solid var(--color-accent); background: #333; transform: scale(1.02); }

    .actions {
      display: flex; justify-content: flex-end; gap: .5rem;
    }
    button {
      padding: .6rem 1.2rem;
      background: var(--color-accent);
      color: var(--color-surface);
      border: none; border-radius: var(--radius);
      font-weight: 600; cursor: pointer;
      transition: background var(--transition), transform var(--transition);
    }
    button:disabled {
      background: var(--color-muted); opacity: .6;
      cursor: not-allowed;
    }
    button:hover:not(:disabled) {
      background: var(--color-secondary);
      transform: translateY(-2px) scale(1.03);
    }

    /* Spinner & status */
    .spinner {
      width: 48px; height: 48px;
      border: 6px solid var(--color-muted);
      border-top: 6px solid var(--color-accent);
      border-radius: 50%;
      animation: spin .8s linear infinite;
      margin: 1.5rem auto;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .status { text-align: center; font-style: italic; color: var(--color-muted); }

    /* Markdown output */
    .output {
      background: var(--color-surface); padding: 1rem;
      border-radius: var(--radius); font-family: monospace;
      font-size: .9rem; max-height: 400px; overflow-y: auto;
      display: none; white-space: pre-wrap;
      animation: fadeInUp .6s ease-out;
    }

    /* Footer (unchanged) */
    footer.site-footer { /* … your existing footer styles … */ }
  </style>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>

<body>
  <header>
    <div class="logo">
      <img src="../assets/cellanova_logo.png" alt="CellaNova Tech" />
      <h1>CellaNova Tech</h1>
    </div>
  </header>

  <main>
    <div class="builder-container">
      <div class="builder-header"><h2>Resume Builder</h2></div>
      <div class="builder-body">
        <!-- Step 1: PDF upload -->
        <div id="step1" class="step">
          <label for="fileInput">Upload your resume (PDF)</label>
          <input type="file" id="fileInput" accept="application/pdf" />
          <div class="actions">
            <button id="toStep2" disabled>Next</button>
          </div>
        </div>

        <!-- Step 2: Job URL -->
        <div id="step2" class="step" style="display:none;">
          <label for="jobUrl">Job description URL</label>
          <input type="text" id="jobUrl" placeholder="https://..." />
          <div class="actions">
            <button id="back">Back</button>
            <button id="run">Generate</button>
          </div>
        </div>

        <!-- Loading -->
        <div id="loader" style="display:none; text-align:center;">
          <div class="spinner"></div>
          <div class="status" id="loaderText">Initializing…</div>
        </div>

        <!-- Output -->
        <div id="result" class="output"></div>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="site-footer">
    <!-- … your existing footer markup … -->
  </footer>

  <script>
    // Simplified two-step logic
    const fileInput = document.getElementById('fileInput');
    const toStep2   = document.getElementById('toStep2');
    const backBtn   = document.getElementById('back');
    const runBtn    = document.getElementById('run');
    const step1     = document.getElementById('step1');
    const step2     = document.getElementById('step2');
    const loader    = document.getElementById('loader');
    const loaderText= document.getElementById('loaderText');
    const resultBox = document.getElementById('result');
    let resumeText  = '';

    fileInput.onchange = () => {
      toStep2.disabled = !fileInput.files.length;
    };

    toStep2.onclick = async () => {
      const f = fileInput.files[0];
      if (!f) return;
      step1.style.display = 'none';
      loader.style.display = 'block';
      loaderText.textContent = 'Extracting PDF…';
      const form = new FormData();
      form.append('pdf', f);
      const res = await fetch('/api/extract', { method:'POST', body: form });
      const { text } = await res.json();
      resumeText = text || '';
      loader.style.display = 'none';
      step2.style.display = 'flex';
    };

    backBtn.onclick = () => {
      step2.style.display = 'none';
      step1.style.display = 'flex';
    };

    runBtn.onclick = async () => {
      step2.style.display = 'none';
      loader.style.display = 'block';
      const statuses = ['Analyzing…','Rewriting…'];
      let idx = 0;
      const iv = setInterval(() => {
        loaderText.textContent = statuses[idx];
        idx = (idx+1) % statuses.length;
      }, 1200);

      try {
        const res = await fetch('/api/run', {
          method: 'POST',
          headers:{ 'Content-Type':'application/json' },
          body: JSON.stringify({
            resume_text: resumeText,
            job_url: document.getElementById('jobUrl').value
          })
        });
        const { output } = await res.json();
        resultBox.innerHTML = marked.parse(output || '');
      } catch(e) {
        resultBox.textContent = 'Error: '+ e.message;
      } finally {
        clearInterval(iv);
        loader.style.display = 'none';
        resultBox.style.display = 'block';
      }
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
    file = request.files.get('pdf')
    if not file:
        return jsonify({'text': ''})
    reader = PyPDF2.PdfReader(file)
    text = []
    for page in reader.pages:
        text.append(page.extract_text() or '')
    return jsonify({'text': '\n'.join(text)})

@app.route('/api/run', methods=['POST'])
@app.route('/api/run', methods=['POST'])
def api_run_crew():
    data = request.get_json() or {}
    resume_text = data.get('resume_text', '')
    job_url = data.get('job_url', '')
    crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()

    # Execute crew and normalize output
    result = crew.kickoff(inputs={'resume_text': resume_text, 'job_description_url': job_url})
    if isinstance(result, str): 
        output = result
    else:
        output = str(result)

    return jsonify({'output': output.strip()})

if __name__ == '__main__':
    app.run(debug=True, port=5000)(debug=True, port=5000)
# from flask import Flask, request, jsonify
# import PyPDF2
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(__name__)

# # Single‐route serving inline HTML with embedded CSS & JS & Markdown support
# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang="en" data-theme="dark">
# <head>
#   <meta charset="UTF-8" />
#   <meta name="viewport" content="width=device-width,initial-scale=1" />
#   <title>CellaNova Tech • Resume Builder</title>
#   <style>
#     /* Base palettes & typography */
#     :root {
#       --color-bg: #121212;
#       --color-surface: #0d1b2a;
#       --color-text: #E0E0E0;
#       --color-muted: #757575;
#       --color-primary: #1ABC9C;
#       --color-secondary: #FFC107;
#       --color-accent: #FF5722;
#       --radius: 8px;
#       --transition: 0.3s;
#       --font-stack: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
#       --footer-height: 320px;
#     }
#     html[data-theme="light"] {
#       --color-bg: #f4f7fa;
#       --color-surface: #ffffff;
#       --color-text: #333333;
#       --color-muted: #888888;
#     }
#     *, *::before, *::after { box-sizing: border-box; margin:0; padding:0; }
#     html, body {
#       height:100%; background:var(--color-bg); color:var(--color-text);
#       font-family:var(--font-stack); transition:background var(--transition),color var(--transition);
#     }
#     ::-webkit-scrollbar { width:8px; }
#     ::-webkit-scrollbar-track { background:var(--color-bg); }
#     ::-webkit-scrollbar-thumb { background:#111; border-radius:4px; }
#     ::-webkit-scrollbar-thumb:hover { background:#333; }
#     body { display:flex; flex-direction:column; min-height:100vh; }

#     /* Header */
#     header {
#       background:var(--color-surface); padding:1rem 2rem;
#       display:flex; align-items:center; justify-content:space-between;
#       box-shadow:0 2px 4px rgba(0,0,0,0.7);
#     }
#     .logo { display:flex; align-items:center; }
#     .logo img { height:36px; margin-right:.75rem; }
#     .logo h1 {
#       font-size:1.25rem; letter-spacing:.05em;
#       color:var(--color-text);
#     }

#     /* Main builder */
#     main {
#       flex:1; display:flex; align-items:flex-start; justify-content:center;
#       padding:6rem 2rem 2rem; padding-bottom:calc(var(--footer-height)+2rem);
#     }
#     .builder-container {
#       background:var(--color-surface); border-radius:var(--radius);
#       box-shadow:0 8px 24px rgba(0,0,0,0.7);
#       width:100%; max-width:1000px; overflow:visible; height:auto;
#       animation:fadeInUp .6s ease-out;
#     }
#     @keyframes fadeInUp {
#       from { opacity:0; transform:translateY(20px); }
#       to   { opacity:1; transform:translateY(0);    }
#     }
#     .builder-header {
#       background:var(--color-primary); padding:1rem; text-align:center;
#       cursor:pointer; color:var(--color-surface);
#     }
#     .builder-body {
#       padding:1.5rem; display:flex; flex-direction:column; gap:1.5rem;
#     }

#     /* Two‐step inputs */
#     .step { display:flex; flex-direction:column; gap:.5rem; }
#     label { color:var(--color-muted); font-size:.95rem; }
#     input[type="file"], input[type="text"] {
#       width:100%; padding:.75rem; border:none; border-radius:var(--radius);
#       background:#222; color:var(--color-text);
#       transition:background var(--transition),transform var(--transition);
#     }
#     input:focus {
#       outline:2px solid var(--color-accent); background:#333; transform:scale(1.02);
#     }
#     .actions { display:flex; justify-content:flex-end; gap:.5rem; }
#     button {
#       padding:.6rem 1.2rem; background:var(--color-accent);
#       color:var(--color-surface); border:none; border-radius:var(--radius);
#       font-weight:600; cursor:pointer;
#       transition:background var(--transition),transform var(--transition);
#     }
#     button:disabled {
#       background:var(--color-muted); opacity:.6; cursor:not-allowed;
#     }
#     button:hover:not(:disabled) {
#       background:var(--color-secondary);
#       transform:translateY(-2px) scale(1.03);
#     }

#     /* Spinner & status */
#     .spinner {
#       width:48px; height:48px; border:6px solid var(--color-muted);
#       border-top:6px solid var(--color-accent); border-radius:50%;
#       animation:spin .8s linear infinite; margin:1.5rem auto;
#     }
#     @keyframes spin { to { transform:rotate(360deg); } }
#     .status { text-align:center; font-style:italic; color:var(--color-muted); }

#     /* Markdown output */
#     .output {
#       background:var(--color-surface); padding:1rem; border-radius:var(--radius);
#       font-family:monospace; font-size:.9rem; max-height:400px; overflow-y:auto;
#       display:none; white-space:pre-wrap; animation:fadeInUp .6s ease-out;
#     }

#     /* Footer (your existing footer styles) */
#     footer.site-footer { /* … */ }
#   </style>
#   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
# </head>

# <body>
#   <header>
#     <div class="logo">
#       <img src="../assets/cellanova_logo.png" alt="CellaNova Tech" />
#       <h1>CellaNova Tech</h1>
#     </div>
#   </header>

#   <main>
#     <div class="builder-container">
#       <div class="builder-header">
#         <h2>Resume Builder</h2>
#       </div>
#       <div class="builder-body">
#         <!-- Step 1 -->
#         <div id="step1" class="step">
#           <label for="resume_pdf">Upload your resume PDF:</label>
#           <input type="file" id="resume_pdf" accept="application/pdf" />
#           <button id="toStep2" disabled>Next Step</button>
#         </div>

#         <!-- Step 2 -->
#         <div id="step2" class="step" style="display:none;">
#           <label for="job_url">Job description URL:</label>
#           <input type="text" id="job_url" placeholder="https://..." />
#           <div class="actions">
#             <button id="toStep1">Back</button>
#             <button id="submitBtn">Submit</button>
#           </div>
#         </div>

#         <!-- Loading -->
#         <div id="loadingBox" style="display:none; text-align:center;">
#           <div class="spinner"></div>
#           <div class="status" id="statusText">Initializing...</div>
#         </div>

#         <!-- Markdown Output -->
#        <div class="output" id="output">
#   <div class="actions" style="justify-content: flex-start; gap:1rem;">
#     <button id="editBtn">🔧 Edit</button>
#     <button id="copyBtn">📋 Copy Markdown</button>
#   </div>
#   <textarea id="markdownEditor" style="
#     flex:1;
#     width:100%;
#     padding:1rem;
#     background:var(--color-surface);
#     color:var(--color-text);
#     border:none;
#     resize:none;
#     font-family:monospace;
#     font-size:.9rem;
#   " readonly></textarea>
# </div>

#       </div>
#     </div>
#   </main>

#   <footer class="site-footer">
#     <!-- … your existing footer markup … -->
#   </footer>

#   <script>
#     const steps        = { step1: document.getElementById('step1'), step2: document.getElementById('step2') };
#     const resumePdf    = document.getElementById('resume_pdf');
#     const toStep2      = document.getElementById('toStep2');
#     const toStep1      = document.getElementById('toStep1');
#     const submitBtn    = document.getElementById('submitBtn');
#     const loadingBox   = document.getElementById('loadingBox');
#     const statusText   = document.getElementById('statusText');
#     const outputDiv    = document.getElementById('output');
#     const outputMarkdown = document.getElementById('outputMarkdown');
#     let extractedText = '';

#     // Enable “Next” when a file is selected
#     resumePdf.onchange = () => {
#       toStep2.disabled = !resumePdf.files.length;
#     };

#     // Step 1 → Step 2
#     toStep2.onclick = async () => {
#       const file = resumePdf.files[0];
#       if (!file) return;
#       loadingBox.style.display = 'block';
#       statusText.textContent = 'Extracting PDF text...';
#       const form = new FormData();
#       form.append('pdf', file);
#       const resp = await fetch('/api/extract', { method:'POST', body: form });
#       const j = await resp.json();
#       extractedText = j.text || '';
#       loadingBox.style.display = 'none';
#       steps.step1.style.display = 'none';
#       steps.step2.style.display = 'block';
#     };

#     // Back button
#     toStep1.onclick = () => {
#       steps.step2.style.display = 'none';
#       steps.step1.style.display = 'block';
#     };

#     // Submit → run AI crew
#     submitBtn.onclick = async () => {
#       steps.step2.style.display = 'none';
#       loadingBox.style.display = 'block';
#       outputDiv.style.display = 'none';

#       // spinner statuses
#       const statuses = ['Analyzing Job Description...', 'Crafting Your Resume...'];
#       let idx = 0;
#       statusText.textContent = statuses[idx];
#       const interval = setInterval(() => {
#         idx = (idx+1) % statuses.length;
#         statusText.textContent = statuses[idx];
#       }, 1500);

#       try {
#         const res = await fetch('/api/run', {
#           method: 'POST',
#           headers: { 'Content-Type': 'application/json' },
#           body: JSON.stringify({
#             resume_text: extractedText,
#             job_url: document.getElementById('job_url').value
#           })
#         });
#         const data = await res.json();
#         outputMarkdown.innerHTML = marked.parse(data.output || '');
#       } catch(err) {
#         outputMarkdown.textContent = 'Error: ' + err;
#       } finally {
#         clearInterval(interval);
#         loadingBox.style.display = 'none';
#         outputDiv.style.display = 'block';
#       }
#     };
#     // AFTER you set `outputMarkdown.innerHTML = marked.parse(output)`:
# const editor = document.getElementById('markdownEditor');
# const copyBtn = document.getElementById('copyBtn');
# const editBtn = document.getElementById('editBtn');

# function showMarkdown(md) {
#   editor.value = md;
#   editor.readOnly = true;
#   editor.style.display = 'block';
# }

# copyBtn.onclick = () => {
#   navigator.clipboard.writeText(editor.value)
#     .then(() => alert('Markdown copied!'))
#     .catch(() => alert('Copy failed.'));
# };

# editBtn.onclick = () => {
#   editor.readOnly = !editor.readOnly;
#   editBtn.textContent = editor.readOnly ? '🔧 Edit' : '✅ Save';
#   if (editor.readOnly) {
#     // optionally re-render the preview if you keep a preview div too
#   }
# };

# // When you get your AI result:
# submitBtn.onclick = async () => {
#   /* … your existing code … */
#   // once you have `data.output`:
#   showMarkdown(data.output || '');
#   /* … */
# };

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
#     pages = [page.extract_text() or '' for page in reader.pages]
#     return jsonify({'text': '\n'.join(pages)})

# @app.route('/api/run', methods=['POST'])
# def api_run_crew():
#     data = request.get_json() or {}
#     resume_text = data.get('resume_text', '')
#     job_url     = data.get('job_url', '')
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#     result = crew.kickoff(inputs={
#       'resume_text': resume_text,
#       'job_description_url': job_url
#     })
#     output = result if isinstance(result, str) else str(result)
#     return jsonify({'output': output.strip()})

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
# from flask import Flask, request, jsonify
# import PyPDF2

# app = Flask(__name__)

# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang="en" data-theme="dark">
# <head>
#   <meta charset="UTF-8" />
#   <meta name="viewport" content="width=device-width,initial-scale=1" />
#   <title>CellaNova Tech • Resume Builder</title>
#   <style>
#     /* Base palettes & typography */
#     :root {
#       --color-bg: #121212;
#       --color-surface: #0d1b2a;
#       --color-text: #E0E0E0;
#       --color-muted: #757575;
#       --color-primary: #1ABC9C;
#       --color-secondary: #FFC107;
#       --color-accent: #FF5722;
#       --radius: 8px;
#       --transition: 0.3s;
#       --font-stack: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
#       --footer-height: 320px;
#     }
#     html[data-theme="light"] {
#       --color-bg: #f4f7fa;
#       --color-surface: #ffffff;
#       --color-text: #333333;
#       --color-muted: #888888;
#     }
#     *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
#     html, body {
#       height: 100%;
#       background: var(--color-bg);
#       color: var(--color-text);
#       font-family: var(--font-stack);
#       overflow: hidden;
#       transition: background var(--transition), color var(--transition);
#     }

#     /* Header */
#     header {
#       background: var(--color-surface);
#       padding: 1rem 2rem;
#       display: flex; align-items: center;
#       box-shadow: 0 2px 4px rgba(0,0,0,0.7);
#     }
#     .logo { display: flex; align-items: center; }
#     .logo img { height: 36px; margin-right: .75rem; }
#     .logo h1 {
#       font-size: 1.25rem; letter-spacing: .05em;
#       color: var(--color-text);
#     }

#     /* Full‐screen builder */
#     main {
#       flex: 1;
#       position: absolute;
#       top: 3.5rem; /* header height */
#       left: 0; right: 0; bottom: 0;
#     }
#     .builder-container {
#       background: var(--color-surface);
#       width: 100vw; height: calc(100vh - 3.5rem);
#       border-radius: 0;
#       box-shadow: none;
#       display: flex; flex-direction: column;
#     }
#     .builder-header {
#       background: var(--color-primary);
#       padding: 1rem; text-align: center;
#       color: var(--color-surface);
#       font-size: 1.5rem;
#     }
#     .builder-body {
#       flex: 1;
#       display: flex; flex-direction: column;
#       padding: 1rem;
#       overflow: hidden;
#     }

#     /* Steps */
#     .step { margin-bottom: 1rem; }
#     label { display: block; color: var(--color-muted); margin-bottom: .5rem; }
#     input[type="file"], input[type="text"] {
#       width: 100%; padding: .75rem;
#       border: none; border-radius: var(--radius);
#       background: #222; color: var(--color-text);
#       transition: background var(--transition), transform var(--transition);
#     }
#     input:focus { outline: 2px solid var(--color-accent); background: #333; }

#     .actions { text-align: right; margin-top: .5rem; }
#     .actions button {
#       padding: .6rem 1.2rem; margin-left: .5rem;
#       background: var(--color-accent); color: var(--color-surface);
#       border: none; border-radius: var(--radius);
#       cursor: pointer; transition: background var(--transition);
#     }
#     .actions button:disabled {
#       background: var(--color-muted); cursor: not-allowed;
#     }
#     .actions button:hover:not(:disabled) {
#       background: var(--color-secondary);
#     }

#     /* Loader */
#     .spinner {
#       width: 48px; height: 48px;
#       border: 6px solid var(--color-muted);
#       border-top: 6px solid var(--color-accent);
#       border-radius: 50%;
#       animation: spin .8s linear infinite;
#       margin: 2rem auto;
#     }
#     @keyframes spin { to { transform: rotate(360deg); } }
#     .status { text-align: center; color: var(--color-muted); }

#     /* Markdown editor */
#     .output {
#       flex: 1; display: none; flex-direction: column;
#       background: var(--color-surface); padding: 1rem;
#     }
#     #markdownEditor {
#       flex: 1; width: 100%; padding: 1rem;
#       background: var(--color-surface);
#       color: var(--color-text);
#       border: 1px solid #444;
#       border-radius: var(--radius);
#       font-family: monospace; font-size: .9rem;
#       resize: none; overflow: auto;
#     }

#     /* Footer */
#     footer.site-footer {
#       position: absolute; bottom: 0; left: 0; right: 0;
#       background: var(--color-surface); color: var(--color-muted);
#       padding: 1rem; text-align: center;
#       font-size: .8rem;
#     }
#   </style>
#   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
# </head>
# <body>
#   <header>
#     <div class="logo">
#       <img src="../assets/cellanova_logo.png" alt="CellaNova Tech" />
#       <h1>CellaNova Tech</h1>
#     </div>
#   </header>

#   <main>
#     <div class="builder-container">
#       <div class="builder-header">Resume Builder</div>
#       <div class="builder-body">

#         <!-- Step 1 -->
#         <div id="step1" class="step">
#           <label for="fileInput">Upload your resume (PDF)</label>
#           <input type="file" id="fileInput" accept="application/pdf" />
#           <div class="actions">
#             <button id="toStep2" disabled>Next</button>
#           </div>
#         </div>

#         <!-- Step 2 -->
#         <div id="step2" class="step" style="display:none;">
#           <label for="jobUrl">Job description URL</label>
#           <input type="text" id="jobUrl" placeholder="https://..." />
#           <div class="actions">
#             <button id="back">Back</button>
#             <button id="run">Generate</button>
#           </div>
#         </div>

#         <!-- Loader -->
#         <div id="loader" style="display:none;">
#           <div class="spinner"></div>
#           <div class="status" id="loaderText">Initializing…</div>
#         </div>

#         <!-- Output / Markdown Editor -->
#         <div id="output" class="output">
#           <div class="actions" style="justify-content: flex-start;">
#             <button id="editBtn">🔧 Edit</button>
#             <button id="copyBtn">📋 Copy Markdown</button>
#           </div>
#           <textarea id="markdownEditor" readonly></textarea>
#         </div>

#       </div>
#     </div>
#   </main>

#   <footer class="site-footer">
#     &copy; 2025 CellaNova Technologies — <a href="#" style="color:inherit;">Terms</a> | <a href="#" style="color:inherit;">Privacy</a>
#   </footer>

#   <script>
#     // Steps & PDF extraction
#     const fileInput = document.getElementById('fileInput');
#     const toStep2   = document.getElementById('toStep2');
#     const backBtn   = document.getElementById('back');
#     const runBtn    = document.getElementById('run');
#     const step1     = document.getElementById('step1');
#     const step2     = document.getElementById('step2');
#     const loader    = document.getElementById('loader');
#     const loaderText= document.getElementById('loaderText');
#     const outputDiv = document.getElementById('output');
#     const editor    = document.getElementById('markdownEditor');
#     const copyBtn   = document.getElementById('copyBtn');
#     const editBtn   = document.getElementById('editBtn');

#     let resumeText = '';

#     fileInput.onchange = () => {
#       toStep2.disabled = !fileInput.files.length;
#     };

#     toStep2.onclick = async () => {
#       const f = fileInput.files[0];
#       step1.style.display = 'none';
#       loader.style.display = 'block';
#       loaderText.textContent = 'Extracting PDF…';
#       const form = new FormData();
#       form.append('pdf', f);
#       const res = await fetch('/api/extract', { method:'POST', body: form });
#       const { text } = await res.json();
#       resumeText = text || '';
#       loader.style.display = 'none';
#       step2.style.display = 'block';
#     };

#     backBtn.onclick = () => {
#       step2.style.display = 'none';
#       step1.style.display = 'block';
#     };

#     runBtn.onclick = async () => {
#       step2.style.display = 'none';
#       loader.style.display = 'block';
#       let idx = 0;
#       const statuses = ['Analyzing…','Rewriting…'];
#       const iv = setInterval(() => {
#         loaderText.textContent = statuses[idx];
#         idx = (idx+1) % statuses.length;
#       }, 1200);

#       try {
#         const res = await fetch('/api/run', {
#           method:'POST',
#           headers:{ 'Content-Type':'application/json' },
#           body: JSON.stringify({
#             resume_text: resumeText,
#             job_url: document.getElementById('jobUrl').value
#           })
#         });
#         const { output } = await res.json();
#         editor.value = output || '';
#         editor.readOnly = true;
#         outputDiv.style.display = 'flex';
#       } catch(e) {
#         editor.value = 'Error: ' + e.message;
#         outputDiv.style.display = 'flex';
#       } finally {
#         clearInterval(iv);
#         loader.style.display = 'none';
#       }
#     };

#     // Copy & Edit
#     copyBtn.onclick = () => {
#       navigator.clipboard.writeText(editor.value)
#         .then(() => alert('Markdown copied!'))
#         .catch(() => alert('Copy failed.'));
#     };

#     editBtn.onclick = () => {
#       editor.readOnly = !editor.readOnly;
#       editBtn.textContent = editor.readOnly ? '🔧 Edit' : '✅ Save';
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
#     pages = [p.extract_text() or '' for p in reader.pages]
#     return jsonify({'text': "\n".join(pages)})

# @app.route('/api/run', methods=['POST'])
# def api_run_crew():
#     data       = request.get_json() or {}
#     resume_txt = data.get('resume_text', '')
#     job_url    = data.get('job_url', '')

#     from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#     result = crew.kickoff(inputs={
#       'resume_text': resume_txt,
#       'job_description_url': job_url
#     })

#     output = result if isinstance(result, str) else str(result)
#     return jsonify({'output': output.strip()})

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
# from flask import Flask, render_template, request, jsonify
# import PyPDF2
# import requests
# from bs4 import BeautifulSoup
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(
#     __name__,
#     static_folder="assets",
#     static_url_path="/assets",
#     template_folder="templates"
# )

# def fetch_and_extract_text(url: str) -> str:
#     """Fetch a URL and pull out all its visible text."""
#     resp = requests.get(url, timeout=10)
#     resp.raise_for_status()
#     soup = BeautifulSoup(resp.text, "html.parser")
#     return " ".join(soup.stripped_strings)

# @app.route("/", methods=["GET"])
# def index():
#     return render_template("index.html")

# @app.route("/how-it-works")
# def how_it_works():
#     return render_template("how-it-works.html")

# @app.route("/agents")
# def agents():
#     return render_template("agents.html")

# @app.route("/use-cases")
# def use_cases():
#     return render_template("use-cases.html")

# @app.route("/developer-docs")
# def developer_docs():
#     return render_template("developer-docs.html")

# @app.route("/terms")
# def terms():
#     return render_template("terms.html")

# @app.route("/privacy")
# def privacy():
#     return render_template("privacy.html")

# @app.route("/api/extract", methods=["POST"])
# def extract_pdf():
#     f = request.files.get("pdf")
#     if not f:
#         return jsonify({"text": ""})
#     reader = PyPDF2.PdfReader(f)
#     pages = [p.extract_text() or "" for p in reader.pages]
#     return jsonify({"text": "\n".join(pages)})

# @app.route("/api/run", methods=["POST"])
# def api_run():
#     data = request.get_json() or {}
#     resume_text = data.get("resume_text", "")
#     job_url     = data.get("job_description_url", "")
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()

#     try:
#         result = crew.kickoff(inputs={
#             "resume_text": resume_text,
#             "job_description_url": job_url
#         })
#         output = result if isinstance(result, str) else str(result)
#     except Exception as e:
#         # catch interpolation KeyErrors or LLM errors
#         output = f"Error: {e}"

#     return jsonify({"output": output.strip()})

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
# app.py
# from flask import Flask, render_template_string, request, jsonify
# import PyPDF2
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(__name__,
#             static_folder="assets",
#             static_url_path="/assets"
# )

# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang="en" data-theme="dark">
# <head>
#   <meta charset="UTF-8">
#   <meta name="viewport" content="width=device-width,initial-scale=1">
#   <title>CellaNova Tech • Resume Builder</title>
#   <style>
#     /* ─── PALETTE & TYPO ───────────────────────────────────────────────── */
#     :root {
#       --color-bg: #121212; --color-surface: #0d1b2a;
#       --color-text: #E0E0E0; --color-muted: #757575;
#       --color-primary: #1ABC9C; --color-secondary: #FFC107;
#       --color-accent: #FF5722; --radius: 8px;
#       --transition: 0.3s; --font-stack: "Inter",sans-serif;
#       --footer-height: 320px;
#     }
#     html[data-theme="light"] {
#       --color-bg:#f4f7fa; --color-surface:#fff;
#       --color-text:#333; --color-muted:#888;
#     }
#     *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
#     body {
#       background:var(--color-bg); color:var(--color-text);
#       font-family:var(--font-stack); display:flex;
#       flex-direction:column; min-height:100vh;
#       transition:background var(--transition),color var(--transition);
#     }
#     ::-webkit-scrollbar{width:8px;}
#     ::-webkit-scrollbar-track{background:var(--color-bg);}
#     ::-webkit-scrollbar-thumb{background:#111;border-radius:4px;}
#     ::-webkit-scrollbar-thumb:hover{background:#333;}

#     /* ─── HEADER ───────────────────────────────────────────────────────── */
#     header {
#       background:var(--color-surface); padding:1rem 2rem;
#       display:flex; align-items:center; justify-content:space-between;
#       box-shadow:0 2px 4px rgba(0,0,0,0.7);
#     }
#     .logo{display:flex;align-items:center;}
#     .logo img{height:36px;margin-right:.75rem;}
#     .logo h1{
#       font-size:1.25rem; text-transform:uppercase;
#       letter-spacing:.05em; color:var(--color-text);
#     }
#     .theme-toggle{
#       background:none;border:none;cursor:pointer;
#       padding:.5rem;border-radius:var(--radius);
#       transition:background var(--transition);
#     }
#     .theme-toggle:hover{background:rgba(255,255,255,0.1);}
#     .theme-toggle svg{
#       width:24px;height:24px;fill:var(--color-text);
#       transition:fill var(--transition);
#     }

#     /* ─── BUILDER CARD ─────────────────────────────────────────────────── */
#     main {
#       flex:1; display:flex; align-items:flex-start;
#       justify-content:center;
#       padding:6rem 2rem 2rem; padding-bottom: calc(var(--footer-height)+2rem);
#     }
#     .builder-container {
#       background:var(--color-surface); border-radius:var(--radius);
#       box-shadow:0 8px 24px rgba(0,0,0,0.7);
#       max-width:600px; width:100%; overflow:hidden;
#       animation:fadeInUp .6s ease-out;
#     }
#     @keyframes fadeInUp{
#       from{opacity:0;transform:translateY(20px);}
#       to{opacity:1;transform:translateY(0);}
#     }
#     .builder-header{
#       background:var(--color-primary); padding:1rem;
#       text-align:center; cursor:pointer;
#       transition:background var(--transition);
#     }
#     .builder-header:hover{background:var(--color-secondary);}
#     .builder-header h2{margin:0;color:var(--color-surface);font-size:1.5rem;}
#     .builder-body{
#       padding:1.5rem; display:flex;
#       flex-direction:column; gap:1.5rem;
#     }
#     .step{display:flex;flex-direction:column;gap:.5rem;}
#     label{color:var(--color-muted);}
#     input[type="file"],input[type="text"]{
#       width:100%;padding:.75rem;border:none;
#       border-radius:var(--radius);
#       background:#222;color:var(--color-text);
#       transition:background var(--transition),transform var(--transition);
#     }
#     input:focus{
#       outline:2px solid var(--color-accent);
#       background:#333;transform:scale(1.02);
#     }
#     .actions{display:flex;justify-content:flex-end;gap:.5rem;}
#     .actions button{
#       padding:.6rem 1.2rem; background:var(--color-accent);
#       color:var(--color-surface); border:none;
#       border-radius:var(--radius); cursor:pointer;
#       transition:background var(--transition),transform var(--transition);
#     }
#     .actions button:disabled{
#       background:var(--color-muted);opacity:.6;cursor:not-allowed;
#     }
#     .actions button:hover:not(:disabled){
#       background:var(--color-secondary);
#       transform:translateY(-2px) scale(1.03);
#     }

#     /* ─── LOADER ───────────────────────────────────────────────────────── */
#     .spinner{
#       width:48px;height:48px;
#       border:6px solid var(--color-muted);
#       border-top:6px solid var(--color-accent);
#       border-radius:50%;animation:spin .8s linear infinite;
#       margin:1.5rem auto;
#     }
#     @keyframes spin{to{transform:rotate(360deg);}}
#     .status{text-align:center;font-style:italic;color:var(--color-muted);}

#     /* ─── FULLSCREEN MARKDOWN OUTPUT ────────────────────────────────────── */
#     #markdownOutputWrapper{
#       width:100vw; padding:1rem;
#       background:var(--color-surface);
#       box-sizing:border-box;
#     }
#     .markdown-toolbar{
#       display:flex;justify-content:flex-end;gap:.5rem;
#       margin-bottom:.5rem;
#     }
#     .markdown-toolbar button{
#       background:var(--color-accent);
#       color:var(--color-surface);
#       border:none;padding:.5rem 1rem;
#       border-radius:var(--radius);
#       cursor:pointer;transition:background var(--transition);
#     }
#     .markdown-toolbar button:hover{background:var(--color-secondary);}
#     #outputArea{
#       width:100%; height:calc(100vh - 240px);
#       background:var(--color-bg); color:var(--color-text);
#       border:1px solid var(--color-muted);
#       border-radius:var(--radius);
#       padding:1rem; font-family:monospace;
#       font-size:.95rem; resize:vertical;
#       white-space:pre-wrap; overflow-y:auto;
#     }

#     /* ─── FOOTER ───────────────────────────────────────────────────────── */
#     footer.site-footer{
#       background:#0d1b2a; color:#ddd;
#       padding:3rem 1rem 1rem;
#     }
#     .footer-inner{
#       max-width:1200px; margin:0 auto;
#       display:flex;flex-direction:column;
#       gap:2rem;align-items:center;
#     }
#     .footer-brand-social{text-align:center;}
#     .footer-logo{width:40px;height:40px;vertical-align:middle;}
#     .footer-title{
#       font-size:1.25rem;font-weight:700;
#       margin-left:.5rem;color:var(--color-primary);
#       vertical-align:middle;
#     }
#     .footer-social{
#       margin-top:1rem;display:flex;gap:1rem;justify-content:center;
#     }
#     .footer-social svg{
#       width:24px;height:24px;fill:#ddd;
#       transition:fill var(--transition);
#     }
#     .footer-social a:hover svg{fill:var(--color-primary);}
#     .footer-col{text-align:center;}
#     .footer-col h4{
#       color:var(--color-primary);margin-bottom:.75rem;
#     }
#     .footer-col ul{
#       list-style:none;padding:0;line-height:1.6;
#     }
#     .footer-col ul li+li{margin-top:.5rem;}
#     .footer-col ul li a{
#       color:#eee;text-decoration:none;
#       transition:color var(--transition);
#     }
#     .footer-col ul li a:hover{color:var(--color-primary);}
#     .footer-legal{
#       font-size:.8rem;text-align:center;
#       margin-top:2rem;border-top:1px solid #223;
#       padding-top:1rem;
#     }
#     .footer-legal a{
#       color:#eee;text-decoration:none;margin:0 .25rem;
#       transition:color var(--transition);
#     }
#     .footer-legal a:hover{color:var(--color-primary);}

#     @media(min-width:768px){
#       .footer-inner{
#         display:grid;
#         grid-template-columns:2fr 1fr 1fr 1fr;
#         text-align:left;
#       }
#       .footer-legal{grid-column:1/-1;}
#       .footer-social{justify-content:flex-start;}
#       .footer-brand-social{text-align:left;}
#     }
#   </style>
# </head>
# <body>
#   <!-- HEADER -->
#   <header>
#     <div class="logo">
#       <img src="/assets/cellanova_logo.png" alt="CellaNova Tech">
#       <h1>CellaNova Tech</h1>
#     </div>
#     <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
#       <svg id="themeIcon"><use xlink:href="#icon-moon"/></svg>
#     </button>
#   </header>

#   <!-- BUILDER -->
#   <main>
#     <div class="builder-container">
#       <div class="builder-header"><h2>Resume Builder</h2></div>
#       <div class="builder-body">
#         <div id="step1" class="step">
#           <label>Upload Resume (PDF)</label>
#           <input type="file" id="fileInput" accept="application/pdf">
#           <div class="actions">
#             <button id="toStep2" disabled>Next</button>
#           </div>
#         </div>
#         <div id="step2" class="step" style="display:none;">
#           <label>Job Posting URL</label>
#           <input type="text" id="jobUrl" placeholder="https://…">
#           <div class="actions">
#             <button id="back">Back</button>
#             <button id="run">Generate</button>
#           </div>
#         </div>
#         <div id="loader" style="display:none; text-align:center;">
#           <div class="spinner"></div>
#           <div class="status" id="loaderText">Initializing…</div>
#         </div>
#       </div>
#     </div>
#   </main>

#   <!-- FULL-SCREEN MARKDOWN OUTPUT -->
#   <section id="markdownOutputWrapper">
#     <div class="markdown-toolbar">
#       <button id="editBtn">✏️ Edit</button>
#       <button id="copyBtn">📋 Copy Markdown</button>
#     </div>
#     <textarea id="outputArea" readonly placeholder="Your rewritten resume & cover materials will appear here…"></textarea>
#   </section>

#   <!-- SVG ICON SPRITES -->
#   <svg style="display:none" xmlns="http://www.w3.org/2000/svg">
#     <!-- Moon & Sun -->
#     <symbol id="icon-moon" viewBox="0 0 24 24">
#       <path d="M21 12.79A9 9 0 0111.21 3 7 7 0 1012 21a9 9 0 009-8.21z"/>
#     </symbol>
#     <symbol id="icon-sun" viewBox="0 0 24 24">
#       <circle cx="12" cy="12" r="5"/><g stroke="#000" stroke-width="2">
#         <line x1="12" y1="1" x2="12" y2="3"/>
#         <!-- … other sun rays … -->
#       </g>
#     </symbol>
#     <!-- LinkedIn, Instagram, Twitter omitted for brevity—you can paste your full <symbol> blocks here -->
#   </svg>

#   <!-- FOOTER -->
#   <footer class="site-footer">
#     <div class="footer-inner">
#       <div class="footer-brand-social">
#         <img src="/assets/cellanova_logo.png" class="footer-logo" alt="CellaNova Tech">
#         <span class="footer-title">CellaNova Technologies</span>
#         <div class="footer-social">
#           <a href="#" aria-label="LinkedIn"><svg><use xlink:href="#icon-linkedin"/></svg></a>
#           <a href="#" aria-label="Instagram"><svg><use xlink:href="#icon-instagram"/></svg></a>
#           <a href="#" aria-label="Twitter"><svg><use xlink:href="#icon-twitter"/></svg></a>
#         </div>
#       </div>
#       <div class="footer-col">
#         <h4>Solutions</h4>
#         <ul>
#           <li><a href="#">CustomCore</a></li>
#           <li><a href="#">LaunchKit</a></li>
#           <li><a href="#">PrecisionTasks</a></li>
#         </ul>
#       </div>
#       <div class="footer-col">
#         <h4>Resources</h4>
#         <ul>
#           <li><a href="how-it-works.html">How it Works</a></li>
#           <li><a href="agents.html">Agents</a></li>
#           <li><a href="use-cases.html">Use Cases</a></li>
#           <li><a href="developer-docs.html">Developer Docs</a></li>
#         </ul>
#       </div>
#       <div class="footer-col">
#         <h4>Contact</h4>
#         <ul>
#           <li><a href="mailto:contact@cellanova.com">contact@cellanova.com</a></li>
#           <li>5900 Balcones Dr Ste 100</li>
#           <li>Austin, TX 78731</li>
#         </ul>
#       </div>
#       <div class="footer-legal">
#         &copy; 2025 CellaNova Technologies |
#         <a href="#">Terms of Use</a> |
#         <a href="#">Privacy Policy</a> |
#         <a href="#">Cookie Notice</a> |
#         <a href="#">Accessibility Statement</a>
#       </div>
#     </div>
#   </footer>

#   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
#   <script>
#     // ─── THEME TOGGLE ───────────────────────────────────────────────
#     const htmlEl = document.documentElement;
#     const themeBtn = document.getElementById('themeToggle');
#     const iconUse = document.getElementById('themeIcon').querySelector('use');
#     let theme = localStorage.getItem('theme')||'dark';
#     htmlEl.setAttribute('data-theme',theme);
#     iconUse.setAttribute('xlink:href', theme==='dark'? '#icon-moon':'#icon-sun');
#     themeBtn.onclick = ()=>{
#       theme = theme==='dark'?'light':'dark';
#       localStorage.setItem('theme',theme);
#       htmlEl.setAttribute('data-theme',theme);
#       iconUse.setAttribute('xlink:href', theme==='dark'? '#icon-moon':'#icon-sun');
#     };

#     // ─── BUILDER LOGIC ──────────────────────────────────────────────
#     const fileInput = document.getElementById('fileInput'),
#           toStep2   = document.getElementById('toStep2'),
#           backBtn   = document.getElementById('back'),
#           runBtn    = document.getElementById('run'),
#           step1     = document.getElementById('step1'),
#           step2     = document.getElementById('step2'),
#           loader    = document.getElementById('loader'),
#           loaderText= document.getElementById('loaderText'),
#           outputArea= document.getElementById('outputArea');

#     let resumeText = '';

#     fileInput.onchange = ()=> toStep2.disabled = !fileInput.files.length;

#     toStep2.onclick = async ()=>{
#       const f = fileInput.files[0]; if(!f) return;
#       step1.style.display='none';
#       loader.style.display='block'; loaderText.textContent='Extracting PDF…';
#       const form=new FormData(); form.append('pdf',f);
#       const res = await fetch('/api/extract',{method:'POST',body:form});
#       resumeText = (await res.json()).text||'';
#       loader.style.display='none';
#       step2.style.display='flex';
#     };

#     backBtn.onclick = ()=>{ step2.style.display='none'; step1.style.display='flex'; };

#     runBtn.onclick = async ()=>{
#       step2.style.display='none';
#       loader.style.display='block';
#       const statuses=['Analyzing…','Crafting Markdown…'], iv = setInterval(()=>{
#         loaderText.textContent = statuses.shift();
#         statuses.push(loaderText.textContent);
#       },1200);

#       try {
#         const resp = await fetch('/api/run',{
#           method:'POST',
#           headers:{'Content-Type':'application/json'},
#           body:JSON.stringify({
#             resume_text: resumeText,
#             job_description_url: document.getElementById('jobUrl').value
#           })
#         });
#         const { output } = await resp.json();
#         outputArea.value = output||'';
#       } catch(e) {
#         outputArea.value = 'Error: '+e;
#       } finally {
#         clearInterval(iv);
#         loader.style.display='none';
#       }
#     };

#     // ─── EDIT & COPY ────────────────────────────────────────────────
#     const editBtn = document.getElementById('editBtn'),
#           copyBtn = document.getElementById('copyBtn');

#     editBtn.onclick = ()=>{
#       if(outputArea.hasAttribute('readonly')){
#         outputArea.removeAttribute('readonly');
#         editBtn.textContent = '💾 Save';
#       } else {
#         outputArea.setAttribute('readonly','');
#         editBtn.textContent = '✏️ Edit';
#       }
#     };
#     copyBtn.onclick = async ()=>{
#       try {
#         await navigator.clipboard.writeText(outputArea.value);
#         copyBtn.textContent='✅ Copied';
#         setTimeout(()=>copyBtn.textContent='📋 Copy Markdown',1500);
#       } catch(e){
#         alert('Copy failed: '+e);
#       }
#     };
#   </script>
# </body>
# </html>
# """

# @app.route("/", methods=["GET"])
# def index():
#     return render_template_string(HTML_PAGE)

# @app.route("/api/extract", methods=["POST"])
# def extract_pdf():
#     f = request.files.get("pdf")
#     if not f:
#         return jsonify({"text": ""})
#     reader = PyPDF2.PdfReader(f)
#     text = "\n".join(p.extract_text() or "" for p in reader.pages)
#     return jsonify({"text": text})

# @app.route("/api/run", methods=["POST"])
# def api_run():
#     data = request.get_json() or {}
#     resume_text = data.get("resume_text","")
#     job_url     = data.get("job_description_url","")
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#     result = crew.kickoff(inputs={
#       "resume_text": resume_text,
#       "job_description_url": job_url
#     })
#     output = result if isinstance(result,str) else str(result)
#     return jsonify({"output": output.strip()})

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
# app.py
# from flask import Flask, render_template_string, request, jsonify
# import PyPDF2
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(
#     __name__,
#     static_folder="assets",
#     static_url_path="/assets"
# )

# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang="en" data-theme="dark">
# <head>
#   <meta charset="UTF-8">
#   <meta name="viewport" content="width=device-width,initial-scale=1">
#   <title>CellaNova Tech • Resume Builder</title>
#   <style>
#     /* ─── PALETTE & TYPO ───────────────────────────────────────────── */
#     :root {
#       --color-bg: #121212; --color-surface: #0d1b2a;
#       --color-text: #E0E0E0; --color-muted: #757575;
#       --color-primary: #1ABC9C; --color-secondary: #FFC107;
#       --color-accent: #FF5722; --radius: 8px;
#       --transition: 0.3s; --font-stack: "Inter",sans-serif;
#       --footer-height: 320px;
#     }
#     html[data-theme="light"] {
#       --color-bg:#f4f7fa; --color-surface:#fff;
#       --color-text:#333; --color-muted:#888;
#     }
#     *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
#     body {
#       background:var(--color-bg); color:var(--color-text);
#       font-family:var(--font-stack); display:flex;
#       flex-direction:column; min-height:100vh;
#       transition:background var(--transition),color var(--transition);
#     }
#     /* slim scrollbar */
#     ::-webkit-scrollbar{width:8px;}
#     ::-webkit-scrollbar-track{background:var(--color-bg);}
#     ::-webkit-scrollbar-thumb{background:#111;border-radius:4px;}
#     ::-webkit-scrollbar-thumb:hover{background:#333;}

#     /* ─── HEADER ───────────────────────────────────────────────────── */
#     header {
#       background:var(--color-surface);
#       padding:1rem 2rem;
#       display:flex; align-items:center; justify-content:space-between;
#       box-shadow:0 2px 4px rgba(0,0,0,0.7);
#     }
#     .logo{display:flex;align-items:center;}
#     .logo img{height:36px;margin-right:.75rem;}
#     .logo h1{
#       font-size:1.25rem; text-transform:uppercase;
#       letter-spacing:.05em; color:var(--color-text);
#     }
#     .theme-toggle{
#       background:none;border:none;cursor:pointer;
#       padding:.5rem;border-radius:var(--radius);
#       transition:background var(--transition);
#     }
#     .theme-toggle:hover{background:rgba(255,255,255,0.1);}
#     .theme-toggle svg{
#       width:24px;height:24px;fill:var(--color-text);
#       transition:fill var(--transition);
#     }

#     /* ─── BUILDER CARD ───────────────────────────────────────────── */
#     main {
#       flex:1; display:flex; align-items:flex-start;
#       justify-content:center;
#       padding:6rem 2rem 2rem;
#       padding-bottom:calc(var(--footer-height)+2rem);
#     }
#     .builder-container {
#       background:var(--color-surface);
#       border-radius:var(--radius);
#       box-shadow:0 8px 24px rgba(0,0,0,0.7);
#       max-width:600px; width:100%; overflow:hidden;
#       animation:fadeInUp .6s ease-out;
#     }
#     @keyframes fadeInUp{
#       from{opacity:0;transform:translateY(20px);}
#       to{opacity:1;transform:translateY(0);}
#     }
#     .builder-header{
#       background:var(--color-primary);
#       padding:1rem;text-align:center;cursor:pointer;
#       transition:background var(--transition);
#     }
#     .builder-header:hover{background:var(--color-secondary);}
#     .builder-header h2{margin:0;color:var(--color-surface);font-size:1.5rem;}
#     .builder-body{
#       padding:1.5rem;display:flex;
#       flex-direction:column;gap:1.5rem;
#     }
#     .step{display:flex;flex-direction:column;gap:.5rem;}
#     label{color:var(--color-muted);}
#     input[type="file"],input[type="text"]{
#       width:100%;padding:.75rem;border:none;
#       border-radius:var(--radius);
#       background:#222;color:var(--color-text);
#       transition:background var(--transition),transform var(--transition);
#     }
#     input:focus{
#       outline:2px solid var(--color-accent);
#       background:#333;transform:scale(1.02);
#     }
#     .actions{display:flex;justify-content:flex-end;gap:.5rem;}
#     .actions button{
#       padding:.6rem 1.2rem;
#       background:var(--color-accent);
#       color:var(--color-surface);
#       border:none;border-radius:var(--radius);
#       cursor:pointer;
#       transition:background var(--transition),transform var(--transition);
#     }
#     .actions button:disabled{
#       background:var(--color-muted);opacity:.6;cursor:not-allowed;
#     }
#     .actions button:hover:not(:disabled){
#       background:var(--color-secondary);
#       transform:translateY(-2px) scale(1.03);
#     }

#     /* ─── LOADER ───────────────────────────────────────────────────── */
#     .spinner{
#       width:48px;height:48px;
#       border:6px solid var(--color-muted);
#       border-top:6px solid var(--color-accent);
#       border-radius:50%;
#       animation:spin .8s linear infinite;
#       margin:1.5rem auto;
#     }
#     @keyframes spin{to{transform:rotate(360deg);}}
#     .status{text-align:center;font-style:italic;color:var(--color-muted);}

#     /* ─── MARKDOWN OUTPUT ──────────────────────────────────────────── */
#     #markdownOutputWrapper{
#       width:100vw; padding:1rem;
#       background:var(--color-surface);
#       box-sizing:border-box;
#     }
#     .markdown-toolbar{
#       display:flex;justify-content:flex-end;gap:.5rem;
#       margin-bottom:.5rem;
#     }
#     .markdown-toolbar button{
#       background:var(--color-accent);
#       color:var(--color-surface);
#       border:none;padding:.5rem 1rem;
#       border-radius:var(--radius);
#       cursor:pointer;transition:background var(--transition);
#     }
#     .markdown-toolbar button:hover{background:var(--color-secondary);}
#     #renderedOutput{
#       padding:1rem;
#       background:var(--color-bg);
#       border-radius:var(--radius);
#       color:var(--color-text);
#       overflow-y:auto;
#       max-height:calc(100vh - 240px);
#     }
#     #outputArea{
#       display:none;
#       width:100%; height:calc(100vh - 240px);
#       background:var(--color-bg);
#       color:var(--color-text);
#       border:1px solid var(--color-muted);
#       border-radius:var(--radius);
#       padding:1rem; font-family:monospace;
#       font-size:.95rem; resize:vertical;
#       white-space:pre-wrap; overflow-y:auto;
#     }

#     /* ─── FOOTER ───────────────────────────────────────────────────── */
#     footer.site-footer{
#       background:#0d1b2a; color:#ddd;
#       padding:3rem 1rem 1rem;
#     }
#     .footer-inner{
#       max-width:1200px; margin:0 auto;
#       display:flex;flex-direction:column;
#       gap:2rem;align-items:center;
#     }
#     .footer-brand-social{text-align:center;}
#     .footer-logo{width:40px;height:40px;vertical-align:middle;}
#     .footer-title{
#       font-size:1.25rem;font-weight:700;
#       margin-left:.5rem;color:var(--color-primary);
#       vertical-align:middle;
#     }
#     .footer-social{
#       margin-top:1rem;display:flex;gap:1rem;justify-content:center;
#     }
#     .footer-social svg{
#       width:24px;height:24px;fill:#ddd;
#       transition:fill var(--transition);
#     }
#     .footer-social a:hover svg{fill:var(--color-primary);}
#     .footer-col{text-align:center;}
#     .footer-col h4{
#       color:var(--color-primary);margin-bottom:.75rem;
#     }
#     .footer-col ul{
#       list-style:none;padding:0;line-height:1.6;
#     }
#     .footer-col ul li+li{margin-top:.5rem;}
#     .footer-col ul li a{
#       color:#eee;text-decoration:none;
#       transition:color var(--transition);
#     }
#     .footer-col ul li a:hover{color:var(--color-primary);}
#     .footer-legal{
#       font-size:.8rem;text-align:center;
#       margin-top:2rem;border-top:1px solid #223;
#       padding-top:1rem;
#     }
#     .footer-legal a{
#       color:#eee;text-decoration:none;margin:0 .25rem;
#       transition:color var(--transition);
#     }
#     .footer-legal a:hover{color:var(--color-primary);}
#     @media(min-width:768px){
#       .footer-inner{
#         display:grid;
#         grid-template-columns:2fr 1fr 1fr 1fr;
#         text-align:left;
#       }
#       .footer-legal{grid-column:1/-1;}
#       .footer-social{justify-content:flex-start;}
#       .footer-brand-social{text-align:left;}
#     }
#   </style>
# </head>
# <body>
#   <!-- HEADER -->
#   <header>
#     <div class="logo">
#       <img src="/assets/cellanova_logo.png" alt="CellaNova Tech">
#       <h1>CellaNova Tech</h1>
#     </div>
#     <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
#       <svg id="themeIcon"><use xlink:href="#icon-moon"/></svg>
#     </button>
#   </header>

#   <!-- BUILDER -->
#   <main>
#     <div class="builder-container">
#       <div class="builder-header"><h2>Resume Builder</h2></div>
#       <div class="builder-body">
#         <div id="step1" class="step">
#           <label>Upload Resume (PDF)</label>
#           <input type="file" id="fileInput" accept="application/pdf">
#           <div class="actions">
#             <button id="toStep2" disabled>Next</button>
#           </div>
#         </div>
#         <div id="step2" class="step" style="display:none;">
#           <label>Job Posting URL</label>
#           <input type="text" id="jobUrl" placeholder="https://…">
#           <div class="actions">
#             <button id="back">Back</button>
#             <button id="run">Generate</button>
#           </div>
#         </div>
#         <div id="loader" style="display:none;text-align:center;">
#           <div class="spinner"></div>
#           <div class="status" id="loaderText">Initializing…</div>
#         </div>
#       </div>
#     </div>
#   </main>

#   <!-- MARKDOWN OUTPUT -->
#   <section id="markdownOutputWrapper">
#     <div class="markdown-toolbar">
#       <button id="editBtn">✏️ Edit</button>
#       <button id="copyBtn">📋 Copy Markdown</button>
#     </div>
#     <div id="renderedOutput"></div>
#     <textarea id="outputArea" readonly></textarea>
#   </section>

#   <!-- SVG SPRITES -->
#   <svg style="display:none" xmlns="http://www.w3.org/2000/svg">
#     <!-- Moon & Sun -->
#     <symbol id="icon-moon" viewBox="0 0 24 24">
#       <path d="M21 12.79A9 9 0 0111.21 3 7 7 0 1012 21a9 9 0 009-8.21z"/>
#     </symbol>
#     <symbol id="icon-sun" viewBox="0 0 24 24">
#       <circle cx="12" cy="12" r="5"/><g stroke="#000" stroke-width="2">
#         <line x1="12" y1="1" x2="12" y2="3"/>
#         <line x1="12" y1="21" x2="12" y2="23"/>
#         <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
#         <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
#         <line x1="1" y1="12" x2="3" y2="12"/>
#         <line x1="21" y1="12" x2="23" y2="12"/>
#         <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
#         <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
#       </g>
#     </symbol>

#     <!-- LinkedIn -->
#     <symbol id="icon-linkedin" viewBox="0 0 24 24">
#       <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5
#         1.12 1 2.5 1s2.48 1.12 2.48 2.5zm.02
#         4.5H0V24h5V8zM8 8h4.218v2.234h.059c.587
#         -1.116 2.023-2.234 4.164-2.234C22.49
#         8 24 10.334 24 14.133V24h-5v-9.867c0
#         -2.351-.042-5.379-3.277-5.379-3.28
#         0-3.784 2.565-3.784 5.212V24H8V8z"/>
#     </symbol>
#     <!-- Instagram -->
#     <symbol id="icon-instagram" viewBox="0 0 24 24">
#       <path d="M12 2.163c3.204 0 3.584.012 4.85.07
#         1.206.056 1.83.246 2.257.415a4.605
#         4.605 0 011.675 1.09 4.605 4.605
#         0 011.09 1.675c.169.427.359 1.051.415
#         2.257.058 1.266.07 1.645.07 4.85s
#         -.012 3.584-.07 4.85c-.056 1.206
#         -.246 1.83-.415 2.257a4.605 4.605
#         0 01-1.09 1.675 4.605 4.605 0 01
#         -1.675 1.09c-.427.169-1.051.359
#         -2.257.415-1.266.058-1.645.07
#         -4.85.07s-3.584-.012-4.85-.07
#         c-1.206-.056-1.83-.246-2.257
#         -.415a4.605 4.605 0 01-1.675
#         -1.09 4.605 4.605 0 01-1.09
#         -1.675c-.169-.427-.359-1.051
#         -.415-2.257C2.175 15.747 2.163
#         15.368 2.163 12s.012-3.584.07
#         -4.85c.056-1.206.246-1.83.415
#         -2.257a4.605 4.605 0 011.09
#         -1.675 4.605 4.605 0 011.675
#         -1.09c.427-.169 1.051-.359
#         2.257-.415C8.416 2.175 8.796
#         2.163 12 2.163zm0-2.163C8.741
#         0 8.332.013 7.052.072 5.773.131
#         4.845.309 4.012.632a6.772 6.772
#         0 00-2.462 1.61A6.772 6.772 0
#         00.632 4.012C.309 4.845.131
#         5.773.072 7.052.013 8.332 0
#         8.741 0 12c0 3.259.013 3.668
#         .072 4.948.059 1.279.237
#         2.207.56 3.04a6.772 6.772 0
#         001.61 2.462 6.772 6.772 0
#         002.462 1.61c.833.323 1.761.501
#         3.04.56C8.332 23.987 8.741 24
#         12 24s3.668-.013 4.948-.072
#         c1.279-.059 2.207-.237 3.04
#         -.56a6.772 6.772 0 002.462
#         -1.61 6.772 6.772 0 001.61
#         -2.462c.323-.833.501-1.761
#         .56-3.04.059-1.28.072
#         -1.689.072-4.948s-.013
#         -3.668-.072-4.948c-.059
#         -1.279-.237-2.207-.56
#         -3.04a6.772 6.772 0
#         00-1.61-2.462A6.772
#         6.772 0 0019.988.632
#         c-.833-.323-1.761-.501
#         -3.04-.56C15.668.013
#         15.259 0 12 0z"/>
#       <circle cx="12" cy="12" r="3.6"/>
#     </symbol>
#     <!-- Twitter -->
#     <symbol id="icon-twitter" viewBox="0 0 24 24">
#       <path d="M23.954 4.569a10 10 0 01-2.825.775
#         4.932 4.932 0 002.163-2.723
#         9.864 9.864 0 01-3.127
#         1.195 4.916 4.916 0 00-8.384
#         4.482A13.944 13.944 0 011.671
#         3.149a4.902 4.902 0 001.523
#         6.549 4.903 4.903 0
#         01-2.229-.616v.061a4.914
#         4.914 0 003.946 4.809
#         4.996 4.996 0
#         01-2.224.084 4.922
#         4.922 0 004.6
#         3.417A9.867 9.867 0
#         010 19.54a13.94
#         13.94 0 007.548
#         2.212c9.056 0 14.009
#         -7.496 14.009-13.986
#         0-.21-.005-.423
#         -.015-.633A10.012
#         10.012 0 0024 4.59z"/>
#     </symbol>
#   </svg>

#   <!-- FOOTER -->
#   <footer class="site-footer">
#     <div class="footer-inner">
#       <div class="footer-brand-social">
#         <img src="/assets/cellanova_logo.png" class="footer-logo" alt="CellaNova Tech">
#         <span class="footer-title">CellaNova Technologies</span>
#         <div class="footer-social">
#           <a href="#" aria-label="LinkedIn"><svg><use xlink:href="#icon-linkedin"/></svg></a>
#           <a href="#" aria-label="Instagram"><svg><use xlink:href="#icon-instagram"/></svg></a>
#           <a href="#" aria-label="Twitter"><svg><use xlink:href="#icon-twitter"/></svg></a>
#         </div>
#       </div>
#       <div class="footer-col">
#         <h4>Solutions</h4>
#         <ul>
#           <li><a href="#">CustomCore</a></li>
#           <li><a href="#">LaunchKit</a></li>
#           <li><a href="#">PrecisionTasks</a></li>
#         </ul>
#       </div>
#       <div class="footer-col">
#         <h4>Resources</h4>
#         <ul>
#           <li><a href="how-it-works.html">How it Works</a></li>
#           <li><a href="agents.html">Agents</a></li>
#           <li><a href="use-cases.html">Use Cases</a></li>
#           <li><a href="developer-docs.html">Developer Docs</a></li>
#         </ul>
#       </div>
#       <div class="footer-col">
#         <h4>Contact</h4>
#         <ul>
#           <li><a href="mailto:contact@cellanova.com">contact@cellanova.com</a></li>
#           <li>5900 Balcones Dr Ste 100</li>
#           <li>Austin, TX 78731</li>
#         </ul>
#       </div>
#       <div class="footer-legal">
#         &copy; 2025 CellaNova Technologies |
#         <a href="#">Terms of Use</a> |
#         <a href="#">Privacy Policy</a> |
#         <a href="#">Cookie Notice</a> |
#         <a href="#">Accessibility Statement</a>
#       </div>
#     </div>
#   </footer>

#   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
#   <script>
#     // ─── THEME TOGGLE ───────────────────────────────────────────────
#     const htmlEl = document.documentElement;
#     const themeBtn = document.getElementById('themeToggle');
#     const iconUse = document.getElementById('themeIcon').querySelector('use');
#     let theme = localStorage.getItem('theme')||'dark';
#     htmlEl.setAttribute('data-theme',theme);
#     iconUse.setAttribute('xlink:href', theme==='dark'?'#icon-moon':'#icon-sun');
#     themeBtn.onclick = ()=>{
#       theme = theme==='dark'?'light':'dark';
#       localStorage.setItem('theme',theme);
#       htmlEl.setAttribute('data-theme',theme);
#       iconUse.setAttribute('xlink:href', theme==='dark'?'#icon-moon':'#icon-sun');
#     };

#     // ─── BUILDER LOGIC ──────────────────────────────────────────────
#     const fileInput = document.getElementById('fileInput'),
#           toStep2   = document.getElementById('toStep2'),
#           backBtn   = document.getElementById('back'),
#           runBtn    = document.getElementById('run'),
#           step1     = document.getElementById('step1'),
#           step2     = document.getElementById('step2'),
#           loader    = document.getElementById('loader'),
#           loaderText= document.getElementById('loaderText'),
#           rendered  = document.getElementById('renderedOutput'),
#           textarea  = document.getElementById('outputArea');

#     let resumeText = '';

#     fileInput.onchange = ()=> toStep2.disabled = !fileInput.files.length;

#     toStep2.onclick = async ()=>{
#       const f = fileInput.files[0]; if(!f) return;
#       step1.style.display='none';
#       loader.style.display='block'; loaderText.textContent='Extracting PDF…';
#       const form=new FormData(); form.append('pdf',f);
#       const res=await fetch('/api/extract',{method:'POST',body:form});
#       resumeText = (await res.json()).text||'';
#       loader.style.display='none';
#       step2.style.display='flex';
#     };

#     backBtn.onclick = ()=>{ step2.style.display='none'; step1.style.display='flex'; };

#     runBtn.onclick = async ()=>{
#       step2.style.display='none';
#       loader.style.display='block';
#       const statuses=['Analyzing…','Crafting Markdown…'], iv=setInterval(()=>{
#         loaderText.textContent=statuses.shift();
#         statuses.push(loaderText.textContent);
#       },1200);
#       try {
#         const resp = await fetch('/api/run',{
#           method:'POST',
#           headers:{'Content-Type':'application/json'},
#           body:JSON.stringify({
#             resume_text: resumeText,
#             job_description_url: document.getElementById('jobUrl').value
#           })
#         });
#         const { output } = await resp.json();
#         textarea.value = output||'';
#         rendered.innerHTML = marked.parse(output||'');
#       } catch(e) {
#         textarea.value = 'Error: '+e;
#         rendered.textContent = textarea.value;
#       } finally {
#         clearInterval(iv);
#         loader.style.display='none';
#         rendered.style.display = 'block';
#         textarea.style.display = 'none';
#       }
#     };

#     // ─── EDIT & COPY ────────────────────────────────────────────────
#     const editBtn = document.getElementById('editBtn'),
#           copyBtn = document.getElementById('copyBtn');
#     editBtn.onclick = ()=>{
#       if(textarea.style.display==='none'){
#         // switch to edit
#         rendered.style.display='none';
#         textarea.style.display='block';
#         textarea.removeAttribute('readonly');
#         editBtn.textContent='💾 Save';
#       } else {
#         // save
#         rendered.innerHTML = marked.parse(textarea.value);
#         rendered.style.display='block';
#         textarea.setAttribute('readonly','');
#         textarea.style.display='none';
#         editBtn.textContent='✏️ Edit';
#       }
#     };
#     copyBtn.onclick = async ()=>{
#       try {
#         await navigator.clipboard.writeText(textarea.value || rendered.textContent);
#         copyBtn.textContent='✅ Copied';
#         setTimeout(()=>copyBtn.textContent='📋 Copy Markdown',1500);
#       } catch(e){
#         alert('Copy failed: '+e);
#       }
#     };
#   </script>
# </body>
# </html>
# """

# @app.route("/", methods=["GET"])
# def index():
#     return render_template_string(HTML_PAGE)

# @app.route("/api/extract", methods=["POST"])
# def extract_pdf():
#     f = request.files.get("pdf")
#     if not f:
#         return jsonify({"text": ""})
#     reader = PyPDF2.PdfReader(f)
#     text = "\n".join(p.extract_text() or "" for p in reader.pages)
#     return jsonify({"text": text})

# @app.route("/api/run", methods=["POST"])
# def api_run():
#     data = request.get_json() or {}
#     resume_text = data.get("resume_text", "")
#     job_url     = data.get("job_description_url", "")
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#     result = crew.kickoff(inputs={
#       "resume_text": resume_text,
#       "job_description_url": job_url
#     })
#     output = result if isinstance(result, str) else str(result)
#     return jsonify({"output": output.strip()})

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
# import io
# from tkinter import Canvas
# from tkinter.tix import Meter
# from flask import Flask, render_template, request, jsonify, send_file
# import PyPDF2
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(
#     __name__,
#     static_folder="assets",       # <-- your logo + any css/js here
#     static_url_path="/assets",
#     template_folder="templates" 
# )

# HTML_PAGE = """
# <!DOCTYPE html>
# <html lang="en" data-theme="dark">
# <head>
# <meta charset="UTF-8">
# <meta name="viewport" content="width=device-width,initial-scale=1">
# <title>CellaNova Tech • Resume Builder</title>
# <style>
#   /* ---- COLOR + TYPOGRAPHY ---- */
#   :root {
#     --color-bg: #121212;            /* dark bg */
#     --color-surface: #0d1b2a;       /* panel bg */
#     --color-text: #E0E0E0;          /* light text */
#     --color-muted: #757575;         /* small text */
#     --color-primary: #1ABC9C;       /* green */
#     --color-secondary: #FFC107;     /* gold */
#     --color-accent: #FF5722;        /* orange */
#     --radius: 8px;
#     --transition: 0.3s;
#     --font-stack: "Inter", sans-serif;
#     --footer-height: 200px;
#   }
#   html[data-theme="light"] {
#     --color-bg: #f4f7fa;
#     --color-surface: #fff;
#     --color-text: #333;
#     --color-muted: #888;
#   }
#   *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
#   html, body {
#     height: 100%; width: 100%;
#     background: var(--color-bg);
#     color: var(--color-text);
#     font-family: var(--font-stack);
#     transition: background var(--transition), color var(--transition);
#   }

#   /* ---- HEADER ---- */
#   header {
#     background: var(--color-surface);
#     padding: 1rem 2rem;
#     display: flex;
#     align-items: center;
#     justify-content: space-between;
#     box-shadow: 0 2px 4px rgba(0,0,0,0.7);
#   }
#   .logo { display: flex; align-items: center; }
#   .logo img { height: 36px; margin-right: .75rem; }
#   .logo h1 { font-size: 1.25rem; letter-spacing: .05em; color: var(--color-text); }
#   .theme-toggle { background: none; border: none; cursor: pointer; padding: .5rem; border-radius: var(--radius); }
#   .theme-toggle:hover { background: rgba(0,0,0,0.1); }
#   .theme-toggle svg { width:24px; height:24px; fill: var(--color-text); }

#   /* ---- BUILDER ---- */
#   main {
#     flex: 1;
#     display: flex;
#     align-items: flex-start;
#     justify-content: center;
#     padding: 6rem 2rem 2rem;
#     padding-bottom: calc(var(--footer-height) + 2rem);
#   }
#   .builder-container {
#     background: var(--color-surface);
#     border-radius: var(--radius);
#     box-shadow: 0 8px 24px rgba(0,0,0,0.7);
#     width: 100%;
#     max-width: 800px;
#     overflow: hidden;
#     animation: fadeInUp .6s ease-out;
#   }
#   @keyframes fadeInUp {
#     from { opacity: 0; transform: translateY(20px) }
#     to   { opacity: 1; transform: translateY(0) }
#   }
#   .builder-header {
#     background: var(--color-primary);
#     padding: 1rem; text-align: center; color: var(--color-surface);
#   }
#   .builder-body { padding: 1.5rem; display: flex; flex-direction: column; gap: 1.5rem; }
#   .step { display: flex; flex-direction: column; gap: .5rem; }
#   label { color: var(--color-muted); font-size: .95rem; }
#   input[type="file"], input[type="text"] {
#     width: 100%; padding: .75rem;
#     border: none; border-radius: var(--radius);
#     background: #222; color: var(--color-text);
#     transition: background var(--transition), transform var(--transition);
#   }
#   input:focus { outline: 2px solid var(--color-accent); background: #333; transform: scale(1.02); }
#   .actions { display: flex; justify-content: flex-end; gap: .5rem; }
#   button {
#     padding: .6rem 1.2rem;
#     background: var(--color-accent);
#     color: var(--color-surface);
#     border: none; border-radius: var(--radius);
#     font-weight: 600; cursor: pointer;
#     transition: background var(--transition), transform var(--transition);
#   }
#   button:disabled { background: var(--color-muted); opacity: .6; cursor: not-allowed; }
#   button:hover:not(:disabled) { background: var(--color-secondary); transform: translateY(-2px) scale(1.03); }

#   .spinner {
#     width: 48px; height: 48px;
#     border: 6px solid var(--color-muted);
#     border-top: 6px solid var(--color-accent);
#     border-radius: 50%;
#     animation: spin .8s linear infinite;
#     margin: 1.5rem auto;
#   }
#   @keyframes spin { to { transform: rotate(360deg) } }
#   .status { text-align: center; font-style: italic; color: var(--color-muted); }

#   /* ---- FULL-SCREEN OUTPUT ---- */
#   #markdownOutputWrapper {
#     display: none;
#     position: fixed;
#     top: 0; left: 0;
#     width: 100vw; height: 100vh;
#     background: var(--color-bg);
#     overflow-y: auto;
#     padding: 2rem;
#     z-index: 100;
#   }
#   .markdown-toolbar {
#     display: none;
#     position: fixed;
#     top: 1rem; right: 1rem;
#     gap: .5rem;
#     z-index: 110;
#   }
#   .markdown-toolbar button {
#     background: var(--color-accent);
#     color: var(--color-surface);
#     border: none;
#     border-radius: var(--radius);
#     padding: .5rem 1rem;
#     font-weight: 600;
#     cursor: pointer;
#     transition: background var(--transition);
#   }
#   .markdown-toolbar button:hover {
#     background: var(--color-secondary);
#   }
#   #renderedOutput {
#     max-width: 800px;
#     margin: auto;
#     color: var(--color-text);
#     line-height: 1.6;
#   }
#   #outputArea {
#     display: none;
#     width: 100%;
#     height: calc(100vh - 4rem);
#     margin-top: 1rem;
#     background: var(--color-surface);
#     color: var(--color-text);
#     border: none;
#     border-radius: var(--radius);
#     padding: 1rem;
#     font-family: monospace;
#     font-size: .95rem;
#   }

#   /* ---- FOOTER ---- */
#   footer.site-footer {
#     background: var(--color-surface);
#     color: var(--color-text);
#     padding: 2rem 1rem 1rem;
#     margin-top: auto;
#   }
#   .footer-inner {
#     max-width: 1200px;
#     margin: auto;
#     display: grid;
#     grid-template-columns: 2fr 1fr 1fr 1fr;
#     gap: 2rem;
#   }
#   .footer-brand-social {
#     display: flex; align-items: center; gap: .5rem;
#   }
#   .footer-logo { width: 40px; height: 40px; }
#   .footer-title { font-size: 1.25rem; color: var(--color-primary); }
#   .footer-social { display: flex; gap: 1rem; margin-left: auto; }
#   .footer-social svg { width:24px;height:24px;fill:var(--color-text); }
#   .footer-social a:hover svg { fill: var(--color-primary); }
#   .footer-col h4 { color: var(--color-primary); margin-bottom:.5rem; }
#   .footer-col ul { list-style:none; padding:0; line-height:1.6; }
#   .footer-col ul li + li { margin-top:.3rem; }
#   .footer-col ul li a { color: var(--color-text); text-decoration:none; }
#   .footer-col ul li a:hover { color: var(--color-primary);}
#   .footer-legal {
#     grid-column: 1 / -1;
#     font-size:.8rem;
#     text-align:center;
#     margin-top:1rem;
#     border-top:1px solid rgba(255,255,255,0.1);
#     padding-top:1rem;
#   }
#   .footer-legal a { color: var(--color-text); text-decoration:none; margin:0 .25rem; }
#   .footer-legal a:hover { color: var(--color-primary); }

#   @media (max-width:768px) {
#     .footer-inner { display:flex; flex-direction:column; align-items:center; }
#     .footer-legal { text-align:center; }
#   }
# </style>

# <!-- marked.js for Markdown rendering -->
# <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
# </head>
# <body>

#   <!-- HEADER -->
#   <header>
#     <div class="logo">
#       <img src="/assets/cellaNova_logo.png" alt="CellaNova Tech">
#       <h1>CellaNova Tech</h1>
#     </div>
#     <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
#       <svg id="themeIcon"><use xlink:href="#icon-moon"></use></svg>
#     </button>
#   </header>

#   <!-- BUILDER -->
#   <main>
#     <div class="builder-container">
#       <div class="builder-header"><h2>Resume Builder</h2></div>
#       <div class="builder-body">

#         <!-- Step 1 -->
#         <div id="step1" class="step">
#           <label for="fileInput">Upload your resume (PDF)</label>
#           <input type="file" id="fileInput" accept="application/pdf">
#           <div class="actions">
#             <button id="toStep2" disabled>Next</button>
#           </div>
#         </div>

#         <!-- Step 2 -->
#         <div id="step2" class="step" style="display:none;">
#           <label for="jobUrl">Job description URL</label>
#           <input type="text" id="jobUrl" placeholder="https://example.com/job-posting">
#           <div class="actions">
#             <button id="back">Back</button>
#             <button id="run">Generate</button>
#           </div>
#         </div>

#         <!-- Loading -->
#         <div id="loader" style="display:none; text-align:center;">
#           <div class="spinner"></div>
#           <div class="status" id="loaderText">Initializing…</div>
#         </div>

#       </div>
#     </div>
#   </main>

#   <!-- FULL-SCREEN MARKDOWN OUTPUT -->
#   <section id="markdownOutputWrapper">
#     <div class="markdown-toolbar">
#       <button id="editBtn">Edit</button>
#       <button id="copyBtn">Copy Text</button>
#     </div>
#     <div id="renderedOutput"></div>
#     <textarea id="outputArea" readonly></textarea>
#   </section>

#   <!-- FOOTER -->
#   <footer class="site-footer">
#     <div class="footer-inner">
#       <div class="footer-brand-social">
#         <img src="/assets/cellaNova_logo.png" class="footer-logo" alt="CellaNova Logo">
#         <span class="footer-title">CellaNova Technologies</span>
#         <div class="footer-social">
#           <a href="#"><svg><use xlink:href="#icon-linkedin"/></svg></a>
#           <a href="#"><svg><use xlink:href="#icon-instagram"/></svg></a>
#           <a href="#"><svg><use xlink:href="#icon-twitter"/></svg></a>
#         </div>
#       </div>
#       <div class="footer-col">
#         <h4>Solutions</h4>
#         <ul>
#           <li><a href="how-it-works.html">CustomCore</a></li>
#           <li><a href="agents.html">LaunchKit</a></li>
#           <li><a href="use-cases.html">PrecisionTasks</a></li>
#         </ul>
#       </div>
#       <div class="footer-col">
#         <h4>Resources</h4>
#         <ul>
#           <li><a href="how-it-works.html">How it Works</a></li>
#           <li><a href="agents.html">Agents</a></li>
#           <li><a href="use-cases.html">Use Cases</a></li>
#           <li><a href="developer-docs.html">Developer Docs</a></li>
#         </ul>
#       </div>
#       <div class="footer-col">
#         <h4>Contact</h4>
#         <ul>
#           <li><a href="mailto:contactcnt@cellanovatech.com">contactcnt@cellanovatech.com</a></li>
#           <li>5900 Balcones Dr Ste 100</li>
#           <li>Austin, TX 78731-4298</li>
#         </ul>
#       </div>
#       <div class="footer-legal">
#         &copy; 2025 CellaNova Technologies —
#         <a href="#">Terms</a> | <a href="#">Privacy</a>
#       </div>
#     </div>
#   </footer>

# <!-- SVG ICON SPRITES -->
# <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
#   <symbol id="icon-moon" viewBox="0 0 24 24">
#     <path d="M21 12.79A9 9 0 0111.21 3 7 7 0 1012 21a9 9 0 009-8.21z"/>
#   </symbol>
#   <symbol id="icon-sun" viewBox="0 0 24 24">
#     <circle cx="12" cy="12" r="5"/>
#     <g stroke="#000" stroke-width="2">
#       <line x1="12" y1="1"  x2="12" y2="3"/>
#       <line x1="12" y1="21" x2="12" y2="23"/>
#       <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
#       <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
#       <line x1="1" y1="12"  x2="3"    y2="12"/>
#       <line x1="21" y1="12" x2="23"   y2="12"/>
#       <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
#       <line x1="18.36" y1="5.64"  x2="19.78" y2="4.22"/>
#     </g>
#   </symbol>
#   <symbol id="icon-linkedin" viewBox="0 0 24 24">
#     <path d="M4.98 3.5C4.98 4.88 3.88 6 2.5 6S0 4.88 0 3.5 ..."/>
#   </symbol>
#   <symbol id="icon-instagram" viewBox="0 0 24 24">
#     <path d="..."/>
#   </symbol>
#   <symbol id="icon-twitter" viewBox="0 0 24 24">
#     <path d="..."/>
#   </symbol>
# </svg>

# <script>
#   // THEME TOGGLE
#   const htmlEl = document.documentElement;
#   const btn     = document.getElementById('themeToggle');
#   const iconUse = document.querySelector('#themeIcon use');
#   let theme = localStorage.getItem('theme') || 'dark';
#   htmlEl.setAttribute('data-theme', theme);
#   iconUse.setAttribute('xlink:href', theme==='dark'? '#icon-moon':'#icon-sun');
#   btn.onclick = ()=>{
#     theme = theme==='dark' ? 'light':'dark';
#     htmlEl.setAttribute('data-theme', theme);
#     iconUse.setAttribute('xlink:href', theme==='dark'? '#icon-moon':'#icon-sun');
#     localStorage.setItem('theme', theme);
#   };

#   // BUILDER LOGIC
#   const fileInput = document.getElementById('fileInput'),
#         toStep2   = document.getElementById('toStep2'),
#         backBtn   = document.getElementById('back'),
#         runBtn    = document.getElementById('run'),
#         step1     = document.getElementById('step1'),
#         step2     = document.getElementById('step2'),
#         loader    = document.getElementById('loader'),
#         loaderText= document.getElementById('loaderText'),
#         jobUrl    = document.getElementById('jobUrl'),
#         builder   = document.querySelector('.builder-container');

#   let resumeText = '';

#   fileInput.onchange = ()=> toStep2.disabled = !fileInput.files.length;

#   toStep2.onclick = async ()=>{
#     const f = fileInput.files[0];
#     if(!f) return;
#     step1.style.display='none';
#     loader.style.display='block';
#     loaderText.textContent='Extracting PDF…';
#     const form=new FormData(); form.append('pdf',f);
#     const res=await fetch('/api/extract',{method:'POST',body: form});
#     resumeText = (await res.json()).text || '';
#     loader.style.display='none';
#     step2.style.display='flex';
#   };

#   backBtn.onclick = ()=> {
#     step2.style.display='none';
#     step1.style.display='flex';
#   };

#   runBtn.onclick = async ()=>{
#     step2.style.display='none';
#     loader.style.display='block';
#     const statuses=['Analyzing…','Rewriting…'];
#     let idx=0;
#     const iv=setInterval(()=>{
#       loaderText.textContent=statuses[idx];
#       idx=(idx+1)%statuses.length;
#     },1200);

#     const rendered = document.getElementById('renderedOutput');
#     const textarea = document.getElementById('outputArea');
#     try{
#       const resp = await fetch('/api/run',{
#         method:'POST',
#         headers:{'Content-Type':'application/json'},
#         body: JSON.stringify({
#           resume_text: resumeText,
#           job_description_url: jobUrl.value
#         })
#       });
#       const {output} = await resp.json();
#       textarea.value = output||'';
#       rendered.innerHTML = marked.parse(output||'');
#     }catch(e){
#       textarea.value = 'Error: '+e.message;
#       rendered.textContent = textarea.value;
#     }finally{
#       clearInterval(iv);
#       loader.style.display='none';
#       // HIDE BUILDER, SHOW OUTPUT
#       builder.style.display='none';
#       const wrap   = document.getElementById('markdownOutputWrapper');
#       const toolbar= document.querySelector('.markdown-toolbar');
#       wrap.style.display='block';
#       toolbar.style.display='flex';
#       rendered.style.display='block';
#       textarea.style.display='none';
#     }
#   };

#   // EDIT / COPY BUTTONS
#   const editBtn = document.getElementById('editBtn');
#   const copyBtn = document.getElementById('copyBtn');
#   const rendered = document.getElementById('renderedOutput');
#   const textarea = document.getElementById('outputArea');

#   editBtn.onclick = ()=>{
#     const isEditing = textarea.style.display==='block';
#     if(isEditing){
#       textarea.style.display='none';
#       rendered.style.display='block';
#       editBtn.textContent='Edit';
#     } else {
#       textarea.style.display='block';
#       rendered.style.display='none';
#       editBtn.textContent='View';
#     }
#   };

#   copyBtn.onclick = ()=>{
#     const text = textarea.style.display==='block'
#       ? textarea.value
#       : rendered.innerText;
#     navigator.clipboard.writeText(text);
#   };
# </script>
# </body>
# </html>
# """

# @app.route('/', methods=['GET'])
# def index():
#     return HTML_PAGE

# @app.route('/api/extract', methods=['POST'])
# def extract_pdf():
#     f = request.files.get('pdf')
#     if not f:
#         return jsonify({'text': ''})
#     reader = PyPDF2.PdfReader(f)
#     pages = [p.extract_text() or "" for p in reader.pages]
#     return jsonify({'text': "\n".join(pages)})
# @app.route("/", methods=["GET"])
# def index():
#     return render_template("index.html")

# @app.route("/how-it-works")
# def how_it_works():
#     return render_template("how-it-works.html")

# @app.route("/agents")
# def agents():
#     return render_template("agents.html")

# @app.route("/use-cases")
# def use_cases():
#     return render_template("use-cases.html")

# @app.route("/developer-docs")
# def developer_docs():
#     return render_template("developer-docs.html")

# @app.route("/terms")
# def terms():
#     return render_template("terms.html")

# @app.route("/privacy")
# def privacy():
#     return render_template("privacy.html")

# @app.route('/api/run', methods=['POST'])
# def api_run():
#     data = request.get_json() or {}
#     resume_text = data.get('resume_text', '')
#     job_url     = data.get('job_description_url', '')
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#     result = crew.kickoff(inputs={
#       'resume_text': resume_text,
#       'job_description_url': job_url
#     })
#     output = result if isinstance(result, str) else str(result)
#     return jsonify({'output': output.strip()})
# @app.route('/api/download-pdf', methods=['POST'])
# def download_pdf():
#     data = request.get_json() or {}
#     md = data.get('resume_markdown', '')
#     buffer = io.BytesIO()
#     c = Canvas.Canvas(buffer, pagesize=Meter)
#     w,h = Meter
#     text = c.beginText(40, h-40)
#     for line in md.split('\n'):
#         text.textLine(line)
#     c.drawText(text)
#     c.showPage(); c.save()
#     buffer.seek(0)
#     return send_file(
#       io.BytesIO(buffer.read()),
#       mimetype='application/pdf',
#       as_attachment=True,
#       download_name='resume.pdf'
#     )

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)

# app.py
# import io
# from flask import Flask, request, jsonify, send_file, render_template
# import PyPDF2
# from reportlab.lib.pagesizes import letter
# from reportlab.pdfgen import canvas
# from crew import ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew

# app = Flask(
#     __name__,
#     static_folder="assets",
#     static_url_path="/assets",
#     template_folder="templates"
# )

# HTML_PAGE = """<!DOCTYPE html>
# <html lang="en" data-theme="dark">
# <head>
#   <meta charset="UTF-8"/>
#   <meta name="viewport" content="width=device-width,initial-scale=1"/>
#   <title>CellaNova Tech • Resume Builder</title>
#   <style>
#     /* ---- THEME & RESET ---- */
#     :root {
#       --bg: #121212; --surface: #0d1b2a; --text: #E0E0E0;
#       --muted: #757575; --primary: #1ABC9C; --secondary: #FFC107;
#       --accent: #FF5722; --radius:8px; --font:'Inter',sans-serif;
#       --footer-h:200px;
#     }
#     html[data-theme="light"] {
#       --bg:#f4f7fa; --surface:#fff; --text:#333; --muted:#888;
#     }
#     *{box-sizing:border-box;margin:0;padding:0;}
#     html,body{height:100%;width:100%;background:var(--bg);color:var(--text);
#       font-family:var(--font);transition:.3s;}
#     ::-webkit-scrollbar{width:8px;}
#     ::-webkit-scrollbar-thumb{background:#333;border-radius:4px;}
#     /* ---- HEADER ---- */
#     header{background:var(--surface);padding:1rem 2rem;
#       display:flex;align-items:center;justify-content:space-between;
#       box-shadow:0 2px 4px rgba(0,0,0,.7);}
#     .logo img{height:36px;margin-right:.75rem;}
#     .logo h1{font-size:1.25rem;color:var(--text);}
#     .theme-toggle{background:none;border:none;cursor:pointer;padding:.5rem;}
#     /* ---- MAIN BUILDER ---- */
#     main{flex:1;display:flex;align-items:flex-start;
#       justify-content:center;padding:6rem 2rem 2rem;
#       padding-bottom:calc(var(--footer-h)+2rem);}
#     .builder{background:var(--surface);border-radius:var(--radius);
#       box-shadow:0 8px 24px rgba(0,0,0,.7);width:100%;max-width:800px;
#       overflow:hidden;animation:fadeInUp .6s ease-out;}
#     @keyframes fadeInUp{from{opacity:0;transform:translateY(20px);}
#       to{opacity:1;transform:translateY(0);}}
#     .builder-header{background:var(--primary);padding:1rem;
#       text-align:center;color:var(--surface);}
#     .builder-body{padding:1.5rem;display:flex;flex-direction:column;gap:1.5rem;}
#     .step{display:flex;flex-direction:column;gap:.5rem;}
#     input,button{font-size:1rem;}
#     input[type=file],input[type=text]{
#       width:100%;padding:.75rem;border:none;border-radius:var(--radius);
#       background:#222;color:var(--text);transition:.3s;}
#     input:focus{outline:2px solid var(--accent);background:#333;}
#     .actions{display:flex;justify-content:flex-end;gap:.5rem;}
#     button{padding:.6rem 1.2rem;border:none;border-radius:var(--radius);
#       background:var(--accent);color:var(--surface);font-weight:600;
#       cursor:pointer;transition:.3s;}
#     button:disabled{background:var(--muted);opacity:.6;cursor:not-allowed;}
#     button:hover:not(:disabled){background:var(--secondary);
#       transform:translateY(-2px) scale(1.03);}
#     .spinner{width:48px;height:48px;border:6px solid var(--muted);
#       border-top:6px solid var(--accent);border-radius:50%;
#       animation:spin .8s linear infinite;margin:1.5rem auto;}
#     @keyframes spin{to{transform:rotate(360deg);}}
#     .status{text-align:center;font-style:italic;color:var(--muted);}
#     /* ---- FULLSCREEN OUTPUT ---- */
#     #markdownWrapper{display:none;position:fixed;top:0;left:0;
#       width:100vw;height:100vh;background:var(--bg);overflow:auto;
#       padding:2rem;z-index:100;}
#     .toolbar{display:none;position:fixed;top:1rem;right:1rem;gap:.5rem;z-index:110;}
#     .toolbar button{background:var(--accent);color:var(--surface);
#       border:none;border-radius:var(--radius);padding:.5rem 1rem;cursor:pointer;}
#     .toolbar button:hover{background:var(--secondary);}
#     #rendered{max-width:800px;margin:auto;line-height:1.6;color:var(--text);}
#     #outputArea{display:none;width:100%;height:calc(100vh-4rem);
#       margin-top:1rem;background:var(--surface);color:var(--text);
#       border:none;border-radius:var(--radius);padding:1rem;
#       font-family:monospace;font-size:.95rem;overflow:auto;}
#     /* ---- FOOTER ---- */
#     footer{background:var(--surface);color:var(--text);
#       padding:2rem 1rem;margin-top:auto;}
#     .footer-inner{max-width:1200px;margin:auto;
#       display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:2rem;}
#     .footer-logo{width:40px;height:40px;}
#     .footer-title{font-size:1.25rem;color:var(--primary);}
#     .footer-social{display:flex;gap:1rem;margin-left:auto;}
#     .footer-social svg{width:24px;height:24px;fill:var(--text);}
#     .footer-social a:hover svg{fill:var(--primary);}
#     .footer-col h4{color:var(--primary);margin-bottom:.5rem;}
#     .footer-col ul{list-style:none;padding:0;line-height:1.6;}
#     .footer-col ul li+li{margin-top:.3rem;}
#     .footer-col ul li a{color:var(--text);text-decoration:none;}
#     .footer-col ul li a:hover{color:var(--primary);}
#     .footer-legal{grid-column:1/-1;font-size:.8rem;text-align:center;
#       margin-top:1rem;border-top:1px solid rgba(255,255,255,.1);
#       padding-top:1rem;}
#     .footer-legal a{color:var(--text);text-decoration:none;margin:0 .25rem;}
#     .footer-legal a:hover{color:var(--primary);}
#     @media(max-width:768px){
#       .footer-inner{display:flex;flex-direction:column;align-items:center;}
#     }
#   </style>
#   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
# </head>
# <body>

# <header>
#   <div class="logo">
#     <img src="/assets/cellanova_logo.png" alt="CellaNova Tech"/>
#     <h1>CellaNova Tech</h1>
#   </div>
#   <button id="themeToggle" class="theme-toggle" aria-label="Toggle theme">
#     <svg id="themeIcon"><use xlink:href="#icon-moon"/></svg>
#   </button>
# </header>

# <main>
#   <div class="builder">
#     <div class="builder-header"><h2>Resume Builder</h2></div>
#     <div class="builder-body">
#       <div id="step1" class="step">
#         <label>Upload your resume (PDF)</label>
#         <input type="file" id="fileInput" accept="application/pdf"/>
#         <div class="actions">
#           <button id="toStep2" disabled>Next</button>
#         </div>
#       </div>
#       <div id="step2" class="step" style="display:none;">
#         <label>Job description URL</label>
#         <input type="text" id="jobUrl" placeholder="https://…"/>
#         <div class="actions">
#           <button id="back">Back</button>
#           <button id="run">Generate</button>
#         </div>
#       </div>
#       <div id="loader" style="display:none;">
#         <div class="spinner"></div>
#         <div class="status" id="loaderText">Initializing…</div>
#       </div>
#     </div>
#   </div>
# </main>

# <section id="markdownWrapper">
#   <div class="toolbar">
#     <button id="editBtn">Edit</button>
#     <button id="copyBtn">Copy Text</button>
#     <button id="downloadBtn">Download PDF</button>
#   </div>
#   <div id="rendered"></div>
#   <textarea id="outputArea" readonly></textarea>
# </section>

# <footer>
#   <div class="footer-inner">
#     <div class="logo footer-brand-social">
#       <img src="/assets/cellanova_logo.png" class="footer-logo"/>
#       <span class="footer-title">CellaNova Technologies</span>
#       <div class="footer-social">
#         <a href="#"><svg><use xlink:href="#icon-linkedin"/></svg></a>
#         <a href="#"><svg><use xlink:href="#icon-instagram"/></svg></a>
#         <a href="#"><svg><use xlink:href="#icon-twitter"/></svg></a>
#       </div>
#     </div>
#     <div class="footer-col">
#       <h4>Solutions</h4>
#       <ul>
#         <li><a href="how-it-works.html">CustomCore</a></li>
#         <li><a href="agents.html">LaunchKit</a></li>
#         <li><a href="use-cases.html">PrecisionTasks</a></li>
#       </ul>
#     </div>
#     <div class="footer-col">
#       <h4>Resources</h4>
#       <ul>
#         <li><a href="how-it-works.html">How it Works</a></li>
#         <li><a href="agents.html">Agents</a></li>
#         <li><a href="use-cases.html">Use Cases</a></li>
#         <li><a href="developer-docs.html">Developer Docs</a></li>
#       </ul>
#     </div>
#     <div class="footer-col">
#       <h4>Contact</h4>
#       <ul>
#         <li><a href="mailto:contactcnt@cellanovatech.com">contactcnt@cellanovatech.com</a></li>
#         <li>5900 Balcones Dr Ste 100</li>
#         <li>Austin, TX 78731-4298</li>
#       </ul>
#     </div>
#     <div class="footer-legal">
#       &copy; 2025 CellaNova Technologies —
#       <a href="terms.html">Terms</a> |
#       <a href="privacy.html">Privacy</a>
#     </div>
#   </div>
# </footer>

# <!-- ICON SPRITES -->
# <svg xmlns="http://www.w3.org/2000/svg" style="display:none">
#   <symbol id="icon-moon" viewBox="0 0 24 24">
#     <path d="M21 12.79A9 9 0 0111.21 3 7 7 0 1012 21a9 9 0 009-8.21z"/>
#   </symbol>
#   <symbol id="icon-sun" viewBox="0 0 24 24">
#     <circle cx="12" cy="12" r="5"/>
#     <g stroke="#000" stroke-width="2">
#       <line x1="12" y1="1" x2="12" y2="3"/>
#       <line x1="12" y1="21" x2="12" y2="23"/>
#       <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
#       <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
#       <line x1="1" y1="12" x2="3" y2="12"/>
#       <line x1="21" y1="12" x2="23" y2="12"/>
#       <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
#       <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
#     </g>
#   </symbol>
#   <!-- add your social icons here… -->
# </svg>

# <script>
#   // THEME
#   const htmlEl = document.documentElement;
#   const tmBtn = document.getElementById('themeToggle');
#   const tmIcon = document.querySelector('#themeIcon use');
#   let theme = localStorage.getItem('theme')||'dark';
#   htmlEl.setAttribute('data-theme',theme);
#   tmIcon.setAttribute('xlink:href', theme==='dark'? '#icon-moon' :'#icon-sun');
#   tmBtn.onclick = ()=>{
#     theme = theme==='dark'?'light':'dark';
#     localStorage.setItem('theme',theme);
#     htmlEl.setAttribute('data-theme',theme);
#     tmIcon.setAttribute('xlink:href',theme==='dark'? '#icon-moon':'#icon-sun');
#   };

#   // BUILDER
#   const fileInput = document.getElementById('fileInput'),
#         toStep2   = document.getElementById('toStep2'),
#         backBtn   = document.getElementById('back'),
#         runBtn    = document.getElementById('run'),
#         step1     = document.getElementById('step1'),
#         step2     = document.getElementById('step2'),
#         loader    = document.getElementById('loader'),
#         loaderText= document.getElementById('loaderText'),
#         jobUrl    = document.getElementById('jobUrl'),
#         builder   = document.querySelector('.builder');
#   let resumeText='';

#   fileInput.onchange = ()=> toStep2.disabled = !fileInput.files.length;

#   toStep2.onclick = async ()=>{
#     const f = fileInput.files[0]; if(!f)return;
#     step1.style.display='none';
#     loader.style.display='block'; loaderText.textContent='Extracting PDF…';
#     const form=new FormData(); form.append('pdf',f);
#     const res=await fetch('/api/extract',{method:'POST',body:form});
#     resumeText = (await res.json()).text || '';
#     loader.style.display='none'; step2.style.display='flex';
#   };

#   backBtn.onclick = ()=>{ step2.style.display='none'; step1.style.display='flex'; };

#   runBtn.onclick = async ()=>{
#     step2.style.display='none';
#     loader.style.display='block';
#     const statuses=['Analyzing…','Rewriting…']; let idx=0;
#     const iv=setInterval(()=>{
#       loaderText.textContent=statuses[idx];
#       idx=(idx+1)%statuses.length;
#     },1200);

#     const rendered = document.getElementById('rendered');
#     const area     = document.getElementById('outputArea');
#     try {
#       const resp = await fetch('/api/run',{
#         method:'POST',
#         headers:{'Content-Type':'application/json'},
#         body:JSON.stringify({ resume_text: resumeText, job_url: jobUrl.value })
#       });
#       const { output } = await resp.json();
#       area.value = output || '';
#       rendered.innerHTML = marked.parse(output || '');
#     } catch(e) {
#       area.value = 'Error: '+e.message;
#       rendered.textContent = area.value;
#     } finally {
#       clearInterval(iv);
#       loader.style.display='none';
#       builder.style.display='none';
#       document.getElementById('markdownWrapper').style.display='block';
#       document.querySelector('.toolbar').style.display='flex';
#       rendered.style.display='block';
#     }
#   };

#   // EDIT / COPY / DOWNLOAD
#   const editBtn     = document.getElementById('editBtn'),
#         copyBtn     = document.getElementById('copyBtn'),
#         downloadBtn = document.getElementById('downloadBtn'),
#         renderedOut = document.getElementById('rendered'),
#         outputArea  = document.getElementById('outputArea');

#   editBtn.onclick = ()=>{
#     if(outputArea.style.display==='block'){
#       outputArea.style.display='none';
#       renderedOut.style.display='block';
#       editBtn.textContent='Edit';
#     } else {
#       outputArea.style.display='block';
#       renderedOut.style.display='none';
#       editBtn.textContent='View';
#     }
#   };

#   copyBtn.onclick = ()=>{
#     const txt = outputArea.style.display==='block'
#       ? outputArea.value
#       : renderedOut.innerText;
#     navigator.clipboard.writeText(txt);
#   };

#   downloadBtn.onclick = async ()=>{
#     const md = outputArea.style.display==='block'
#       ? outputArea.value
#       : renderedOut.innerText;
#     const res = await fetch('/api/download-pdf',{
#       method:'POST',
#       headers:{'Content-Type':'application/json'},
#       body:JSON.stringify({ resume_markdown: md })
#     });
#     const blob = await res.blob();
#     const url  = URL.createObjectURL(blob);
#     const a    = document.createElement('a');
#     a.href     = url;
#     a.download = 'resume.pdf';
#     document.body.append(a);
#     a.click();
#     a.remove();
#     URL.revokeObjectURL(url);
#   };
# </script>
# </body>
# </html>
# """

# # --- ROUTES ---------------------------------------

# @app.route("/", methods=["GET"])
# def index():
#     return HTML_PAGE

# @app.route("/how-it-works")
# def how_it_works():
#     return render_template("how-it-works.html")

# @app.route("/agents")
# def agents():
#     return render_template("agents.html")

# @app.route("/use-cases")
# def use_cases():
#     return render_template("use-cases.html")

# @app.route("/developer-docs")
# def developer_docs():
#     return render_template("developer-docs.html")

# @app.route("/terms")
# def terms():
#     return render_template("terms.html")

# @app.route("/privacy")
# def privacy():
#     return render_template("privacy.html")

# @app.route("/api/extract", methods=["POST"])
# def extract_pdf():
#     f = request.files.get("pdf")
#     if not f:
#         return jsonify({"text": ""})
#     reader = PyPDF2.PdfReader(f)
#     text = [p.extract_text() or "" for p in reader.pages]
#     return jsonify({"text": "\n".join(text)})

# @app.route("/api/run", methods=["POST"])
# def api_run():
#     data = request.get_json() or {}
#     resume_text = data.get("resume_text", "")
#     job_url     = data.get("job_url", "")
#     crew = ResumeRewritingAgentsUsingJobDescriptionIntegrationCrew().crew()
#     result = crew.kickoff(inputs={"resume_text": resume_text, "job_url": job_url})
#     output = result if isinstance(result, str) else str(result)
#     return jsonify({"output": output.strip()})

# @app.route("/api/download-pdf", methods=["POST"])
# def download_pdf():
#     data = request.get_json() or {}
#     md   = data.get("resume_markdown", "")
#     buffer = io.BytesIO()
#     p = canvas.Canvas(buffer, pagesize=letter)
#     w,h = letter
#     textobj = p.beginText(40, h-40)
#     for line in md.split("\n"):
#         textobj.textLine(line)
#     p.drawText(textobj)
#     p.showPage(); p.save()
#     buffer.seek(0)
#     return send_file(
#         buffer,
#         as_attachment=True,
#         download_name="resume.pdf",
#         mimetype="application/pdf"
#     )

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

