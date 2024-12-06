import base64
from openai import OpenAI

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    
#image_path = "/home/keithuncouth/Downloads/hwt_9.jpeg"
def perform_ocr(image_path):
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract the handwritten text from the image below. Do not include any additional information, labels, or formatting. Provide only the plain text content.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        temperature=0,
        top_p=1
    )
    return response.choices[0].message.content # Return the OCR text directly

# Function to correct text
def correct_text(ocr_text):
    prompt = (
        "Please correct each sentence for grammar and naturalness while maintaining the original intent and overall structure. Keep corrections simple and use casual English. Avoid using semicolons unless absolutely necessary. Do not alter or complete partial or incomplete sentences at the end of the text; leave them as they are without making assumptions."
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
    return correction_response.choices[0].message.content  # Return the corrected text directly
