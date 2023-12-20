import json
import requests
import os
from openai import OpenAI
from prompts import assistant_instructions
from datetime import datetime, timedelta, timezone
import pytz
OPENAI_API_KEY = "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"

# Current time in UTC
now_utc = datetime.utcnow()



def get_current_time_in_iso_format(hours_to_add=0, days_to_add=0):
    # Set timezone to Central European Time (CET)
    cet_timezone = pytz.timezone('CET')

    # Get current time in CET timezone
    current_time_cet = datetime.now(cet_timezone)

    # Add hours and days if specified
    modified_time = current_time_cet + timedelta(hours=hours_to_add, days=days_to_add)

    # Format the time in ISO 8601 format and replace timezone info with 'CET'
    return modified_time.replace(tzinfo=None).isoformat() + 'CET'



# CET is UTC+1
cet_timezone = timezone(timedelta(hours=1))
now_cet = now_utc.replace(tzinfo=timezone.utc).astimezone(cet_timezone)

# Format to ISO 8601
iso_time_cet = now_cet.isoformat()

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r
 
# Check for avaliable time
def check_for_avliable_date():
  current_time_iso = get_current_time_in_iso_format(hours_to_add=5, days_to_add=0)
  time_with_shift = get_current_time_in_iso_format(hours_to_add=5, days_to_add=3)

  url = "https://api.calendly.com/event_type_available_times"
  data = {"event_type": "https://api.calendly.com/event_types/8157fe5d-a3bb-4594-bfa1-ec90aa524f3d", "start_time": current_time_iso, "end_time": time_with_shift}
  response = requests.get(url, auth=BearerAuth('eyJraWQiOiIxY2UxZTEzNjE3ZGNmNzY2YjNjZWJjY2Y4ZGM1YmFmYThhNjVlNjg0MDIzZjdjMzJiZTgzNDliMjM4MDEzNWI0IiwidHlwIjoiUEFUIiwiYWxnIjoiRVMyNTYifQ.eyJpc3MiOiJodHRwczovL2F1dGguY2FsZW5kbHkuY29tIiwiaWF0IjoxNzAyMDgyNjU5LCJqdGkiOiI1MmJkYjJlYi01MmMyLTRjYTAtYTcwMC0zZWViZmM2YTM5ZDciLCJ1c2VyX3V1aWQiOiIwYTc5ZjVhYi04OGE3LTRiZjYtOGEzYS0yOWIxMDE3NDhkYzkifQ.MA2DI9c9GK7PweH12__Am_NAgu8JhnK5fkhj2W4rn3ZDA_AXvz5oeuuTTPSdPzC9ewZewdR0gwvnz80wsHBYYA'), json=data)
  if response.status_code == 200:
    print("Time checked succesfully.")
    post_response_json = response.json()
    print(post_response_json)
    return response.json()
  else:
    print(f"Failed to check time: {response.text}")
    print(current_time_iso)
    print(time_with_shift)
    

# Create or load assistant
def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    # To change the knowledge document, modify the file name below to match your document
    # If you want to add multiple files, paste this function into ChatGPT and ask for it to add support for multiple files
    file = client.files.create(file=open("knowledge.docx", "rb"),
                               purpose='assistants')

    assistant = client.beta.assistants.create(
        # Change prompting in prompts.py file
        instructions=assistant_instructions,
        model="gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
            {
                "type": "function",  # This adds the lead capture as a tool
                "function": {
                    "name": "check_for_avliable_date",
                    "description":
                    "Check for avliable dates on Calendly and propose to the client"
                }
            }
        ],
        file_ids=[file.id])

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id
