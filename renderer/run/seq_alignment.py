import re
from fuzzywuzzy import fuzz


def split_into_sentences(raw_text):
    """
    Split text into sentences while handling edge cases,
    such as abbreviations (e.g., 'etc.', 'e.g.') and periods followed by commas (e.g., 'etc.,').
    """
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', raw_text)
    text = re.sub(r'\b(etc)\.', r'\1<PROTECTEDPERIOD>', text)

    # List of common abbreviations that should not end sentences
    abbreviations = r'\b(?:etc|e\.g|i\.e|vs|Dr|Mr|Mrs|Ms|Prof|Jr|Sr)\.'

    # Protect abbreviations and edge cases by temporarily replacing periods
    text = re.sub(fr'({abbreviations})', r'\1<PERIOD>', text)
    text = re.sub(r'\.\,', '<DOTCOMMA>', text)

    # Regex to split sentences directly
    sentences = re.split(r'([.!?]["\']?\s+)', text)  # Match punctuation + quotes + space

    # Combine the sentences properly
    combined_sentences = []
    buffer = ""
    for segment in sentences:
        if re.match(r'[.!?]["\']?\s+', segment):
            buffer += segment  # Append the punctuation to the previous buffer
            combined_sentences.append(buffer.strip())
            buffer = ""
        else:
            buffer += segment  # Accumulate sentence text

    # Add any remaining text as a sentence
    if buffer.strip():
        combined_sentences.append(buffer.strip())

    # Restore protected periods and commas
    combined_sentences = [
        re.sub(r'(<PERIOD>)+', '.', s).replace('<DOTCOMMA>', '.,').replace('<PROTECTEDPERIOD>', '.')
        for s in combined_sentences
    ]

    return combined_sentences

def find_best_matches_bidirectional(ocr_sentences, corrected_sentences, min_score=50):
    """
    Match OCR sentences to corrected sentences, handling splits and merges bidirectionally.
    
    Args:
        ocr_sentences (List[str]): List of sentences obtained from OCR.
        corrected_sentences (List[str]): List of corrected sentences.
        min_score (int, optional): Minimum similarity score to consider a valid match. Defaults to 70.
    
    Returns:
        List[Tuple[str, str]]: List of tuples containing OCR sentence and its best matched corrected sentence.
    """
    matches = []
    ocr_index = 0
    corrected_index = 0

    while ocr_index < len(ocr_sentences) and corrected_index < len(corrected_sentences):
        ocr_sentence = ocr_sentences[ocr_index]
        current_corrected = corrected_sentences[corrected_index]
        score_current = fuzz.ratio(ocr_sentence, current_corrected)

        # Initialize best match as current corrected sentence
        best_candidate = current_corrected
        max_score = score_current
        increment_corrected = 1
        increment_ocr = 1

        # Attempt to combine with next corrected sentence
        if corrected_index + 1 < len(corrected_sentences):
            next_corrected = corrected_sentences[corrected_index + 1]
            combined_corrected = current_corrected + " " + next_corrected
            score_combined_corrected = fuzz.ratio(ocr_sentence, combined_corrected)
            if score_combined_corrected > max_score and score_combined_corrected >= min_score:
                best_candidate = combined_corrected
                max_score = score_combined_corrected
                increment_corrected = 2  # Skip next corrected sentence

        # Attempt to combine with next OCR sentence
        if ocr_index + 1 < len(ocr_sentences):
            next_ocr = ocr_sentences[ocr_index + 1]
            combined_ocr = ocr_sentence + " " + next_ocr
            score_combined_ocr = fuzz.ratio(combined_ocr, current_corrected)
            if score_combined_ocr > max_score and score_combined_ocr >= min_score:
                best_candidate = current_corrected
                max_score = score_combined_ocr
                increment_corrected = 1
                increment_ocr = 2  # Skip next OCR sentence

        # Decide whether to match single or combined OCR sentence
        if score_current >= min_score and score_current >= max(score_combined_corrected, score_combined_ocr):
            # Match single OCR to single corrected
            best_candidate = current_corrected
            max_score = score_current
            increment_corrected = 1
            increment_ocr = 1
        elif score_combined_corrected >= min_score and score_combined_corrected >= score_combined_ocr:
            # Match single OCR to combined corrected
            best_candidate = combined_corrected
            max_score = score_combined_corrected
            increment_corrected = 2
            increment_ocr = 1
        elif score_combined_ocr >= min_score and score_combined_ocr > max(score_current, score_combined_corrected):
            # Match combined OCR to single corrected
            best_candidate = current_corrected
            max_score = score_combined_ocr
            increment_corrected = 1
            increment_ocr = 2
        else:
            # No good match found
            best_candidate = "NO GOOD MATCH"
            max_score = 0
            increment_corrected = 1
            increment_ocr = 1

        # Append the match
        matches.append((ocr_sentence, best_candidate))

        # Increment indices based on the match type
        ocr_index += increment_ocr
        corrected_index += increment_corrected

    # Handle any remaining OCR sentences without matches
    while ocr_index < len(ocr_sentences):
        matches.append((ocr_sentences[ocr_index], "NO GOOD MATCH"))
        ocr_index += 1

    return matches


# Function to run the alignment directly
def align_sentences(ocr_text, corrected_text):
    # Step 1: Split both texts into sentences
    ocr_sentences = split_into_sentences(ocr_text)
    corrected_sentences = split_into_sentences(corrected_text)

    # Step 2: Perform matching
    matches = find_best_matches_bidirectional(ocr_sentences, corrected_sentences)

    # Step 3: Output sentence pairs
    for ocr_sentence, best_match in matches:
        print(f"Original: {ocr_sentence}")
        print(f"Corrected: {best_match}")
        print("-" * 40)

    return matches
