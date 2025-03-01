import openai
import os
import time  # For generating a unique nonce
from correction_service import (
    get_correction_explanation,
    generate_custom_sentence_for_block,
    get_ocr_sentence_if_isolated,
    rebuild_sentence_for_delete
)

openai.api_key = os.getenv("OPENAI_API_KEY")

def build_replacement_prompt(before_text, after_text, custom_sentence, corrected_sentence):
    """
    Build and display the chain-of-thought for a replacement correction.
    Prints each prompt (in uppercase) and its corresponding output exactly once.
    Appends a unique nonce to avoid caching issues.
    Returns the natural summary of the correction.
    """
    import time
    import openai

    # BASE CONTEXT FOR THE PROMPT.
    nonce = str(int(time.time() * 1000))  # Unique identifier based on timestamp
    base_prompt = (
        f"Correction explanation:\n\n"
        f"Before:\nSentence: \"{custom_sentence}\"\nWord/Phrase: \"{before_text}\"\n\n"
        f"After:\nSentence: \"{corrected_sentence}\"\nWord/Phrase: \"{after_text}\"\n\n"
        f"NONCE: {nonce}\n\n"
    )
    print("\n--- BASE PROMPT ---")
    print(base_prompt.upper())
    
    # STEP 1: GENERATE MINIMAL BULLET POINTS.
    bullet_prompt = (
        base_prompt +
        f"List 3-5 very brief bullet points (max 5 words each) that explain the usage change when replacing "
        f"'{before_text}' with '{after_text}'. Mention if the replacement is effectively expressing the same thing or if it is a structural change where the sentence was reworded."
    )
    print("\n--- BULLET PROMPT ---")
    print(bullet_prompt.upper())
    
    bullet_response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": bullet_prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    bullet_points = bullet_response.choices[0].message["content"].strip()
    print("\n--- BULLET RESPONSE ---")
    print(bullet_points)
    
    # STEP 2: GENERATE A DRAFT EXPLANATION USING THE BULLET POINTS.
    draft_prompt = (
        base_prompt +
        f"Using the bullet points below, write one clear sentence that explains why "
        f"'{before_text}' was replaced by '{after_text}' and, if it is a structural change, what was changed around in the sentence. "
        "Do not include any extra commentary.\n\n"
        f"Bullet Points:\n{bullet_points}"
    )
    print("\n--- DRAFT PROMPT ---")
    print(draft_prompt.upper())
    
    draft_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": draft_prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    draft_explanation = draft_response.choices[0].message["content"].strip()
    print("\n--- DRAFT RESPONSE ---")
    print(draft_explanation)
    
    # STEP 3: POLISH THE DRAFT INTO A FINAL ANSWER.
    polish_prompt = (
        f"\n\nWhat is most important for the English learner to take note of in the following explanation?\n"
        f"{draft_explanation}"
    )
    print("\n--- POLISHED PROMPT ---")
    print(polish_prompt.upper())
    
    polish_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": polish_prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    final_answer = polish_response.choices[0].message["content"].strip()
    print("\n--- FINAL ANSWER ---")
    print(final_answer)
    
    # STEP 4: ADDITIONAL NATURAL SUMMARIZATION PROMPT.
    summary_prompt = (
        f"Below are the correction details and the final explanation:\n\n"
        f"Before:\nSentence: \"{custom_sentence}\"\nWord/Phrase: \"{before_text}\"\n\n"
        f"After:\nSentence: \"{corrected_sentence}\"\nWord/Phrase: \"{after_text}\"\n\n"
        f"Final Explanation:\n\"{final_answer}\"\n\n"
        "Please provide a natural, intuitive answer that emphasis the bigger picture of why '{before_text}' what was changed to '{after_text}' and consider if they were intedning something else and we the corrector are misinterperating them? Be consice and matter of fact."
    )
    print("\n--- SUMMARY PROMPT ---")
    print(summary_prompt.upper())
    
    summary_response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": summary_prompt}],
        temperature=0.7,
        max_tokens=200,
    )
    summary = summary_response.choices[0].message["content"].strip()
    print("\n--- SUMMARY RESPONSE ---")
    print(summary)
    
    return summary

def build_deletion_prompt(original_snippet, custom_sentence, corrected_sentence):
    """
    Build a deletion prompt.
    """
    base_prompt = (
        f"Sentence: \"{custom_sentence}\"\n\n"
        f"Corrected sentence: \"{corrected_sentence}\"\n\n"
        f"Removed: \"{original_snippet}\"\n\n"
    )
    instructions = (
        "Briefly explain, in plain English, what the removal means and why it was necessary."
    )
    return base_prompt + instructions

def build_insertion_prompt(inserted_text, custom_sentence, corrected_sentence):
    """
    Build an insertion prompt.
    """
    base_prompt = (
        f"Incorrect sentence: \"{custom_sentence}\"\n\n"
        f"Correct sentence: \"{corrected_sentence}\"\n\n"
        f"Inserted text: \"{inserted_text}\"\n\n"
    )
    instructions = (
        "Explain in one or two short, plain English sentences why the inserted text is needed to correct the sentence based on usage patterns. Avoid broader commentary."
    )
    return base_prompt + instructions

def generate_correction_explanation_single(block_type, ocr_sentence, corrected_sentence, correction_block, correction_entry=None):
    """
    Generate the final correction explanation.
    For 'replacement' blocks, uses the output from build_replacement_prompt directly.
    For 'delete' and 'insert', builds the appropriate prompt and shows its output.
    """
    if block_type == "delete":
        if correction_entry is not None:
            clicked_delete_block_id = correction_block.get("delete_block_index")
            ocr_from_mapping = get_ocr_sentence_if_isolated(correction_entry, clicked_delete_block_id)
            if ocr_from_mapping is not None:
                print("DEBUG: DETECTED ISOLATED PUNCTUATION; USING OCR SENTENCE.")
                custom_sentence = ocr_from_mapping
            else:
                custom_sentence = rebuild_sentence_for_delete(correction_entry, clicked_delete_block_id)
            print("DEBUG: FINAL SENTENCE AFTER DELETE PROCESSING:")
            print(custom_sentence)
        else:
            start = correction_block.get("final_start")
            deleted_text = correction_block.get("delete_text", "")
            print(f"DEBUG: FALLBACK DELETE METHOD AT {start}, REINSERTING '{deleted_text}'.")
            custom_sentence = corrected_sentence[:start] + deleted_text + corrected_sentence[start:]
            print("DEBUG: RESULTING SENTENCE:")
            print(custom_sentence)
    elif block_type in ("replacement", "insert"):
        custom_sentence = generate_custom_sentence_for_block(correction_entry, correction_block, block_type)
    else:
        raise ValueError(f"UNSUPPORTED BLOCK TYPE: {block_type}")

    if block_type == "replacement":
        before_text = correction_block.get("replaced_text", "")
        after_text = correction_block.get("corrected_text", "")
        # For replacement blocks, directly use build_replacement_prompt's output.
        explanation = build_replacement_prompt(before_text, after_text, custom_sentence, corrected_sentence)
    elif block_type == "delete":
        original_snippet = correction_block.get("delete_text", "")
        final_prompt = build_deletion_prompt(original_snippet, custom_sentence, corrected_sentence)
        print("\n--- FINAL DELETION PROMPT ---")
        print(final_prompt.upper())
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0,
            max_tokens=100
        )
        explanation = response.choices[0].message["content"].strip()
        print("\n--- FINAL DELETION RESPONSE ---")
        print(explanation)
    elif block_type == "insert":
        inserted_text = correction_block.get("insert_text", "")
        final_prompt = build_insertion_prompt(inserted_text, custom_sentence, corrected_sentence)
        print("\n--- FINAL INSERTION PROMPT ---")
        print(final_prompt.upper())
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": final_prompt}],
            temperature=0,
            max_tokens=100
        )
        explanation = response.choices[0].message["content"].strip()
        print("\n--- FINAL INSERTION RESPONSE ---")
        print(explanation)
    else:
        raise ValueError(f"UNSUPPORTED BLOCK TYPE: {block_type}")

    return explanation

# --- Example Test Harness (Adjust for your own usage) ---
if __name__ == "__main__":
    test_data = {"blockType": "replacement", "blockIndex": 0, "sentenceIndex": 0}
    
    correction_info = get_correction_explanation(test_data)
    if "error" in correction_info:
        print("ERROR FROM CORRECTIONS_SERVICE:", correction_info)
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

        print("\nEXPLANATION FOR SINGLE BLOCK:")
        print(explanation)
