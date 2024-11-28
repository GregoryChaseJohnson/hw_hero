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

def find_best_matches_with_rules(ocr_sentences, corrected_sentences, min_score=50):
    """
    Sequentially match OCR sentences to corrected sentences with rules for handling splits and merges.
    """
    matches = []
    corrected_index = 0  # Track the current corrected sentence index

    for ocr_sentence in ocr_sentences:
        if corrected_index >= len(corrected_sentences):
            # If no more corrected sentences, append unmatched
            matches.append((ocr_sentence, "NO GOOD MATCH"))
            continue

        # Current corrected sentence
        current_corrected = corrected_sentences[corrected_index]

        # Compare with current sentence
        score_current = fuzz.ratio(ocr_sentence, current_corrected)

        # Lookahead: Compare with the next sentence (if it exists)
        score_next = 0
        combined_next = ""
        if corrected_index + 1 < len(corrected_sentences):
            next_corrected = corrected_sentences[corrected_index + 1]
            score_next = fuzz.ratio(ocr_sentence, next_corrected)
            # Combine current and next corrected sentences
            combined_next = current_corrected + " " + next_corrected
            score_combined = fuzz.ratio(ocr_sentence, combined_next)
        else:
            score_combined = 0

        # Choose the best match based on scores
        if score_current >= min_score and score_current >= score_next and score_current >= score_combined:
            # Match with the current corrected sentence
            matches.append((ocr_sentence, current_corrected))
            corrected_index += 1
        elif score_next >= min_score and score_next >= score_combined:
            # Match with the next corrected sentence
            matches.append((ocr_sentence, next_corrected))
            corrected_index += 2  # Skip to the sentence after the next
        elif score_combined >= min_score:
            # Match with the combined sentences
            matches.append((ocr_sentence, combined_next))
            corrected_index += 2  # Skip to the sentence after the next
        else:
            # No good match
            matches.append((ocr_sentence, "NO GOOD MATCH"))
            corrected_index += 1

    return matches

# Example OCR output
ocr_text = """Why would it be more valuable to teach students practical subjects instead of theory subjects?

We have a lot of information today and it is more important to experience something first than theoretical information. However, many schools believe theory subjects are more important than practical subjects, and there are more theory subjects than practical subjects, so many people don't care much about practical subjects.

Teaching practical subjects is more valuable because it is easy to learn and understand how to do something. We learn practical course, practical skills, how to behave polite to elders in practical subjects, we use this in our real life, but except for the basis, students don't use many of theory subjects. In life, we only study theory subjects for tests and go to university. We can apply practical subjects to our everyday life. Except for math-related profession, most of the students don't use equations, factorization, intersection etc. before they die.

"""

# Corrected text
corrected_text = """Why would it be more valuable to teach students practical subjects instead of theoretical subjects?

We have a lot of information today, and it is more important to experience something firsthand than to rely solely on theoretical information. However, many schools believe that theoretical subjects are more important than practical subjects, and there are more theoretical subjects than practical ones, so many people don't care much about practical subjects.

Teaching practical subjects is more valuable because it is easier to learn and understand how to do something. In practical courses, we learn practical skills, such as how to behave politely toward elders. We use these skills in our real lives, but aside from the basics, students don't often apply many theoretical subjects. In life, we primarily study theoretical subjects for tests and to gain admission to university. We can apply practical subjects to our everyday lives. Except for math-related professions, most students don't use equations, factorization, intersections, etc., before they die.

"""

# Step 1: Split both texts into sentences
ocr_sentences = split_into_sentences(ocr_text)
corrected_sentences = split_into_sentences(corrected_text)

# Step 2: Perform matching with rules
matches = find_best_matches_with_rules(ocr_sentences, corrected_sentences)

# Step 3: Output sentence pairs
for ocr_sentence, best_match in matches:
    print(f"Original: {ocr_sentence}")
    print(f"Corrected: {best_match}")
    print("-" * 40)
