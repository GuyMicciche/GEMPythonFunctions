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
    # Get the current date
    today = datetime.today()
    
    # Format the date to match the "data-date" attribute in the HTML
    formatted_date = today.strftime('%Y-%m-%dT00:00:00.000Z')
    
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content)
    
    # Determine the index for "today"
    day = 1  # Index 1 for today in the list of daily texts
    
    # Find the h2 tags and get the appropriate one based on 'day'
    h2_tags = soup.find_all('h2')
    h2_text = h2_tags[day].get_text(strip=True) if len(h2_tags) > day else 'Not Found'
    
    # Find the p tags with the class "themeScrp"
    themeScrp_tags = soup.find_all('p', class_='themeScrp')
    themeScrp_text = themeScrp_tags[day].get_text(strip=True) if len(themeScrp_tags) > day else 'Not Found'
    
    # Find the div tag with the appropriate data-date based on the formatted_date
    tabContent_div = soup.find('div', attrs={"data-date": formatted_date})
    tabContent_text = tabContent_div.get_text(strip=True) if tabContent_div else 'Not Found'
    
    # Extracting scripture from themeScrp_text based on pattern
    scripture_match = re.search(r'—(.*? \d+:\d+)', themeScrp_text)
    scripture_text = scripture_match.group(1) if scripture_match else 'Not Found'
    
    # Prepare the result
    result = {
        'dateText': h2_text,
        'scriptureFull': themeScrp_text,
        'scriptureReference': scripture_text,
        'dailyText': tabContent_text
    }
    
    # Return the result as JSON
    return jsonify(result)
