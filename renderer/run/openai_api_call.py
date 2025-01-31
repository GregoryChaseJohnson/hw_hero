import base64
import openai

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Perform OCR using OpenAI API
def perform_ocr(image_path):
    """
    Extract text from an image using OpenAI's GPT-4 vision capabilities.
    """
    base64_image = encode_image(image_path)

    response = openai.ChatCompletion.create(
        model="gpt-4-vision",  # Use the correct vision model
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the handwritten text from the image below."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=300
    )
    return response.choices[0].message["content"]

# Correct Text
def correct_text(ocr_text):
    """
    Correct the grammar and structure of OCR-generated text.
    """
    prompt = (
        f"Correct the following text for grammar and naturalness:\n\n{ocr_text}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=300
    )
    return response.choices[0].message["content"]
