import base64
from openai import OpenAI

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = "/home/keithuncouth/Downloads/hwt_test3.jpeg"

# Getting the base64 string
base64_image = encode_image(image_path)

response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Perform OCR",
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{base64_image}"
          },
        },
      ],
    }
  ],
  temperature=0,
  top_p=1
)

ocr_output = response.choices[0].message.content
print("OCR Output:")
print(ocr_output)

def correct_text(ocr_text):
    prompt = (
        "Correct the grammar and punation mistakes sentence by sentence. Keep the corrections simple, use casual english, and retain the original sentences overall structure. avoid using semi-colons unless absolutly necessary"
        f"Text to correct:\n{ocr_text}"
    )
    correction_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        top_p=1
    )
    return correction_response.choices[0].message.content

# Correct the OCR output
corrected_text = correct_text(ocr_output)
print("\nCorrected Text:")
print(corrected_text)
