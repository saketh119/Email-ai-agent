import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Use latest flash model
model = genai.GenerativeModel("gemini-flash-latest")


def process_email_with_gemini(prompt_text: str, email_text: str):
    """
    Processes email using Gemini:
    - Categorizes the email
    - Generates a professional reply
    Returns: category, reply, tokens_used
    """

    # Structured prompt
    full_prompt = f"""
{prompt_text}

Email:
{email_text}

Instructions:
Return output in EXACT format:

Category: <one of Work, Personal, Finance, Spam, Other>
Reply: <professional reply only>
"""

    # Call Gemini
    response = model.generate_content(full_prompt)
    output_text = response.text

    # Default values
    category = "Other"
    reply = output_text

    # Parse structured output
    if output_text and "Category:" in output_text and "Reply:" in output_text:
        parts = output_text.split("Reply:")
        category_part = parts[0]
        reply_part = parts[1]

        category = category_part.replace("Category:", "").strip()
        reply = reply_part.strip()

    # Estimate tokens (Gemini free tier doesn't return usage)
    tokens_used = len(full_prompt.split()) + len(reply.split())

    return category, reply, tokens_used
