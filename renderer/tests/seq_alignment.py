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
    skip_next_corrected = False  # Flag to skip the next corrected sentence if combined

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
        score_next, combined_corrected = 0, ""
        if corrected_index + 1 < len(corrected_sentences):
            next_corrected = corrected_sentences[corrected_index + 1]
            score_next = fuzz.ratio(ocr_sentence, next_corrected)
            combined_corrected = current_corrected + " " + next_corrected
            score_combined_corrected = fuzz.ratio(ocr_sentence, combined_corrected)
        else:
            score_combined_corrected = 0

        # Lookahead: Combine OCR sentences
        combined_ocr = ""
        if i + 1 < len(ocr_sentences):
            next_ocr = ocr_sentences[i + 1]
            combined_ocr = ocr_sentence + " " + next_ocr
            score_combined_ocr = fuzz.ratio(combined_ocr, current_corrected)
        else:
            score_combined_ocr = 0

        # Determine the best match
        if score_current >= min_score and score_current >= score_next and score_current >= max(score_combined_corrected, score_combined_ocr):
            best_match = (current_corrected, score_current)
            corrected_index += 1  # Advance to the next corrected sentence
        elif score_next >= min_score and score_next >= score_combined_corrected and score_next >= score_combined_ocr:
            best_match = (next_corrected, score_next)
            corrected_index += 2  # Skip to the sentence after the next
        elif score_combined_corrected >= min_score and score_combined_corrected >= score_combined_ocr:
            best_match = (combined_corrected, score_combined_corrected)
            corrected_index += 2  # Skip the combined corrected sentences
            skip_next_corrected = True
        elif score_combined_ocr >= min_score:
            best_match = (current_corrected, score_combined_ocr)
            skip_next_ocr = True  # Skip the next OCR sentence as it's combined
            corrected_index += 1

        # Append the match
        matches.append((ocr_sentence, best_match[0]))

    return matches


# Example OCR output
ocr_text = """Recently, there are many music and K-pop singer coming out. Also, many people including youth are enjoying and affected by it. As the world keeps affected by K-pop, some people are concerned about K-pop music's bad influence because it can have the bad effect. But, for my opinion, I strongly believe that K-pop has more positive effect than harm on the youth.

Firstly, it can inspire confidence and hope. In my life, I'm having hard time due to the homework and school test. But, I sometimes get rested by hearing K-pop music and getting hope by it. Also, during COVID-19 pandemic, I was having hard time by its regulation. But when BTS's song named 'Permission to Dance', I can feel the hope to end the pandemic.

Secondly, it can make the whole culture more interest to youths. In my school, how many girl classmates gather and hang out to talk about their favorite K-pop singer or songs. Also, they collect their money or go to other place merchandise product of singer. This can trigger youths to make more friends and making them to be more socialized, which is important to later on the work.

Third and lastly, it can make Korean youth to think again about their traditional culture and proud of. Like recent I heard many about the fusion.





"""

# Corrected text
corrected_text = """Recently, there are many music and K-pop singers coming out. Also, many people, including youth, are enjoying it and being affected by it. As the world keeps being affected by K-pop, some people are concerned about its bad influence because it can have negative effects. But in my opinion, I strongly believe that K-pop has more positive effects than harm on the youth.

Firstly, it can inspire confidence and hope. In my life, I'm having a hard time due to homework and school tests. But I sometimes get a break by listening to K-pop music and finding hope in it. Also, during the COVID-19 pandemic, I was having a tough time with the restrictions. But when I heard BTS's song "Permission to Dance," I felt hopeful about the end of the pandemic.

Secondly, it can make the whole culture more interesting to youth. In my school, many of my girl classmates gather and hang out to talk about their favorite K-pop singers or songs. They also save their money or go to other places to buy merchandise from their favorite artists. This can encourage youth to make more friends and become more social, which is important for their future work.

Third and lastly, it can make Korean youth think again about their traditional culture and feel proud of it. Like recently, I heard a lot about the fusion.



"""

# Step 1: Split both texts into sentences
ocr_sentences = split_into_sentences(ocr_text)
corrected_sentences = split_into_sentences(corrected_text)

# Step 2: Perform matching with rules
# Step 2: Perform matching with rules
matches = find_best_matches_bidirectional(ocr_sentences, corrected_sentences)

# Step 3: Output sentence pairs
for ocr_sentence, best_match in matches:
    print(f"Original: {ocr_sentence}")
    print(f"Corrected: {best_match}")
    print("-" * 40)
