import json
import os
import sys

SENTENCE_MAPPING_PATH = "/home/keithuncouth/hw_hero/renderer/run/sentence_mapping.json"
OUTPUT_JSON_PATH = "/home/keithuncouth/hw_hero/renderer/run/output.json"

def get_correction_explanation(data):
    print("DEBUG: Function get_correction_explanation() was called")
    print("DEBUG: Received data:", data) 
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
        # Note: output_data is expected to be a dictionary with key "sentences"
        print(f"DEBUG: Loaded {len(output_data.get('sentences', []))} corrections")

        # **NEW: Print the first few entries to inspect**
        print(f"DEBUG: Type of output_data: {type(output_data)}")
        if isinstance(output_data, dict):
            sentences_list = output_data.get("sentences", [])
            if sentences_list:
                print(f"DEBUG: First entry type: {type(sentences_list[0])}")
        else:
            print("DEBUG: Output data is NOT a dict! Investigate format.")
            print(f"DEBUG: Full output_data content: {output_data}")

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

    # Retrieve correction entry (assuming output_data is a dict with key "sentences")
    correction_entry = next((c for c in output_data.get("sentences", [])
                         if c.get("sentence_index") == sentence_index), None)

    if not correction_entry:
        print(f"DEBUG: No correction found for index {sentence_index}")
        return {"error": "Corrections not found", "sentence_index": sentence_index}

    block_key = f"{block_type}_blocks"
    if block_key not in correction_entry:
        print(f"DEBUG: Block type '{block_type}' not found")
        return {"error": "Invalid block type", "block_type": block_type}

    # Find the correct block using special keys for delete and insert
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

# If you run this file directly, test manually
if __name__ == "__main__":
    test_data = {"blockType": "replacement", "blockIndex": 0, "sentenceIndex": 14}
    print("DEBUG: Running manual test")
    print(get_correction_explanation(test_data))
