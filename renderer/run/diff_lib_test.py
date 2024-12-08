import re
import difflib
from typing import List, Tuple
from seq_alignment import align_sentences

# Define the special marker
COMBINATION_MARKER = "^``^"

def generate_report(matches: List[Tuple[str, str]]) -> str:
    """
    Generate a report of changes with sentence numbers and color formatting.
    Remove markers before producing the final report.
    """
    report = []
    tokenized_output = []  # To store tokenized sentences
    for num, (original, corrected) in enumerate(matches, 1):
        # Highlight changes
        highlighted = highlight_changes(original, corrected)
        # Remove markers after processing
        cleaned_highlighted = highlighted.replace(COMBINATION_MARKER, "")
        report.append(f"Sentence {num}:\n{cleaned_highlighted}")
        
        # Tokenize the cleaned output for block creation
        tokenizer = TextTokenizer(cleaned_highlighted)
        tokenized_output.extend(tokenizer.parse_text())
    return "\n\n".join(report), tokenized_output

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words, spaces, and punctuation.
    """
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*(?:\.[A-Za-z]+)*(?:[.,!?;:]+)?|\s+|[^\w\s]", text)

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

def highlight_changes(original: str, corrected: str) -> str:
    """
    Highlight differences between original and corrected sentences.
    """
    orig_tokens = tokenize(original)
    corr_tokens = tokenize(corrected)
    return align_and_highlight(orig_tokens, corr_tokens)

def test_single_example(ocr_text: str, corrected_text: str):
    """
    Test with the output from the sequence alignment script.
    """
    print("Aligning sentences using sequence alignment...")
    matches = align_sentences(ocr_text, corrected_text)

    print("\nGenerating report...")
    report = generate_report(matches)

    # Print the final cleaned report
    print("\nFinal Report:")
    print(report)

def process_text(ocr_text: str, corrected_text: str):
    """
    Process text using seq_alignment output and generate a report.
    """
    print("Aligning sentences...")
    matches = align_sentences(ocr_text, corrected_text)

    print("\nGenerating report...")
    report = generate_report(matches)
    print(report)

    return report

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

if __name__ == "__main__":
    # Hard-coded examples for testing
    ocr_text = "Actually when I was touring around Southeast Asia, I didn't have enough time and money so I couldn't go to Bali."
    corrected_text = "When I was touring around Southeast Asia, I didn’t have enough time or money.^``^ So I couldn’t go to Bali."
    test_single_example(ocr_text, corrected_text)
