import pickle
from openai_api_call import perform_ocr, correct_text
from seq_alignment_reverse import align_sentences
from diff_lib_test2 import generate_report
from block_creation import create_blocks
from data_loader import DataLoader
from renderer import process_sentences
from annotated_line_space_cleanup import post_process
from align_overhang import finalize_transformation
use_test_data = False

test_ocr_text = """Recently, there are many music and K-pop singer coming out. Also, many people including youth are enjoying and affected by it. As the world keeps affected by K-pop, some people are concerned about K-pop music's bad influence because it can have the bad effect. But, for my opinion, I strongly believe that K-pop has more positive effect than harm on the youth.

Firstly, it can inspire confidence and hope. In my life, I'm having hard time due to the homework and school test. But, I sometimes get rested by hearing K-pop music and getting hope by it. Also, during COVID-19 pandemic, I was having hard time by its regulation. But when BTS's song named 'Permission to Dance', I can feel the hope to end the pandemic.

Secondly, it can make the whole culture more interest to youths. In my school, how many girl classmates gather and hang out to talk about their favorite K-pop singer or songs. Also, they collect their money or go to other place merchandise product of singer. This can trigger youths to make more friends and making them to be more socialized, which is important to later on the work.

Third and lastly, it can make Korean youth to think again about their traditional culture and proud of. Like recent I heard many about the Pusion.
"""
test_corrected_text = """Recently, there have been many new music and K-pop singers coming out. Also, a lot of people, including young people, are enjoying it and being influenced by it. As the world continues to be affected by K-pop, some people are concerned about its negative influence because it can have bad effects. But in my opinion, I strongly believe that K-pop has a more positive impact than harm on youth.

Firstly, it can inspire confidence and hope. In my life, I'm having a hard time with homework and school tests. But I sometimes find comfort in listening to K-pop music and feeling hopeful because of it. Also, during the COVID-19 pandemic, I struggled with the restrictions. But when I heard BTS's song "Permission to Dance," I felt hopeful about the end of the pandemic.

Secondly, it can make the whole culture more interesting to young people. In my school, many of my female classmates gather and hang out to talk about their favorite K-pop singers or songs. They also save up their money to buy merchandise from their favorite artists. This can encourage young people to make more friends and become more social, which is important for their future careers.

Lastly, it can make Korean youth rethink their traditional culture and feel proud of it. Recently, I've heard a lot about Pusion.
"""
image_path = "/home/keithuncouth/Downloads/hwt_5.jpeg"

def main():
    # Steps 1 & 2: OCR and correct
    if use_test_data:
        ocr_output = test_ocr_text
        corrected_text = test_corrected_text
    else:
        ocr_output = perform_ocr(image_path)
        print("OCR Output:")
        print(ocr_output)
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

    # Step 5: Create blocks
    final_tokens_by_sentence = []
    blocks_by_sentence = []
    for idx, sentence_tokens in enumerate(tokenized_output):
        blocks = create_blocks(sentence_tokens)
        final_tokens_by_sentence.append(sentence_tokens)
        blocks_by_sentence.append(blocks)

    # Step 6: Load into DataLoader and render
    data_loader = DataLoader(final_tokens_by_sentence, blocks_by_sentence)
    process_sentences(data_loader)

    # Step 7: Now that rendering is done, load renderer output
    with open("renderer_output.pkl", "rb") as f:
        data = pickle.load(f)
        annotated_lines = data["annotated_lines"]
        final_sentences = data["final_sentences"]
        blocks_by_sentence = data["blocks_by_sentence"]

    # Step 8: Post-process after rendering
    print("\nRunning Post-Process Stage...")
    post_process(annotated_lines, final_sentences, blocks_by_sentence)

    with open("annotated_line_space_cleanup_output.pkl", "rb") as f:
        updated_data = pickle.load(f)
        annotated_lines = updated_data["annotated_lines"]
        final_sentences = updated_data["final_sentences"]
        blocks_by_sentence = updated_data["blocks_by_sentence"]  # If needed

    print("\nRunning Final Transformation Stage...")
    finalize_transformation(annotated_lines, final_sentences)

if __name__ == "__main__":
    main()
