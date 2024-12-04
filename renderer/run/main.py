# main.py

from openai_api_call import perform_ocr, correct_text
from seq_alignment import align_sentences
from diff_lib import generate_report, TextTokenizer, split_into_sentences
from block_creation import create_blocks
from test_renderer import test_renderer

def main():
    # Example image file path
    image_path = "/home/keithuncouth/Downloads/hwt_9.jpg"

    # Step 1: Perform OCR
    ocr_output = perform_ocr(image_path)

    # Step 2: Correct the text
    corrected_text = correct_text(ocr_output)

    # Step 3: Align sentences
    matches = align_sentences(ocr_output, corrected_text)

    # Step 4: Generate a report of differences
    report = generate_report(matches)
    print("\nGenerated Report:")
    print(report)

    # Step 5: Split the report into sentences
    sentences = split_into_sentences(report)

    # Lists to hold tokenized sentences and their corresponding blocks
    tokenized_sentences = []
    blocks_by_sentence = []

    for idx, sentence in enumerate(sentences):
        # Tokenize the sentence
        tokenizer = TextTokenizer(sentence)
        tokens = tokenizer.parse_text()

        # Debug: Print the tokenized output
        print(f"Tokenized output for Sentence {idx + 1}:")
        for token in tokens:
            print(token)

        # Create blocks from tokens
        blocks = create_blocks(tokens)

        # Debug: Print the created blocks
        print(f"Created blocks for Sentence {idx + 1}:")
        for block in blocks:
            print(vars(block))

        # Append to the lists
        tokenized_sentences.append(tokens)
        blocks_by_sentence.append(blocks)

    # Step 6: Render all sentences with their annotations
    test_renderer(tokenized_sentences, blocks_by_sentence)

if __name__ == "__main__":
    main()
