import openai
import os
from correction_service import get_correction_explanation

openai.api_key = os.getenv("OPENAI_API_KEY")

# --- STEP 2: Explanation ---
def build_replacement_prompt(before_text, after_text, full_sentence):
    """
    Build a prompt for a replacement change including the full corrected sentence.
    """
    base_prompt = (
        f"Sentence: \"{full_sentence}\"\n\n"
        f"Before: \"{before_text}\"\n"
        f"After: \"{after_text}\"\n\n"
    )
    instructions = (
        "In a short and consice way tell me what was wrong and what is now right. Identify the specific word(s) that were changed and explain why the new word(s) fit better with the context of the sentence."
    )
    return base_prompt + instructions


def build_deletion_prompt(original_snippet, corrected_snippet, full_corrected_sentence):
    """
    Build a prompt for a DELETION change including the full corrected sentence.
    """
    base_prompt = (
        f"Full corrected sentence: \"{full_corrected_sentence}\"\n\n"
        f"Original snippet: \"{original_snippet}\"\n"
        f"Deleted text: \"{corrected_snippet}\"\n\n"
    )
    instructions = (
        "In one or two sentences, explain in simple terms how removing this text improves the sentence. "
        "Focus on the clarity and natural flow of the full sentence."
    )
    return base_prompt + instructions

def build_insertion_prompt(original_snippet, corrected_snippet, full_corrected_sentence):
    """
    Build a prompt for an INSERTION change including the full corrected sentence.
    """
    base_prompt = (
        f"Full corrected sentence: \"{full_corrected_sentence}\"\n\n"
        f"Original snippet: \"{original_snippet}\"\n"
        f"Inserted text: \"{corrected_snippet}\"\n\n"
    )
    instructions = (
        "In one or two sentences, explain in simple terms why adding this text makes the sentence clearer or more accurate. "
        "Focus on how the insertion improves the overall sentence."
    )
    return base_prompt + instructions

def generate_correction_explanation_single(block_type, ocr_sentence, corrected_sentence, correction_block):
    """
    1) Extract the relevant snippets from the correction block.
    2) Build a detailed explanation prompt that includes the full corrected sentence.
    3) Retrieve and return the explanation from OpenAI.
    """
    if block_type == "replacement":
        original_snippet = correction_block.get("replaced_text", "")
        corrected_snippet = correction_block.get("corrected_text", "")
    elif block_type == "delete":
        original_snippet = correction_block.get("delete_text", "")
        corrected_snippet = ""  # No replacement text for deletions.
    elif block_type == "insert":
        original_snippet = ""
        corrected_snippet = correction_block.get("insert_text", "")
    else:
        raise ValueError(f"Unsupported block type: {block_type}")

    if block_type == "replacement":
        final_prompt = build_replacement_prompt(original_snippet, corrected_snippet, corrected_sentence)
    elif block_type == "delete":
        final_prompt = build_deletion_prompt(original_snippet, corrected_snippet, corrected_sentence)
    elif block_type == "insert":
        final_prompt = build_insertion_prompt(original_snippet, corrected_snippet, corrected_sentence)

    print("\n--- Explanation Prompt ---")
    print(final_prompt)

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0,
        max_tokens=200
    )
    explanation = response.choices[0].message["content"].strip()

    print("\n--- Explanation Response ---")
    print(explanation)

    return explanation

# --- Example Test Harness (Adjust for your own usage) ---
if __name__ == "__main__":
    # Example: The user clicked on a "replacement" block
    test_data = {"blockType": "replacement", "blockIndex": 0, "sentenceIndex": 14}
    
    # Get correction details from the service
    correction_info = get_correction_explanation(test_data)

    if "error" in correction_info:
        print("Error from corrections_service:", correction_info)
    else:
        block_type = correction_info.get("block_type", "replacement")
        ocr_sentence = correction_info["ocr_sentence"]
        corrected_sentence = correction_info["corrected_sentence"]
        correction_block = correction_info["correction_block"]

        # Generate the explanation for this correction block
        explanation = generate_correction_explanation_single(
            block_type,
            ocr_sentence,
            corrected_sentence,
            correction_block
        )

        print("\nExplanation for Single Block:", explanation)
