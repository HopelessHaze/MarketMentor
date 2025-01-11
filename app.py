# ==============================================================================
# app.py - Market Mentor: A Website for Walmart Suppliers
# ==============================================================================
import os
import time
import logging
from typing import Dict, List
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from functools import lru_cache
from hashlib import md5
import re
import string

# ==============================================================================
# 1. Configuration and Setup
# ==============================================================================

# Load environment variables and setup logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
app = Flask(__name__)

@app.route('/public/<path:filename>')
def serve_public(filename):
    return send_from_directory('public', filename)

# Environment variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_DIF_API_KEY = os.getenv("OPENROUTER_DIF_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
CUSTOM_SEARCH_ENGINE_ID = os.getenv("CUSTOM_SEARCH_ENGINE_ID")
YDC_API_KEY = os.getenv("YDC_API_KEY")

# Confirm environment variables loading
for var in ['OPENROUTER_API_KEY', 'OPENROUTER_DIF_API_KEY',
            'GOOGLE_API_KEY', 'CUSTOM_SEARCH_ENGINE_ID', 'YDC_API_KEY']:
    if not os.getenv(var):
        logging.error(f"{var} is missing or not loaded correctly.")
    else:
        logging.info(f"{var} loaded successfully.")

# Validate environment variables
if not all([OPENROUTER_API_KEY, GOOGLE_API_KEY, CUSTOM_SEARCH_ENGINE_ID, YDC_API_KEY]):
    logging.error("One or more required API keys are missing. Please check your environment variables.")
    raise ValueError("Missing required API keys")

# ==============================================================================
# 2. Utility Functions
# ==============================================================================

def hardcoded_walmart_check(question: str) -> bool:
    """
    Perform a quick, hardcoded relevance check to determine if the question
    is likely related to Walmart suppliers, Walmart's processes, or
    selling products through Walmart. 
    """
    question_normalized = question.lower().translate(str.maketrans('', '', string.punctuation))

    # Expanded list of keywords and phrases related to Walmart suppliers & processes
    walmart_keywords = [
        r"\bwalmart\b", r"\bsam['s]? club\b", r"\bwalmart connect\b", r"\bretail link\b", r"\bsupplier center\b",
        r"\bwalmart supplier portal\b", r"\bmodular\b", r"\bin-store merchandising\b",
        r"\bsupplier agreement\b", r"\bwalmart terms\b", r"\bstore planning\b", r"\bon-time in full\b",
        r"\botif\b", r"\bsustainability\b", r"\bcompliance\b", r"\belectronic product code\b",
        r"\bepc\b", r"\bpackaging\b", r"\bshipping\b", r"\bwarehouse\b", r"\bdelivery\b",
        r"\bdistribution center\b", r"\bsupplier security\b", r"\bglobal supplier\b", r"\bedi\b",
        r"\binvoice\b", r"\bupc\b", r"\bbarcode\b", r"\blabeling\b", r"\bfreight\b",
        r"\bcollect-ready\b", r"\bmust arrive by date\b", r"\bmabd\b", r"\binventory management\b",
        r"\bforecasting\b", r"\breplenishment\b", r"\bgeneral merchandise\b", r"\bproduct listing\b",
        r"\bexecution requirements\b", r"\boms\b", r"\blogistics\b", r"\bvendor agreement\b",
        r"\bonline marketplace\b", r"\bthird-party marketplace\b", r"\bwalmart marketplace\b",
        r"\bvba\b", r"\bsupplier compliance\b", r"\bsuppliers?\b", r"\bsupply chain\b", r"\bmerchandise\b",
        r"\bpurchase order\b", r"\bpo\b", r"\bcase pack\b", r"\bmaster pack\b", r"\bpackaging specification\b",
        r"\bitem file\b", r"\breceiving\b", r"\bcarrier\b", r"\bpayables\b", r"\bvpn\b",
        r"\bnew item setup\b", r"\bmod creation\b", r"\bmod changes\b", r"\brack and stack\b",
        r"\bshelf management\b", r"\bmarket manager\b", r"\baccount manager\b", r"\bin-store compliance\b",
        r"\bin-store standards\b", r"\bhazardous materials\b", r"\bhazmat\b", r"\bstorm compliance\b",
        r"\brfid\b", r"\bgs1\b", r"\bglobal data synchronization network\b", r"\bgdsn\b",
        r"\bdata sync\b", r"\bretail industry\b", r"\bclub channel\b", r"\bprivate label\b",
        r"\bgreat value\b", r"\bbrand guidelines\b", r"\bpackaging design\b", r"\bexecution tracking\b",
        r"\breturns policy\b", r"\bwalmart store returns\b", r"\bstore claims\b", r"\bdispute resolution\b",
        r"\bvendor compliance\b", r"\bmonetary fines\b", r"\bchargebacks\b", r"\broot cause\b",
        r"\bglobal compliance\b", r"\bproduct safety\b", r"\bfood safety\b", r"\bbakery supplier\b",
        r"\bproduce supplier\b", r"\bmeat supplier\b", r"\bconsumables supplier\b", r"\bhealth and wellness supplier\b",
        r"\bonline grocery\b", r"\bclick and collect\b", r"\bpickup tower\b", r"\bdrone delivery\b",
        r"\bjet.com\b", r"\bfulfillment\b", r"\bwalmart fulfillment services\b", r"\breturns center\b",
        r"\bapparel supplier\b", r"\belectronics supplier\b", r"\btoy supplier\b", r"\bimport requirements\b",
        r"\btariffs\b", r"\bharmonized tariff schedule\b", r"\bhs code\b", r"\bcountry of origin\b",
        r"\blead time\b", r"\bmodule changes\b", r"\bexecution guide\b", r"\bcompliance guide\b",
        r"\bcorporate compliance\b", r"\bcorporate responsibility\b", r"\bethics\b", r"\bconduct\b",
        r"\binvoice matching\b", r"\baccounts payable\b", r"\bremittance\b", r"\bbilling disputes\b",
        r"\bremittance advice\b", r"\bpayment terms\b", r"\bsam's club suppliers?\b",
        r"\bselling at walmart\b", r"\bproduct onboarding\b", r"\bproduct compliance\b",
        r"\bonline item file\b", r"\bproduct development\b", r"\bwalmart labs\b", r"\bmerchandising portal\b"
    ]

    for keyword in walmart_keywords:
        if re.search(keyword, question_normalized):
            logging.info(f"Hardcoded Walmart relevance check passed for keyword: {keyword}")
            return True

    logging.info("Hardcoded Walmart relevance check failed.")
    return False


def is_walmart_supplier_related(question: str, snippets: str) -> bool:
    """
    Use GPT-4o to determine if a question is related to Walmart supplier issues,
    Walmart processes, or Walmart-specific retail topics by checking provided snippets.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_DIF_API_KEY}",
        "HTTP-Referer": "https://marketmentor.com",  # Optional for analytics
        "X-Title": "Market Mentor",                  # Optional for display
        "Content-Type": "application/json"
    }
    
    system_message = """You are an expert consultant in Walmart’s supplier processes, retail operations, and corporate policies. Your task is to determine whether a question (and its accompanying snippets) is related to Walmart suppliers, Walmart's selling processes, or corporate requirements.

Relevant topics include:
- Supplier onboarding, contracts, compliance
- Walmart store processes, shipping and packaging guidelines
- Walmart Marketplace policies, brand guidelines
- Corporate sustainability, legal, and ethical requirements
- Inventory management, OTIF (on-time in-full), distribution, supply chain

Respond with 'true' if any snippet suggests the question is about Walmart supplier or selling processes; otherwise respond 'false'."""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Is this question related to Walmart suppliers or retail processes considering these snippets? Question: {question} Snippets: {snippets}"}
    ]

    payload = {
        "model": "openai/gpt-4o",
        "messages": messages,
        "temperature": 0.1,
        "top_p": 1,
        "max_tokens": 50
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        if content.lower().startswith('true'):
            decision = True
            explanation = content[4:].strip()
        elif content.lower().startswith('false'):
            decision = False
            explanation = content[5:].strip()
        else:
            decision = False
            explanation = "Unexpected response format from API."

        logging.info(f"AI-based Walmart relevance check decision: {decision}, Explanation: {explanation}")
        return decision
    except Exception as e:
        logging.error(f"Error in Walmart relevancy check: {e}")
        return False


def count_distinct_options(question: str, pattern: str) -> int:
    matches = re.findall(pattern, question, re.IGNORECASE)
    return len(set(matches))

@lru_cache(maxsize=1000)
def get_cached_walmart_relevancy_check(question: str, snippets: str) -> bool:
    """Cached version of the Walmart relevancy check."""
    return is_walmart_supplier_related(question, snippets)

def check_relevancy_with_cache(question: str, snippets: str) -> bool:
    """Interface for cached relevancy check."""
    question_normalized = question.lower().strip()
    question_hash = md5(question_normalized.encode()).hexdigest()
    return get_cached_walmart_relevancy_check(question, snippets)

# ==============================================================================
# 3. API Integration Functions
# ==============================================================================

def perform_web_search(query, time_restricted=False, num_results=10):
    """
    Perform a Google search (STANDARD).
    Used to gather Walmart-specific knowledge from general web results.
    """
    logging.info(f"\n{'='*80}\nPERFORMING GOOGLE SEARCH (STANDARD)\n{'='*80}")
    logging.info(f"Query: {query}")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CUSTOM_SEARCH_ENGINE_ID,
        "q": query,
        "num": num_results,
        "gl": "us",
        "lr": "lang_en"
    }

    if time_restricted:
        params["dateRestrict"] = "d365"
        params["sort"] = "date"

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_data = response.json()

        results = []
        for item in search_data.get("items", []):
            results.append(
                f"Title: {item.get('title', 'No Title')}\n"
                f"URL: {item.get('link', 'No Link')}\n"
                f"Snippet: {item.get('snippet', 'No Snippet')}"
            )

        final_results = "\n\n".join(results) if results else "No relevant search results found."

        if results:
            logging.info(f"Google search completed, found {len(results)} results.")
        else:
            logging.info("No relevant search results found from Google search.")

        return final_results
    except Exception as e:
        logging.error(f"Error in web search: {e}")
        return f"(Error: {str(e)})"


def perform_you_search(query, num_results=15):
    """
    Perform search using the You.com API for Walmart-related questions.
    """
    logging.info(f"\n{'='*80}\nPERFORMING YOU.COM SEARCH\n{'='*80}")
    logging.info(f"Search query: {query}")

    headers = {
        "X-API-Key": YDC_API_KEY
    }

    params = {
        "query": query,
        "num_web_results": min(num_results, 20),
        "safesearch": "moderate",
        "country": "US"
    }

    try:
        response = requests.get(
            "https://api.ydc-index.io/search",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        data = response.json()

        results = []
        for hit in data.get('hits', [])[:num_results]:
            combined_snippets = ' '.join(hit.get('snippets', []))
            description = hit.get('description', 'No Description')

            results.append(
                f"Title: {hit.get('title', 'No Title')}\n"
                f"URL: {hit.get('url', 'No URL')}\n"
                f"Description: {description}\n"
                f"Snippet: {combined_snippets}"
            )

        final_results = "\n\n".join(results) if results else "No relevant You.com search results found."

        if results:
            logging.info(f"You.com search completed, found {len(results)} results.")
        else:
            logging.info("No relevant You.com search results found.")

        return final_results
    except Exception as e:
        error_msg = f"Error in You.com search: {e}"
        logging.error(error_msg)
        return f"(Error: {str(e)})"


def create_system_prompt(context_combined):
    """
    Create system prompt with essential requirements for Walmart supplier Q&A.
    We only cite official Walmart documents if relevant in the provided context.
    The style is an enthusiastic consultant well-versed in Walmart corporate requirements.
    """
    base_prompt = f"""You are Market Mentor, an enthusiastic consultant intimately familiar with Walmart’s corporate requirements, supplier processes, and best practices. You provide thorough, accurate, and helpful answers about how to sell products at Walmart, navigate supplier systems, and comply with corporate policies.

**RESPONSE REQUIREMENTS:**

1. **Length & Depth**:
   - Your responses should be substantial (detailed and thorough). Aim for at least 800 words but not exceeding 1200 words. (If the question is extremely brief, you may scale down slightly.)
   - Provide deep analysis, as you are a consultant excited to help.

2. **Voice & Tone**:
   - Sound like an experienced Walmart corporate consultant: warm, professional, and excited to assist.

3. **Content Approach**:
   - Provide clear, step-by-step guidance related to Walmart processes.
   - Address potential pitfalls or compliance concerns.
   - Write in well-structured paragraphs (avoid bullet lists).

4. **Citations**:
   - **Only cite official Walmart documents** or pages if they appear in your context. (No third-party or extraneous citations.)
   - If no official Walmart documents are provided in the context, mention that official references are recommended but not available in the data you have.
   - Use the format: 
     **Citations**
     [1] [Document Title], available at [URL]
     - Number citations in bracket form outside the punctuation.

5. **Structure**:
   - Begin with a strong, direct introduction that conveys expertise.
   - Use **bold** headings for major sections, each at least four sentences.
   - End with a concise concluding paragraph that summarizes next steps or final advice.

6. **No Plagiarism**:
   - Synthesize context, do not copy verbatim.

7. **Focus**:
   - Always relate your answer to Walmart’s supplier processes, compliance, and corporate requirements.

Here is your CONTEXT:

{context_combined}

When you answer, incorporate relevant context from the searches if it helps. 
If no official Walmart sources are present in the context, you may reference the general idea of official Walmart documentation without inventing specific titles or URLs.
"""
    return base_prompt


def query_claude_with_context(question: str, context: str) -> str:
    """
    Query the AI model with the constructed prompt and user question.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    base_system_prompt = create_system_prompt(context)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://marketmentor.com",
        "X-Title": "Market Mentor",
        "Content-Type": "application/json"
    }

    messages = [
        {"role": "system", "content": base_system_prompt},
        {"role": "user", "content": question}
    ]

    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": messages,
        "temperature": 0.7,
        "top_p": 1,
        "repetition_penalty": 1.0,
        "max_tokens": 30000,
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        response_json = response.json()
        content = response_json['choices'][0]['message']['content']

        logging.info(f"\n{'='*80}\nAI RESPONSE GENERATED\n{'='*80}")
        logging.info(content)

        # Optional: Log usage stats
        system_prompt_length = len(base_system_prompt)
        context_length = len(context)
        question_length = len(question)
        content_length = len(content)
        logging.info(f"System Prompt Length: {system_prompt_length}")
        logging.info(f"Context Length: {context_length}")
        logging.info(f"Question Length: {question_length}")
        logging.info(f"Response Length: {content_length}")

        return content

    except Exception as e:
        logging.error(f"Error in AI response generation: {str(e)}")
        return "An error occurred while generating the response. Please try again."


def generate_humorous_rejection(question: str) -> str:
    """
    Generate a witty but professional rejection message if a question
    is not related to Walmart supplier or corporate processes.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://marketmentor.com",
        "X-Title": "Market Mentor",
        "Content-Type": "application/json"
    }
    
    system_message = """You are Market Mentor, a Walmart-focused consultant AI with a friendly, witty style.
You can only answer questions about Walmart suppliers, processes, or corporate policies.

Craft a short, playful rejection (2-3 sentences) that:
1) Declines the user's unrelated question.
2) Lightly connects it to Walmart or retail in a humorous way.
3) Encourages them to ask about Walmart processes or supplier info instead.
4) Does not apologize or mention other AI. 
"""

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Create a brief, witty rejection for this unrelated question: {question}"}
    ]
    
    payload = {
        "model": "anthropic/claude-3.5-sonnet",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 150,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        rejection_message = response.json()["choices"][0]["message"]["content"].strip()
        
        logging.info("Humorous rejection generated successfully.")
        return rejection_message
    except Exception as e:
        logging.error(f"Error generating humorous rejection: {e}")
        return (
            "I'm Market Mentor, your friendly Walmart supplier guru. "
            "I only handle Walmart-related inquiries. Perhaps you'd like to talk about "
            "product setup, shipping, or compliance? I'm here whenever you're ready!"
        )

# ==============================================================================
# 4. Core Logic
# ==============================================================================

def process_question(question: str) -> str:
    """
    Process the user's question:
      1. Check if it's related to Walmart supplier or corporate processes 
         via a hardcoded check or AI-based check.
      2. If yes, gather context from You.com and Google (standard).
      3. Summarize and craft a thorough AI answer in the voice of a Walmart consultant.
      4. If not related, provide a playful rejection message.
    """
    logging.info(f"\n{'='*80}\nPROCESSING NEW QUESTION: '{question}'\n{'='*80}")

    # Step 1: Perform hardcoded Walmart relevance check
    if hardcoded_walmart_check(question):
        logging.info("✓ Hardcoded Walmart relevance check passed.")
    else:
        logging.info("Hardcoded Walmart relevance check failed. Performing AI-based check.")
        # Perform AI-based relevance check with a limited snippet from You.com
        snippets = perform_you_search(question, num_results=5)
        is_related = is_walmart_supplier_related(question, snippets)
        if not is_related:
            logging.info("AI-based Walmart relevance check failed. Generating humorous rejection.")
            return generate_humorous_rejection(question)
        else:
            logging.info("AI-based Walmart relevance check passed.")

    # Step 2: Gather context from You.com and Google
    try:
        logging.info(f"\n{'='*80}\nGATHERING INFORMATION FROM SOURCES\n{'='*80}")
        you_results = perform_you_search(f"In the context of Walmart suppliers: {question}")
        google_results = perform_web_search(f"In the context of Walmart suppliers: {question}", time_restricted=False)

        logging.info("Searches completed from You.com and Google.")

        # Combine contexts
        contexts = [
            ("YOU.COM SEARCH RESULTS", you_results),
            ("GOOGLE SEARCH RESULTS (STANDARD)", google_results),
        ]

        combined_context = "\n\n".join([
            f"{'='*80}\n{title}\n{'='*80}\n{content}" 
            for title, content in contexts
        ])

        # Step 3: Generate final answer
        logging.info(f"\n{'='*80}\nGENERATING FINAL RESPONSE\n{'='*80}")
        response = query_claude_with_context(question, combined_context)
        logging.info("Final AI response generated successfully.")

        return response

    except Exception as e:
        logging.error(f"Error processing question: {e}")
        return f"An error occurred while processing your question: {str(e)}"


# ==============================================================================
# 5. Flask Routes
# ==============================================================================

@app.route('/')
def home():
    # Render the updated index.html for Market Mentor
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_question():
    """
    Primary endpoint for handling user questions.
    Expects JSON payload: {"question": "..."}
    """
    try:
        user_question = request.json.get("question")
        if not user_question or not user_question.strip():
            return jsonify({'response': 'Please provide a valid question.'})

        response = process_question(user_question)
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in ask_question route: {e}")
        return jsonify({'response': f'An error occurred: {str(e)})'})

@app.route('/terms')
def terms():
    # Optional: update Terms of Service references if you have a custom file
    try:
        with open('mentor_tos.txt', 'r', encoding='utf-8') as file:
            terms_content = file.read()
        return render_template('legal.html', content=terms_content, title='Market Mentor - Terms of Service')
    except Exception as e:
        logging.error(f"Error loading terms: {e}")
        return "Error loading Terms of Service", 500

@app.route('/privacy')
def privacy():
    # Optional: update Privacy Policy references if you have a custom file
    try:
        with open('mentor_privacy.txt', 'r', encoding='utf-8') as file:
            privacy_content = file.read()
        return render_template('legal.html', content=privacy_content, title='Market Mentor - Privacy Policy')
    except Exception as e:
        logging.error(f"Error loading privacy policy: {e}")
        return "Error loading Privacy Policy", 500

if __name__ == '__main__':
    app.run(debug=True)