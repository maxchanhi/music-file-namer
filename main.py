import os
import glob
import requests
import json
import re

# You'll need to fill these in
API_KEY = ""  # Replace with your Mistral API key
PDF_FOLDER = ""  # Change this to your folder path
COMPOSER = "Mozart"  # change according to this
TITLE = "Symphony No.40"  # change according to this

# Orchestral section numbering mapping
INSTRUMENT_PREFIXES = {
    # Scores
    "Full Score": "00",
    "Score": "00",
    "Conductor": "00",
    
    # Woodwinds (01-09)
    "Piccolo": "01",
    "Flute": "01",
    "Oboe": "02",
    "English Horn": "02",
    "Clarinet": "03",
    "Bass Clarinet": "03",
    "Bassoon": "04",
    "Contrabassoon": "04",
    "Saxophone": "05",
    
    # Brass (11-19)
    "Horn": "11",
    "Trumpet": "12",
    "Cornet": "12",
    "Trombone": "13",
    "Bass Trombone": "13",
    "Tuba": "14",
    "Euphonium": "14",
    
    # Percussion and other (21-29)
    "Timpani": "20",
    "Percussion": "21",
    "Harp": "22",
    "Piano": "23",
    "Celesta": "23",
    "Organ": "24",
    "Guitar": "25",
    "Mandolin": "25",
    # Add optional definitions
    # Strings (91-95)
    "Violin I": "91",
    "Violin II": "92",
    "Viola": "93",
    "Cello": "94",
    "Double Bass": "95",
}

def extract_instrument_from_filename(filename):
    """Extract the instrument name from the existing filename format."""
    
    # Extract the base filename without extension
    base_filename = os.path.basename(filename)
    name_without_ext = os.path.splitext(base_filename)[0]
    
    return identify_instrument_from_mistral(name_without_ext)

def identify_instrument_from_mistral(filename_text):
    """Use Mistral AI to identify the instrument part based on the filename text."""
    
    # Prepare the API request
    url = "https://api.mistral.ai/v1/chat/completions" #change if use different api
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    prompt = f"""
    Analyze the following music score filename and determine which musical instrument 
    part this is. Return only the name of the instrument or instrument section (e.g., "Violin 1", "Violin 2","Flute 1", "Horn 1","Horn 2" etc.). 
    If no instrument section is found, just return the name of the instrument
    Only return the instrument name in a word, not any other.
    Do not say any thinking process
    File Name: {filename_text}
    """
    
    data = {
        "model": "mistral-tiny",  # Using mistral-tiny - small, cheap and fast
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()
        instrument = result["choices"][0]["message"]["content"].strip()
        print(f"Found instrument:{instrument}")
        return instrument
    except Exception as e:
        print(f"Error calling Mistral API: {e}")
        print(f"Response: {response.text if 'response' in locals() else 'No response'}")
        return "Unknown"

def get_instrument_prefix(instrument):
    """Get the correct prefix for an instrument based on orchestral section."""
    
    # Check if this is a numbered instrument (like Violin 1, Horn 2, etc.)
    instrument_base = re.sub(r'\s+\d+$', '', instrument)
    instrument_number = ""
    
    number_match = re.search(r'\s+(\d+)$', instrument)
    if number_match:
        instrument_number = number_match.group(1)
    
    # Look for the base instrument in our prefix dictionary
    for key in INSTRUMENT_PREFIXES:
        if key in instrument_base:
            prefix = INSTRUMENT_PREFIXES[key]
            return f"{prefix}{instrument}"
    
    # If we can't find a match, return just the instrument name
    return instrument

def standardize_filenames():
    """Process all PDF files in the folder and standardize the naming format."""
    
    # Process all PDF files in the folder
    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    
    for pdf_path in pdf_files:
        # Get the current filename for logging
        current_filename = os.path.basename(pdf_path)
        print(f"Processing: {current_filename}")
        
        # Extract instrument part
        instrument = extract_instrument_from_filename(pdf_path)
        print(f"  Extracted instrument: {instrument}")
        
        # Get the correct prefix for this instrument
        prefixed_instrument = get_instrument_prefix(instrument)
        print(f"  Prefixed instrument: {prefixed_instrument}")
        
        # Create the standardized filename using the global variables
        new_filename = f"{COMPOSER} - {TITLE} - {prefixed_instrument}.pdf"
        new_path = os.path.join(os.path.dirname(pdf_path), new_filename)
        
        # Don't rename if the file would have the same name
        if pdf_path == new_path:
            print(f"  File already has the correct name: {current_filename}")
            continue
        
        # Don't rename if the destination file already exists
        if os.path.exists(new_path):
            print(f"  Cannot rename: destination file already exists: {new_filename}")
            continue
            
        # Rename the file
        try:
            os.rename(pdf_path, new_path)
            print(f"  Renamed to: {new_filename}")
        except Exception as e:
            print(f"  Error renaming file: {e}")

if __name__ == "__main__":
    # Make sure the folder exists
    if not os.path.exists(PDF_FOLDER):
        print(f"Folder {PDF_FOLDER} does not exist.")
    else:
        standardize_filenames()
