# main.py

from openai_api_call import perform_ocr, correct_text
from seq_alignment import align_sentences
from diff_lib import generate_report, TextTokenizer, split_into_sentences
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

image_path = "/home/keithuncouth/Downloads/hwt_test2.jpeg"

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
    report = generate_report(matches)
    print("\nGenerated Report:")
    print(report)

    # Step 5: Split the report into sentences
    sentences = split_into_sentences(report)

    # Lists to hold final sentences with ANSI colors and their corresponding blocks
    final_sentences = []
    blocks_by_sentence = []

    for idx, sentence in enumerate(sentences):
        # Tokenize the sentence
        tokenizer = TextTokenizer(sentence)
        tokens = tokenizer.parse_text()

        # Debug: Print the tokenized output
        #print(f"Tokenized output for Sentence {idx + 1}:")
        #for token in tokens:
            #print(token)

        # Create blocks from tokens
        blocks = create_blocks(tokens)

        # Debug: Print the created blocks
        #print(f"Created blocks for Sentence {idx + 1}:")
        #for block in blocks:
            #zprint(vars(block))

        # Construct the final sentence with ANSI colors
        final_sentence = ''.join(
            f"{ANSI_COLORS.get(token['color'], '')}{token['char']}" for token in tokens
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
