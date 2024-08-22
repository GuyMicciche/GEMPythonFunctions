import re
import requests
from datetime import datetime
from flask import Blueprint, jsonify, request
from bs4 import BeautifulSoup

functions_bp = Blueprint('functions', __name__)

@functions_bp.route('/daily-text', methods=['GET', 'POST'])
def daily_text():
    """Handles both GET and POST requests to retrieve and process daily text."""
    
    if request.method == 'POST':
        # Handle the POST request where HTML content is provided in the request body
        data = request.get_json()
        html_input = data.get('html', None)
        
        if not html_input:
            return jsonify({"error": "No HTML content provided"}), 400
    
    elif request.method == 'GET':
        # Handle the GET request by fetching the HTML content from the WOL site
        today = datetime.today()
        url_date = today.strftime("%Y/%m/%d")
        url = f"https://wol.jw.org/en/wol/dt/r1/lp-e/{url_date}"
        
        # Send an HTTP GET request to the URL
        response = requests.get(url)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            html_input = response.text
        else:
            return jsonify({"error": "Failed to retrieve the page from the URL"}), 500
    
    # Process the HTML content
    return process_daily_text(html_input)

def process_daily_text(html_content):
    """Processes the daily text from the provided HTML content."""
   
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content)
    
    # Extract the date text from the first <h2> tag
    date_tag = soup.find('h2')  # This gets the first <h2> tag
    date_text = h2_tag.get_text(strip=True) if h2_tag else 'Not Found'

    # Extract the theme scripture text from the <p> tag with class "themeScrp"
    themeScrp_tag = soup.find('p', class_='themeScrp')
    themeScrp_text = themeScrp_tag.get_text(strip=True) if themeScrp_tag else 'Not Found'

    # Extract the main body text from the <div> tag with class "bodyTxt"
    bodyTxt_div = soup.find('div', class_='bodyTxt')
    bodyTxt_text = bodyTxt_div.get_text(strip=True) if bodyTxt_div else 'Not Found'

    # Extracting scripture reference from themeScrp_text based on pattern
    scripture_match = re.search(r'—(.*? \d+:\d+)', themeScrp_text)
    scripture_text = scripture_match.group(1) if scripture_match else 'Not Found'
    
    # Prepare the result
    result = {
        'dateText': date_text,
        'scriptureFull': themeScrp_text,
        'scriptureReference': scripture_text,
        'dailyText': bodyTxt_text
    }
    
    # Return the result as JSON
    return jsonify(result)
