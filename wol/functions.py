import re
import requests
import gzip
import json
from io import BytesIO
from datetime import datetime
from flask import Blueprint, jsonify, request
from bs4 import BeautifulSoup

functions_bp = Blueprint('functions', __name__)

@functions_bp.route("/catalog", methods=['GET'], defaults={'language': 'E'})
@functions_bp.route("/catalog/<language>", methods=['GET'])
def catalog(language='E'):
    url = f"https://app.jw-cdn.org/catalogs/media/{language}.json.gz"
    response = requests.get(url)
    response.raise_for_status()
    
    with gzip.GzipFile(fileobj=BytesIO(response.content)) as gz:
        data = gz.read().decode('utf-8')

    items = [json.loads(item)['o']
             for item in data.splitlines()
             if json.loads(item)["type"] == "media-item"
             and json.loads(item).get('o', {}).get('keyParts', {}).get('formatCode') == 'VIDEO']

    return jsonify(items)

# Example GET: http://localhost:5000/mediaitems?languages=E,CHS&mediaItems=pub-iam-1_10_AUDIO,pub-jwb-080_9_VIDEO,pub-jwb-081_10_VIDEO,pub-jwb-081_11_VIDEO,pub-jwb-081_1_AUDIO,pub-jwb-081_1_VIDEO
# Example POST: {"languages": ["E", "CHS"], "mediaItems": ["pub-iam-1_10_AUDIO", "pub-jwb-080_9_VIDEO"}]}
@functions_bp.route("/mediaitems", methods=['POST', 'GET'])
def mediaitems():
    try:
        if request.method == 'POST':
            data = request.get_json()
            
        else:
            data = request.args

        lang_str = data.get('languages')
        media_str = data.get('mediaItems')
        languages = lang_str.split(',') if lang_str else ['E']
        mediaItems = media_str.split(',') if media_str else []

        final_response = process_media_items(languages, mediaItems)

        return jsonify(final_response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# Example GET: http://localhost:5000/mediaitem/E/pub-jwb-080_9_VIDEO
@app.route("/mediaitem/<language>/<mediaItem>", methods=['GET'])
def mediaitem(language, mediaItem):
    try:
        # If the route is /mediainfo/<language>/<mediaItem>
        languages = [str(language)]
        mediaItems = [str(mediaItem)]

        final_response = process_media_items(languages, mediaItems)

        return jsonify(final_response)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@functions_bp.route('/dailytext', methods=['GET', 'POST'])
def dailytext():
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

def process_media_items(languages, mediaItems):
    responses = []

    for language in languages:
        for mediaItem in mediaItems:
            url = f"https://b.jw-cdn.org/apis/mediator/v1/media-items/{language}/{mediaItem}?clientType=www"
            response = requests.get(url)
            response.raise_for_status()

                # Get the first image from the first image_type that has an image_size
            for image_type in ["lsr", "cvr", "sqr"]:
                images = response.json().get('media')[0].get('images').get(image_type)
                if images:
                    for image_size in ["xl", "lg", "md"]:
                        image_url = images.get(image_size)
                        if image_url:
                            image_url = image_url
                            break  # Stop after finding the first image
                    if image_url: 
                        break # Stop after finding an image in any image_type
                    else:
                        image_url = None
                        break

            largest_file = max([file for file in response.json().get('media')[0].get('files')], key=lambda f: f['filesize'])

                # Create the custom dictionary
            media_data = {
                    "title": response.json().get('media')[0].get('title'),
                    "primaryCategory": response.json().get('media')[0].get('primaryCategory'),
                    "mediaCitation": response.json().get('media')[0].get('printReferences')[0],
                    "languageAgnosticNaturalKey": response.json().get('media')[0].get('languageAgnosticNaturalKey'),
                    "firstPublished": response.json().get('media')[0].get('firstPublished'),
                    "type": response.json().get('media')[0].get('type'),
                    "duration": response.json().get('media')[0].get('duration'),
                    # "files": [
                    #     {
                    #         "filesize": file.get('filesize'),
                    #         "progressiveDownloadURL": file.get('progressiveDownloadURL'),
                    #         "subtitles": file.get('subtitles', {}).get('url')
                    #     } for file in response.json().get('media')[0].get('files')
                    # ], # Gets all files
                    "file": largest_file["progressiveDownloadURL"],
                    #"images": response.json().get('media')[0].get('images') # Gets all images
                }

                # Add subtitle field only if subtitles exist
            if largest_file.get('subtitles'):
                media_data["subtitle"] = largest_file.get('subtitles', {}).get('url')

                # Add image field only if image exist
            if image_url:
                media_data["image"] = image_url

            responses.append(media_data)
                
        # Create a list of dictionaries to represent the overall response
    final_response = []
    for lang in languages:
        lang_response = {
                "languageCode": lang,
                "media": [
                    media_data for media_data in responses
                ]
            }
        final_response.append(lang_response)

    return final_response
    
def process_daily_text(html_content):
    """Processes the daily text from the provided HTML content."""
   
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content)
    
    # Extract the date text from the first <h2> tag
    date_tag = soup.find('h2')  # This gets the first <h2> tag
    date_text = date_tag.get_text(strip=True) if date_tag else 'Not Found'

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
        'scriptureReference': scripture_text,
        'scriptureFull': themeScrp_text,
        'dailyText': bodyTxt_text
    }
    
    # Return the result as JSON
    return jsonify(result)
