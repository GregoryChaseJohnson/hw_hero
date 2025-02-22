import json
import os
import sys

SENTENCE_MAPPING_PATH = "/home/keithuncouth/hw_hero/renderer/run/sentence_mapping.json"
OUTPUT_JSON_PATH = "/home/keithuncouth/hw_hero/renderer/run/output.json"

def get_correction_explanation(data):
    print("DEBUG: Function get_correction_explanation() was called")
    print("DEBUG: Received data:", data)
    sys.stdout.flush()

    try:
        block_type = data['blockType']
        block_index = int(data['blockIndex'])
        sentence_index = int(data['sentenceIndex'])
    except Exception as e:
        print("DEBUG: Input parsing error:", e)
        return {"error": "Invalid input", "details": str(e)}

    # Check if JSON files exist
    if not os.path.exists(SENTENCE_MAPPING_PATH):
        print(f"ERROR: {SENTENCE_MAPPING_PATH} does not exist")
        return {"error": "Sentence mapping file not found"}

    if not os.path.exists(OUTPUT_JSON_PATH):
        print(f"ERROR: {OUTPUT_JSON_PATH} does not exist")
        return {"error": "Output file not found"}

    # Load JSON metadata
    try:
        with open(SENTENCE_MAPPING_PATH, "r", encoding="utf-8") as f:
            sentence_mapping = json.load(f)
        with open(OUTPUT_JSON_PATH, "r", encoding="utf-8") as f:
            output_data = json.load(f)

        print(f"DEBUG: Loaded {len(sentence_mapping.get('sentences', []))} sentences")
        print(f"DEBUG: Loaded {len(output_data.get('sentences', []))} corrections")

    except Exception as e:
        print("DEBUG: Error loading JSON files:", e)
        return {"error": "JSON load error", "details": str(e)}

    # Retrieve sentence by index
    sentence_entry = next((s for s in sentence_mapping.get("sentences", [])
                           if s.get("sentence_index") == sentence_index), None)

    if not sentence_entry:
        print(f"DEBUG: No sentence found for index {sentence_index}")
        return {"error": "Sentence not found", "sentence_index": sentence_index}

    print(f"DEBUG: Found sentence {sentence_entry.get('ocr_sentence')}")

    # Retrieve correction entry
    correction_entry = next((c for c in output_data.get("sentences", [])
                             if c.get("sentence_index") == sentence_index), None)

    if not correction_entry:
        print(f"DEBUG: No correction found for index {sentence_index}")
        return {"error": "Corrections not found", "sentence_index": sentence_index}

    block_key = f"{block_type}_blocks"
    if block_key not in correction_entry:
        print(f"DEBUG: Block type '{block_type}' not found")
        return {"error": "Invalid block type", "block_type": block_type}

    try:
        if block_type == "delete":
            correction_block = next((b for b in correction_entry[block_key]
                                     if b.get("delete_block_index", -1) == block_index), None)
        elif block_type == "insert":
            correction_block = next((b for b in correction_entry[block_key]
                                     if b.get("insert_block_index", -1) == block_index), None)
        else:
            correction_block = next((b for b in correction_entry[block_key]
                                     if b.get("block_index", -1) == block_index), None)
    except Exception as e:
        print(f"DEBUG: Error extracting block: {e}")
        return {"error": "Block index error", "details": str(e)}

    if not correction_block:
        print(f"DEBUG: No block found for type {block_type} at index {block_index}")
        return {"error": f"{block_type.capitalize()} block not found", "block_index": block_index}

    print("DEBUG: Correction block found:", correction_block)

    return {
        "ocr_sentence": sentence_entry.get("ocr_sentence"),
        "corrected_sentence": sentence_entry.get("corrected_sentence"),
        "correction_block": correction_block
    }

def generate_custom_sentence_for_block(corrected_sentence, correction_block, block_type):
    """
    Generate a custom sentence for API context by reverting only the clicked correction.
    
    For each correction type:
      - Replacement: Replace the first occurrence of the corrected text with the original text.
      - Insert: Remove the inserted text.
      - Delete: Insert the deleted text back into the sentence.
    
    Parameters:
        corrected_sentence (str): The fully corrected sentence.
        correction_block (dict): The block details for the clicked correction.
        block_type (str): One of "replacement", "insert", or "delete".
    
    Returns:
        str: The custom sentence with the specific correction reverted.
    """
    if block_type == "replacement":
        # Instead of using final_start/final_end (which seem inconsistent),
        # locate the corrected text in the sentence and replace it with the original text.
        corrected_text = correction_block.get("corrected_text", "")
        replaced_text = correction_block.get("replaced_text", "")
        # Replace the first occurrence only.
        custom_sentence = corrected_sentence.replace(corrected_text, replaced_text, 1)
        return custom_sentence

    elif block_type == "insert":
        start = correction_block.get("final_start")
        end = correction_block.get("final_end")
        custom_sentence = corrected_sentence[:start] + corrected_sentence[end:]
        return custom_sentence

    elif block_type == "delete":
        start = correction_block.get("final_start")
        deleted_text = correction_block.get("delete_text", "")
        custom_sentence = corrected_sentence[:start] + deleted_text + corrected_sentence[start:]
        return custom_sentence

    else:
        return corrected_sentence


# If you run this file directly, test manually
if __name__ == "__main__":
    test_data = {"blockType": "replacement", "blockIndex": 0, "sentenceIndex": 14}
    print("DEBUG: Running manual test")

    result = get_correction_explanation(test_data)
    print(result)  # Print correction info

    if "error" not in result:
        corrected_sentence = result["corrected_sentence"]
        correction_block = result["correction_block"]
        block_type = test_data["blockType"]

        # Generate and print the custom sentence
        custom_sentence = generate_custom_sentence_for_block(corrected_sentence, correction_block, block_type)
        print("\n--- Custom Sentence (Correction Reverted) ---")
        print(custom_sentence)
