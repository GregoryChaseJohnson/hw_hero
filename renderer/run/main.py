# main.py

from openai_api_call import perform_ocr, correct_text
from seq_alignment_reverse import align_sentences
from diff_lib_test2 import generate_report
from block_creation import create_blocks
from data_loader import DataLoader
from renderer import process_sentences

# Define ANSI_COLORS here as used in main.py to construct final_sentence
# To avoid duplication, consider moving ANSI_COLORS to a separate module
ANSI_COLORS = {
    'normal': '\033[0m',
    'red': '\033[31m',
    'green': '\033[92m',
    'blue': '\033[34m',
    'pink': '\033[35m',
}

image_path = "/home/keithuncouth/Downloads/hwt_9.jpeg"

def main():
    # Step 1: Perform OCR
    ocr_output = perform_ocr(image_path)
    print("OCR Output:")
    print(ocr_output)

    # Step 2: Correct the text
    corrected_text = correct_text(ocr_output)
    print("\nCorrected Text:")
    print(corrected_text)

    # Step 3: Align sentences
    matches = align_sentences(ocr_output, corrected_text)

    # Step 4: Generate a report of differences
    report, tokenized_output = generate_report(matches)  # Updated to unpack tokenized output
    print("\nGenerated Report:")
    print(report)

    print("\nDebug: Tokenized Output from generate_report:")
    for idx, tokens in enumerate(tokenized_output):
        print(f"Sentence {idx + 1} Tokens:")
        if isinstance(tokens, list):  # Ensure tokens is a list
            for token in tokens:
                print(token)  # Print each token dictionary
        else:
            print("Error: Tokens are not in the expected list format!")
            print(tokens)  # Debug what tokens contain


    # Lists to hold final sentences with ANSI colors and their corresponding blocks
    final_sentences = []
    blocks_by_sentence = []

    # Step 5: Process tokenized sentences
    for idx, sentence_tokens in enumerate(tokenized_output):

        # Create blocks from tokens
        blocks = create_blocks(sentence_tokens)

        # Construct the final sentence with ANSI colors
        final_sentence = ''.join(
            f"{ANSI_COLORS.get(token['color'], '')}{token['char']}" for token in sentence_tokens
        )
        final_sentence += ANSI_COLORS['normal']  # Reset color

        final_sentences.append(final_sentence)
        blocks_by_sentence.append(blocks)

    # Step 6: Create DataLoader
    data_loader = DataLoader(final_sentences, blocks_by_sentence)

    # Step 7: Render all sentences sequentially
    process_sentences(data_loader)

if __name__ == "__main__":
    main()
