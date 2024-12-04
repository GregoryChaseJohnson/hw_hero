import base64
from openai import OpenAI

client = OpenAI()

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to perform OCR on an image
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
    return response.choices[0].message.content  # Return the OCR text directly

# Function to correct text
def correct_text(ocr_text):
    prompt = (
        "Correct the grammar sentence by sentence correcting unnatural sentences. "
        "Keep the corrections simple, use casual English, and retain the original sentences' overall structure. "
        "Avoid using semi-colons unless absolutely necessary. Leave end-of-text partial or incomplete sentences as they are; do not make assumptions.\n\n"
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

# Example usage:
if __name__ == "__main__":
    # Define the image path
    image_path = "/home/keithuncouth/Downloads/hwt_9.jpg"

    # Step 1: Perform OCR
    print("Performing OCR...")
    ocr_output = perform_ocr(image_path)
    print("\nOCR Output:")
    print(ocr_output)

    # Step 2: Correct the text
    print("Correcting text...")
    corrected_text = correct_text(ocr_output)
    print("\nCorrected Text:")
    print(corrected_text)
