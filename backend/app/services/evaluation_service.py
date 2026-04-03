import os
import json
import mimetypes
import openai
import pandas as pd
from PyPDF2 import PdfReader
from PIL import Image
import docx

openai.api_key = os.getenv("OPENAI_API_KEY")

def evaluate_submission(file_path: str = None, remark: str = None, task=None) -> dict:
    """
    Evaluate a submission using OpenAI with dynamic prompts based on file/task type.
    Returns JSON: {score: int, feedback: str, details: {...}}
    """
    task_desc = task.description if task else "No description provided"
    task_type = getattr(task, "type", None) 
    content_summary = ""
    if file_path:
        mime_type, _ = mimetypes.guess_type(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in [".txt", ".md"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content_summary = f.read()
                task_type = task_type or "text"
            elif ext in [".py", ".java", ".js", ".cpp"]:
                with open(file_path, "r", encoding="utf-8") as f:
                    content_summary = f.read()
                task_type = task_type or "code"
            elif ext in [".xlsx", ".csv"]:
                df = pd.read_excel(file_path) if ext == ".xlsx" else pd.read_csv(file_path)
                content_summary = df.head(10).to_json()
                task_type = task_type or "excel"
            elif ext in [".pdf"]:
                reader = PdfReader(file_path)
                content_summary = " ".join([page.extract_text() or "" for page in reader.pages[:5]])
                task_type = task_type or "text"
            elif ext in [".docx"]:
                doc = docx.Document(file_path)
                content_summary = " ".join([p.text for p in doc.paragraphs[:10]])
                task_type = task_type or "text"
            elif ext in [".png", ".jpg", ".jpeg"]:
                img = Image.open(file_path)
                content_summary = f"Image of size {img.size}, mode {img.mode}"
                task_type = task_type or "image"
            else:
                content_summary = "File type not specifically handled, content ignored."
                task_type = task_type or "generic"
        except Exception as e:
            content_summary = f"Could not read file: {str(e)}"

    
    combined_content = ""
    if content_summary and remark:
        combined_content = f"Task Description: {task_desc}\n\nUser Remark: {remark}\n\nFile Content: {content_summary}"
    elif content_summary:
        combined_content = f"Task Description: {task_desc}\n\nFile Content: {content_summary}"
    elif remark:
        combined_content = f"Task Description: {task_desc}\n\nUser Remark: {remark}"
    else:
        combined_content = f"Task Description: {task_desc}\n\nNo content submitted."

   
    if task_type in ["code"]:
        prompt_instructions = """
        You are a programming mentor.
        Evaluate the code submission for correctness, syntax, runtime issues, and best practices.
        Provide a score 0-100 and constructive feedback.
        """
    elif task_type in ["excel", "data", "finance"]:
        prompt_instructions = """
        You are a data analyst reviewing a spreadsheet.
        Check formulas, calculations, data analysis accuracy, and clarity.
        Provide a score 0-100 and feedback.
        """
    elif task_type in ["text", "essay", "pdf", "docx"]:
        prompt_instructions = """
        You are an expert teacher reviewing written work.
        Evaluate correctness, clarity, completeness, grammar, and logical flow.
        Provide a score 0-100 and feedback.
        """
    elif task_type in ["image", "uiux", "design"]:
        prompt_instructions = """
        You are a design reviewer.
        Evaluate visual aesthetics, usability, and task requirement fulfillment.
        Provide a score 0-100 and constructive feedback.
        """
    else:
        prompt_instructions = """
        You are an AI evaluator.
        Evaluate if the submission fulfills the task and give constructive feedback.
        Score 0-100.
        """

    
    prompt = f"""
    {prompt_instructions}
    Task Description: {task_desc}
    Submission Content: {combined_content}

    Instructions:
    1. Evaluate completion and quality.
    2. Give a score 0-100.
    3. Provide **detailed feedback** including:
       - Types of errors (syntax, logic, formatting, conceptual)
       - Suggestions for improvement
       - Tips for doing better next time
       - References (books, documentation, online resources)
       - Theory or conceptual explanation related to the answer
    4. Output strictly in JSON format:
    {{
        "score": int,
        "feedback": str,
        "errors": list,
        "suggestions": list,
        "tips": list,
        "references": list,
        "theory": str
    }}
    """
   
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        result_text = response.choices[0].message.content.strip()
        result = json.loads(result_text)
    except Exception as e:
        result = {
            "score": 0,
            "feedback": f"AI evaluation failed: {str(e)}",
            "errors": [],
            "suggestions": [],
            "tips": [],
            "references": [],
            "theory": combined_content
        }

    return result
