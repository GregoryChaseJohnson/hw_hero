import re
from fuzzywuzzy import fuzz

# Define a unique marker to indicate sentence combinations
COMBINATION_MARKER = "^**^"


def split_into_sentences(raw_text):
    """
    Split text into sentences while handling edge cases,
    such as abbreviations (e.g., 'etc.', 'e.g.') and periods followed by commas.
    """
    # Step 1: Normalize apostrophes
    def normalize_apostrophes(text):
        return text.replace('‘', "'").replace('’', "'").replace('‛', "'").replace('`', "'").replace('´', "'")
    
    text = normalize_apostrophes(raw_text)    


    text = re.sub(r'\s+', ' ', raw_text)
    abbreviations = r'\b(?:etc|e\.g|i\.e|vs|Dr|Mr|Mrs|Ms|Prof|Jr|Sr)\.'
    text = re.sub(fr'({abbreviations})', r'\1<PERIOD>', text)
    sentences = re.split(r'([.!?]["\']?\s+)', text)
    combined_sentences = []
    buffer = ""

    for segment in sentences:
        if re.match(r'[.!?]["\']?\s+', segment):
            buffer += segment
            combined_sentences.append(buffer.strip())
            buffer = ""
        else:
            buffer += segment

    if buffer.strip():
        combined_sentences.append(buffer.strip())

    combined_sentences = [
        s.replace('<PERIOD>', '.').strip() for s in combined_sentences
    ]
    return combined_sentences

def insert_marker_in_combination(first_sentence, marker=COMBINATION_MARKER):
    """
    Append the marker directly to the end of the first sentence.
    """
    return first_sentence.strip() + marker



def find_best_matches_bidirectional(ocr_sentences, corrected_sentences, min_score=50):
    matches = []
    ocr_index = 0
    corrected_index = 0

    while ocr_index < len(ocr_sentences) and corrected_index < len(corrected_sentences):
        ocr_sentence = ocr_sentences[ocr_index]
        current_corrected = corrected_sentences[corrected_index]
        score_current = fuzz.ratio(ocr_sentence, current_corrected)

        best_candidate = current_corrected
        max_score = score_current
        increment_corrected = 1
        increment_ocr = 1

        score_combined_corrected = 0
        score_combined_ocr = 0

        # Check if combining corrected sentences improves score
        if corrected_index + 1 < len(corrected_sentences):
            next_corrected = corrected_sentences[corrected_index + 1]
            combined_corrected = current_corrected + " " + next_corrected
            score_combined_corrected = fuzz.ratio(ocr_sentence, combined_corrected)
            if score_combined_corrected > max_score and score_combined_corrected >= min_score:
                best_candidate = combined_corrected
                max_score = score_combined_corrected
                increment_corrected = 2

        # Check if combining OCR sentences improves score
        if ocr_index + 1 < len(ocr_sentences):
            next_ocr = ocr_sentences[ocr_index + 1]
            combined_ocr = ocr_sentence + " " + next_ocr
            score_combined_ocr = fuzz.ratio(combined_ocr, current_corrected)
            if score_combined_ocr > max_score and score_combined_ocr >= min_score:
                best_candidate = current_corrected
                max_score = score_combined_ocr
                increment_corrected = 1
                increment_ocr = 2

        # Unified marker insertion logic:
        # If two OCR sentences combined
        if increment_ocr == 2:
            # Insert marker at the end of the first OCR sentence
            next_ocr = ocr_sentences[ocr_index + 1]
            ocr_sentence = insert_marker_in_combination(ocr_sentence) + " " + next_ocr

        # If two corrected sentences combined
        elif increment_corrected == 2:
            # Insert marker at the end of the first corrected sentence
            # Since we have best_candidate = current_corrected + " " + next_corrected
            # We know the first sentence is current_corrected
            first_corrected = current_corrected
            second_corrected = corrected_sentences[corrected_index + 1]
            best_candidate = insert_marker_in_combination(first_corrected) + " " + second_corrected

        matches.append((ocr_sentence.strip(), best_candidate.strip()))
        ocr_index += increment_ocr
        corrected_index += increment_corrected

    # Handle remaining unmatched OCR sentences
    while ocr_index < len(ocr_sentences):
        matches.append((ocr_sentences[ocr_index], "NO GOOD MATCH"))
        ocr_index += 1

    return matches


def resolve_conflicts(forward_matches, reverse_matches):
    """
    Resolve conflicts between forward and reverse matches.
    """
    forward_dict = {(o, c): fuzz.ratio(o, c) for o, c in forward_matches}
    reverse_dict = {(o, c): fuzz.ratio(c, o) for c, o in reverse_matches}

    resolved = []
    for key in set(forward_dict) | set(reverse_dict):
        forward_score = forward_dict.get(key, 0)
        reverse_score = reverse_dict.get(key, 0)
        if forward_score > reverse_score:
            resolved.append(key)
        elif reverse_score > forward_score:
            resolved.append(key)
        else:
            resolved.append(key)
    return resolved

def find_best_matches_bidirectional_reverse(ocr_sentences, corrected_sentences, min_score=50):
    """
    Perform bidirectional matching and conflict resolution.
    """
    forward_matches = find_best_matches_bidirectional(ocr_sentences, corrected_sentences, min_score)
    reverse_matches = find_best_matches_bidirectional(corrected_sentences, ocr_sentences, min_score)
    combined_matches = resolve_conflicts(forward_matches, reverse_matches)
    return combined_matches

def align_sentences(ocr_text, corrected_text):
    """
    Align OCR text with corrected text.
    """
    ocr_sentences = split_into_sentences(ocr_text)
    corrected_sentences = split_into_sentences(corrected_text)
    matches = find_best_matches_bidirectional_reverse(ocr_sentences, corrected_sentences, min_score=50)
    return matches

if __name__ == "__main__":
    example_ocr_text = """
      Actually when I was touring around Southeast Asia, I didn't have enough time and money so I couldn't go to Bali.
    """
    example_corrected_text = """ When I was touring around Southeast Asia, I didn’t have enough time or money. So I couldn’t go to Bali.
"""

    aligned_pairs = align_sentences(example_ocr_text, example_corrected_text)
    for ocr_sentence, corrected_sentence in aligned_pairs:
        print(f"OCR Sentence: {ocr_sentence}")
        print(f"Corrected Sentence: {corrected_sentence}")
