import openai
import os
from correction_service import (
    get_correction_explanation,
    generate_custom_sentence_for_block,
    get_ocr_sentence_if_isolated,
    rebuild_sentence_for_delete
)

openai.api_key = os.getenv("OPENAI_API_KEY")

def build_replacement_prompt(before_text, after_text, custom_sentence, corrected_sentence):
    base_prompt = (
        f"Incorrect sentence: \"{custom_sentence}\"\n\n"
        f"Correct sentence: \"{corrected_sentence}\"\n\n"
        f"Original text: \"{before_text}\"\n"
        f"Corrected text: \"{after_text}\"\n\n"
    )
    instructions = (
        "In as few words as possible explain why replacing the original text with the corrected text in the written sentence is consistent with the indented meaning of the sentence. "
        "If it is a simple trivial mistake, be a bit more brief. Focus only on how this affects the sentence's meaning, without using technical grammar terminology. "
        "If it's a trivial change or in casual language either is acceptable then explain that too."
    )
    return base_prompt + instructions

def build_deletion_prompt(original_snippet, custom_sentence, corrected_sentence):
    base_prompt = (
        f"Sentence: \"{custom_sentence}\"\n\n"
        f"Corrected sentence: \"{corrected_sentence}\"\n\n"
        f"Removed: \"{original_snippet}\"\n\n"
    )
    instructions = (
        "Briefly explain, in easy plain English, what it seems you intended by including what was removed and why you need to remove it."
    )
    return base_prompt + instructions

def build_insertion_prompt(inserted_text, custom_sentence, corrected_sentence):
    base_prompt = (
        f"Incorrect sentence: \"{custom_sentence}\"\n\n"
        f"Correct sentence: \"{corrected_sentence}\"\n\n"
        f"Inserted text: \"{inserted_text}\"\n\n"
    )
    instructions = (
        "In one or two sentences, tell the learner why you needed to add the inserted text to make the sentence correct, using plain English and minimal grammar jargon."
    )
    return base_prompt + instructions

def generate_correction_explanation_single(block_type, ocr_sentence, corrected_sentence, correction_block, correction_entry=None):
    """
    1) Generate a custom context sentence that reverts the clicked correction.
    2) Build a detailed prompt that always includes the full corrected sentence.
    3) Retrieve and return the explanation from OpenAI.
    """
    if block_type == "delete":
        if correction_entry is not None:
            clicked_delete_block_id = correction_block.get("delete_block_index")
            # First, check if the deleted token is isolated punctuation.
            ocr_from_mapping = get_ocr_sentence_if_isolated(correction_entry, clicked_delete_block_id)
            if ocr_from_mapping is not None:
                print("DEBUG: Detected isolated punctuation; using OCR sentence.")
                custom_sentence = ocr_from_mapping
            else:
                # Rebuild the sentence ignoring insert tokens.
                custom_sentence = rebuild_sentence_for_delete(correction_entry, clicked_delete_block_id)
            print("DEBUG: Final sentence after delete processing:", custom_sentence)
        else:
            start = correction_block.get("final_start")
            deleted_text = correction_block.get("delete_text", "")
            print(f"DEBUG: Fallback delete method at {start}, reinserting '{deleted_text}'.")
            custom_sentence = corrected_sentence[:start] + deleted_text + corrected_sentence[start:]
            print("DEBUG: Resulting sentence:", custom_sentence)
    elif block_type in ("replacement", "insert"):
        custom_sentence = generate_custom_sentence_for_block(corrected_sentence, correction_block, block_type)
    else:
        raise ValueError(f"Unsupported block type: {block_type}")

    if block_type == "replacement":
        before_text = correction_block.get("replaced_text", "")
        after_text = correction_block.get("corrected_text", "")
        final_prompt = build_replacement_prompt(before_text, after_text, custom_sentence, corrected_sentence)
    elif block_type == "delete":
        original_snippet = correction_block.get("delete_text", "")
        final_prompt = build_deletion_prompt(original_snippet, custom_sentence, corrected_sentence)
    elif block_type == "insert":
        inserted_text = correction_block.get("insert_text", "")
        final_prompt = build_insertion_prompt(inserted_text, custom_sentence, corrected_sentence)
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
    test_data = {"blockType": "delete", "blockIndex": 0, "sentenceIndex": 11}
    
    correction_info = get_correction_explanation(test_data)
    if "error" in correction_info:
        print("Error from corrections_service:", correction_info)
    else:
        block_type = test_data["blockType"]
        ocr_sentence = correction_info["ocr_sentence"]
        corrected_sentence = correction_info["corrected_sentence"]
        correction_block = correction_info["correction_block"]
        correction_entry = correction_info.get("correction_entry")  # Needed for delete blocks.

        explanation = generate_correction_explanation_single(
            block_type,
            ocr_sentence,
            corrected_sentence,
            correction_block,
            correction_entry
        )

        print("\nExplanation for Single Block:", explanation)
