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


def find_best_matches_bidirectional(ocr_sentences, corrected_sentences, min_score=70):
    """
    Match OCR sentences to corrected sentences, handling splits and merges bidirectionally.
    """
    matches = []
    corrected_index = 0  # Track the current corrected sentence index
    skip_next_ocr = False  # Flag to skip the next OCR sentence if combined

    for i, ocr_sentence in enumerate(ocr_sentences):
        if skip_next_ocr:
            skip_next_ocr = False
            continue

        if corrected_index >= len(corrected_sentences):
            # If no more corrected sentences, append unmatched
            matches.append((ocr_sentence, "NO GOOD MATCH"))
            continue

        # Initialize variables
        current_corrected = corrected_sentences[corrected_index]
        score_current = fuzz.ratio(ocr_sentence, current_corrected)
        best_match = (current_corrected, score_current)

        # Lookahead: Combine corrected sentences
        score_combined_corrected = 0
        if corrected_index + 1 < len(corrected_sentences):
            combined_corrected = current_corrected + " " + corrected_sentences[corrected_index + 1]
            score_combined_corrected = fuzz.ratio(ocr_sentence, combined_corrected)

        # Determine the best match
        if score_current >= min_score and score_current >= score_combined_corrected:
            best_match = (current_corrected, score_current)
            corrected_index += 1  # Advance to the next corrected sentence
        elif score_combined_corrected >= min_score:
            best_match = (combined_corrected, score_combined_corrected)
            corrected_index += 2  # Skip the combined corrected sentences

        # Append the match
        matches.append((ocr_sentence, best_match[0]))

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
