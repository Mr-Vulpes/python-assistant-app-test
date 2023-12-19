import json
import requests
import os
# import sys
# sys.path.insert(0, 'pythonlibs\lib\python3.10\site-packages')
import openai
from openai import OpenAI
from prompts import assistant_instructions

OPENAI_API_KEY = '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'
AIRTABLE_API_KEY = 'Bearer patcuXJaBsA2eNxwO.b9008c7e67247ec5889a741b67ac4f3d3439e93598e8defd8040514b50f68a75'

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)


# Add lead to Airtable
def create_lead(name, phone):
  url = "https://api.airtable.com/v0/appYBGup8Lf9x9s9a/Leads%20Target"
  headers = {
      "Authorization": AIRTABLE_API_KEY,
      "Content-Type": "application/json"
  }
  data = {"records": [{"fields": {"Name": name, "Phone": phone}}]}
  response = requests.post(url, headers=headers, json=data)
  if response.status_code == 200:
    print("Lead created successfully.")
    return response.json()
  else:
    print(f"Failed to create lead: {response.text}")
    

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
                    "name": "create_lead",
                    "description":
                    "Capture lead details and save to Airtable.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Full name of the lead."
                            },
                            "phone": {
                                "type":
                                "string",
                                "description":
                                "Phone number of the lead including country code."
                            }
                        },
                        "required": ["name", "phone"]
                    }
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
