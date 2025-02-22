import openai
import os
from correction_service import get_correction_explanation, generate_custom_sentence_for_block

openai.api_key = os.getenv("OPENAI_API_KEY")

def build_replacement_prompt(before_text, after_text, full_context_sentence):
    """
    Build a prompt for a replacement change using the context sentence 
    where the clicked correction is reverted.
    """
    base_prompt = (
        f"Sentence with reverted correction: \"{full_context_sentence}\"\n\n"
        f"Reverted (original) text: \"{before_text}\"\n"
        f"Corrected text: \"{after_text}\"\n\n"
    )
    instructions = (
        "Briefly explain what was wrong and why the corrected text is better. "
        "Focus only on the changed word(s) in the given context."
    )
    return base_prompt + instructions

def build_deletion_prompt(original_snippet, corrected_snippet, full_context_sentence):
    base_prompt = (
        f"Sentence with reverted deletion: \"{full_context_sentence}\"\n\n"
        f"Text that was originally present: \"{original_snippet}\"\n"
        f"Text deleted in the corrected sentence: \"{corrected_snippet}\"\n\n"
    )
    instructions = (
        "In one or two sentences, explain how adding back the deleted text changes the sentence, "
        "and why its removal may have improved clarity."
    )
    return base_prompt + instructions

def build_insertion_prompt(original_snippet, corrected_snippet, full_context_sentence):
    base_prompt = (
        f"Sentence with reverted insertion: \"{full_context_sentence}\"\n\n"
        f"Text before insertion: \"{original_snippet}\"\n"
        f"Inserted text in the corrected sentence: \"{corrected_snippet}\"\n\n"
    )
    instructions = (
        "In one or two sentences, explain how removing the inserted text changes the sentence, "
        "and why its inclusion might affect the overall clarity."
    )
    return base_prompt + instructions

def generate_correction_explanation_single(block_type, ocr_sentence, corrected_sentence, correction_block):
    """
    1) Generate a custom context sentence that reverts the clicked correction.
    2) Build a detailed prompt that includes the custom sentence.
    3) Retrieve and return the explanation from OpenAI.
    """
    # Generate the custom context sentence
    custom_sentence = generate_custom_sentence_for_block(corrected_sentence, correction_block, block_type)

    if block_type == "replacement":
        before_text = correction_block.get("replaced_text", "")
        after_text = correction_block.get("corrected_text", "")
        final_prompt = build_replacement_prompt(before_text, after_text, custom_sentence)
    elif block_type == "delete":
        original_snippet = correction_block.get("delete_text", "")
        corrected_snippet = ""
        final_prompt = build_deletion_prompt(original_snippet, corrected_snippet, custom_sentence)
    elif block_type == "insert":
        original_snippet = ""
        corrected_snippet = correction_block.get("insert_text", "")
        final_prompt = build_insertion_prompt(original_snippet, corrected_snippet, custom_sentence)
    else:
        raise ValueError(f"Unsupported block type: {block_type}")

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
    test_data = {"blockType": "replacement", "blockIndex": 0, "sentenceIndex": 0}
    
    # Get correction details from the service
    correction_info = get_correction_explanation(test_data)

    if "error" in correction_info:
        print("Error from corrections_service:", correction_info)
    else:
        block_type = test_data["blockType"]  # We know the block type from the payload.
        ocr_sentence = correction_info["ocr_sentence"]
        corrected_sentence = correction_info["corrected_sentence"]
        correction_block = correction_info["correction_block"]

        # Generate the explanation for this correction block using the custom sentence for context.
        explanation = generate_correction_explanation_single(
            block_type,
            ocr_sentence,
            corrected_sentence,
            correction_block
        )

        print("\nExplanation for Single Block:", explanation)
