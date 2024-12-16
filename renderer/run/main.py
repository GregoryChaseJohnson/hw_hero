# main.py
from openai_api_call import perform_ocr, correct_text
from seq_alignment_reverse import align_sentences
from diff_lib_test2 import generate_report
from block_creation import create_blocks
from data_loader import DataLoader
from renderer import process_sentences

ANSI_COLORS = {
    'normal': '\033[0m',
    'red': '\033[31m',
    'green': '\033[92m',
    'blue': '\033[34m',
    'pink': '\033[35m',
}

# Set this to True when testing without API calls
use_test_data = False 

# Hard-coded test data
test_ocr_text = """
What is your favorite subject in your school? If I ask this to my friends most of them says that it is P.E class. P.E class is the only time for students to exercise and play around during school time. It can be the best time for most of the students, but however, there are some students which don't want to exercise during P.E time. They don't want to move their body or have physical disadvantages. However, many schools are still requiring P.E and sports time. So, should sports should be required in school? I believe that it should be not required, but should be optional.

First, we should respect students' opinions. Some students want sports time. But some does not. We can't require even one side's opinion. In my school, we have selected-subject time. We can choose the class which I wants and we could also choose what sports class I could attend. And to respect each students our school made the board game class. And we could be able to just relax or play board games during sports time.

Second, it can make dark history to some students. If we play any sports, sometimes we make mistakes. But most of the students criticize the student which made a mistake. And some even bullies. When I was in middle school first grade, I was playing soccer with my classmates. I was playing as goalkeeper. But I made a mistake, and we lose one goal. Then, one of my classmate which is bully and said "Are you out of mind? Saving

"""
test_corrected_text = """
What is your favorite subject in school? If I ask my friends, most of them say it's P.E. P.E. class is the only time for students to exercise and have fun during school. It can be the best time for many students, but there are some who don’t want to exercise during P.E. They don’t want to move their bodies or may have physical challenges. Still, many schools require P.E. and sports time. So, should sports be required in school? I believe it shouldn’t be required but should be optional.

First, we should respect students' opinions. Some students want sports time, but some don’t. We can’t force one side’s opinion. In my school, we have selected-subject time. We can choose the classes we want, including which sports class to attend. To respect all students, our school even created a board game class, so we can relax or play board games during sports time.

Second, sports can bring up bad memories for some students. When we play sports, we sometimes make mistakes. But many students criticize those who mess up, and some even bully them. When I was in first grade in middle school, I was playing soccer with my classmates. I was the goalkeeper, but I made a mistake and we let in a goal. Then, one of my classmates, who was a bully, said, "Are you out of your mind? Saving...
"""

image_path = "/home/keithuncouth/Downloads/hwt_5.jpeg"

def main():
    # If using test data, skip API calls
    if use_test_data:
        ocr_output = test_ocr_text
        corrected_text = test_corrected_text
    else:
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
    print("\nAligned Sentences:")
    for ocr_sentence, corrected_sentence in matches:
        print(f"OCR Sentence: {ocr_sentence}")
        print(f"Corrected Sentence: {corrected_sentence}")

    # Step 4: Generate a report
    report, tokenized_output = generate_report(matches)
    print("\nGenerated Report:")
    print(report)

    # Step 5: Process tokenized sentences into blocks
    final_tokens_by_sentence = []
    blocks_by_sentence = []
    for idx, sentence_tokens in enumerate(tokenized_output):
        blocks = create_blocks(sentence_tokens)
        final_tokens_by_sentence.append(sentence_tokens)
        blocks_by_sentence.append(blocks)

    # Step 6: Load data into DataLoader
    data_loader = DataLoader(final_tokens_by_sentence, blocks_by_sentence)

    # Step 7: Render all sentences
    process_sentences(data_loader)

if __name__ == "__main__":
    main()
