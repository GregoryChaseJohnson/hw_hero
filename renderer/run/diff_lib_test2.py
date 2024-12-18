import re
import difflib
from typing import List, Tuple
from seq_alignment_reverse import align_sentences
import pickle

ANSI_COLORS = {
    'normal': '\033[0m',
    'red': '\033[91m',
    'green': '\033[92m',
    'blue': '\033[94m',
    'pink': '\033[95;1m',
}


# Define the special marker
COMBINATION_MARKER = "^**^"

def remove_combination_marker(tokens: List[dict], marker: str) -> List[dict]:
    """
    Remove tokens matching the COMBINATION_MARKER from the token list.
    Handles cases where the marker spans multiple tokens.
    """
    marker_chars = list(marker)  # ['^', '*', '*', '^']
    filtered_tokens = []
    i = 0

    while i < len(tokens):
        # Check if the current slice matches the marker
        if (
            i + len(marker_chars) <= len(tokens) and
            all(tokens[i + j]['char'] == marker_chars[j] for j in range(len(marker_chars))) 
        ):
            # Skip the entire marker span
            i += len(marker_chars)
        else:
            # Retain non-marker tokens
            filtered_tokens.append(tokens[i])
            i += 1

    return filtered_tokens



# Utility functions
def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words, spaces, and punctuation.
    """

    return re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)*|\.\w+|[.,!?;:]+|\s+|[^\w\s]", text)



def align_and_highlight(original: List[str], corrected: List[str]) -> str:
    """
    Align tokens between original and corrected sentences and highlight changes.
    """
    sm = difflib.SequenceMatcher(None, original, corrected)
    highlighted = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            highlighted.extend(corrected[j1:j2])
        elif tag == 'replace':
            highlighted.extend(f"\033[91m{token}\033[0m" for token in original[i1:i2])  # Red for deletions
            highlighted.extend(f"\033[92m{token}\033[0m" for token in corrected[j1:j2])  # Green for additions
        elif tag == 'delete':
            highlighted.extend(f"\033[95;1m{token}\033[0m" for token in original[i1:i2])  # Magenta for deletions
        elif tag == 'insert':
            highlighted.extend(f"\033[94m{token}\033[0m" for token in corrected[j1:j2])  # Blue for additions
    return ''.join(highlighted)


def normalize_apostrophes(text: str) -> str:
    """
    Replace curly and inconsistent apostrophes with straight apostrophes for consistent tokenization.
    """
    return text.replace('‘', "'").replace('’', "'").replace('‛', "'").replace('`', "'").replace('´', "'")

def highlight_changes(original: str, corrected: str) -> str:
    """
    Highlight differences between original and corrected sentences.
    Ensure apostrophes are normalized before processing.
    """
    original = normalize_apostrophes(original)
    corrected = normalize_apostrophes(corrected)
    orig_tokens = tokenize(original)
    corr_tokens = tokenize(corrected)
    return align_and_highlight(orig_tokens, corr_tokens)


# Tokenizer class
class TextTokenizer:
    def __init__(self, text: str):
        """
        Initialize the tokenizer with the input text.
        """
        self.text = text  # Store the input text
        self.red_start = "\033[91m"  # Red for replaced (incorrect original)
        self.green_start = "\033[92m"  # Green for replaced (corrected text)
        self.blue_start = "\033[94m"  # Blue for insertions
        self.pink_start = "\033[95;1m"  # Bright magenta (pink) for deletions
        self.color_end = "\033[0m"  # Reset color
        self.tokens = []

    def parse_text(self) -> List[dict]:
        """
        Tokenizes the input text into characters with associated colors and assigns indices.
        Ensures blue tokens remain blue, and spaces between contiguous blocks inherit the block's color.
        """
        pattern = re.compile(r'(\033\[\d+;?\d*m|\s+|\w+|[^\w\s])')
        split_text = pattern.findall(self.text)

        current_color = 'normal'
        token_index = 0

        for token in split_text:
            if token == self.red_start:
                current_color = 'red'
            elif token == self.green_start:
                current_color = 'green'
            elif token == self.blue_start:
                current_color = 'blue'
            elif token == self.pink_start:
                current_color = 'pink'
            elif token == self.color_end:
                current_color = 'normal'
            else:
                for char in token:
                    if char == ' ':
                        self.tokens.append({'index': token_index, 'char': char, 'color': 'normal'})
                    else:
                        self.tokens.append({'index': token_index, 'char': char, 'color': current_color})
                    token_index += 1

        for i in range(1, len(self.tokens) - 1):
            current_token = self.tokens[i]
            prev_token = self.tokens[i - 1]
            next_token = self.tokens[i + 1]

            if current_token['char'] == ' ' and prev_token['color'] == next_token['color'] and prev_token['color'] != 'normal':
                current_token['color'] = prev_token['color']

        return self.tokens

    def get_colored_text(self) -> str:
        """
        Reconstruct the colored text from tokens.
        """
        colored_text = ""
        for token in self.tokens:
            if token['color'] == 'red':
                colored_text += self.red_start + token['char'] + self.color_end
            elif token['color'] == 'green':
                colored_text += self.green_start + token['char'] + self.color_end
            elif token['color'] == 'blue':
                colored_text += self.blue_start + token['char'] + self.color_end
            elif token['color'] == 'pink':
                colored_text += self.pink_start + token['char'] + self.color_end
            else:
                colored_text += token['char']
        return colored_text


# Main report generation
def generate_report(matches: List[Tuple[str, str]]) -> Tuple[str, List[dict]]:
    """
    Generate a report of changes with sentence numbers and color formatting.
    Use TextTokenizer to clean and structure the output, removing markers and preserving formatting.
    """
    report = []  # To store cleaned sentences
    tokenized_output = []  # To store tokenized sentences for further use

    for num, (original, corrected) in enumerate(matches, 1):
        # Normalize apostrophes before highlighting changes
        original = normalize_apostrophes(original)
        corrected = normalize_apostrophes(corrected)

        # Highlight differences between original and corrected sentences
        highlighted = highlight_changes(original, corrected)

        # Use TextTokenizer to parse the highlighted text into structured tokens
        tokenizer = TextTokenizer(highlighted)
        tokens = tokenizer.parse_text()

        # Remove the combination marker from tokens
        filtered_tokens = remove_combination_marker(tokens, COMBINATION_MARKER)

        # Rebuild the cleaned text with preserved colors
        cleaned_highlighted = ''.join(
            f"{ANSI_COLORS.get(token['color'], '')}{token['char']}" for token in filtered_tokens
        )
        cleaned_highlighted += ANSI_COLORS['normal']  # Reset color at the end

        # Append the cleaned sentence to the report
        report.append(f"Sentence {num}:\n{cleaned_highlighted}")

        # Add the filtered tokens to the tokenized output for downstream processing
        tokenized_output.append(filtered_tokens)

    return "\n\n".join(report), tokenized_output


# Core processing functions
def process_text(ocr_text: str, corrected_text: str):
    print("Aligning sentences...")
    matches = align_sentences(ocr_text, corrected_text)

    print("\nGenerating report...")
    formatted_report, tokenized_output = generate_report(matches)  # Get tokenized_output here
    print("\nFormatted Report:")
    print(formatted_report)

    # Add this block

    with open("tokenized_output.pkl", "wb") as f:
        pickle.dump(tokenized_output, f)
    print("tokenized_output saved to tokenized_output.pkl")

    return formatted_report


if __name__ == "__main__":
    ocr_text = "Actually when I was touring around Southeast Asia, I didn't have enough time and money so, I couldn't go to Bali."
    corrected_text = "When I was touring around Southeast Asia, I didn’t have enough time or money.^``^ So I couldn’t go to Bali."
    
    process_text(ocr_text, corrected_text)




