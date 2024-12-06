import re
import difflib
from typing import List, Tuple
from seq_alignment import align_sentences

def generate_report(matches: List[Tuple[str, str]]) -> str:
    """
    Generate a report of changes with sentence numbers and color formatting.
    """
    report = []
    for num, (original, corrected) in enumerate(matches, 1):
        highlighted = highlight_changes(original, corrected)
        report.append(highlighted)
    return "\n\n".join(report)

def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences, ensuring proper handling of sentence-ending punctuation.
    """
    abbreviations = r'\b(?:etc|e\.g|i\.e|vs|Dr|Mr|Mrs|Ms|Prof|Jr|Sr)\.'
    text = re.sub(fr'({abbreviations})', r'\1<PROTECTED>', text)

    sentence_endings = r'([.!?](?:"|\')?(?:[\)\]]+)?\s+|\n\n)' # Matches punctuation with optional quotes
    tokens = re.split(sentence_endings, text)

    sentences = []
    buffer = ""
    for token in tokens:
        buffer += token
        if re.search(sentence_endings, token):
            sentences.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        sentences.append(buffer.strip())

    sentences = [re.sub(r'\.<PROTECTED>', '.', s) for s in sentences]
    sentences = [s.replace('<PROTECTED>', '.') for s in sentences]

    return sentences

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words, spaces, and punctuation separately.
    """
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*(?:\.[A-Za-z]+)*(?:[.,!?;:]+)?|\s+|[^\w\s]", text)


def align_and_highlight(original: List[str], corrected: List[str]) -> str:
    """
    Align tokens between original and corrected sentences and highlight changes.
    Single and double quotes are treated as equivalent.
    """
    # Normalize quotes by replacing all single quotes with double quotes for comparison
    normalized_original = ['"' if c in {"'", '"'} else c for c in original]
    normalized_corrected = ['"' if c in {"'", '"'} else c for c in corrected]
    
    sm = difflib.SequenceMatcher(None, normalized_original, normalized_corrected)
    highlighted = []
    
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            highlighted.extend(corrected[j1:j2])
        elif tag == 'replace':
            highlighted.extend(f"\033[91m{token}\033[0m" for token in original[i1:i2])  # Red for deletions
            highlighted.extend(f"\033[92m{token}\033[0m" for token in corrected[j1:j2])  # Green for additions
        elif tag == 'delete':
            highlighted.extend(f"\033[95;1m{token}\033[0m" for token in original[i1:i2])
        elif tag == 'insert':
            highlighted.extend(f"\033[94m{token}\033[0m" for token in corrected[j1:j2])
    
    return ''.join(highlighted)


def highlight_changes(original: str, corrected: str) -> str:
    """
    Tokenize sentences and highlight changes using structured alignment.
    """
    if not original:
        return f"\033[94m{corrected}\033[0m"  # Blue for additions
    elif not corrected:
        return f"\033[93m{original}\033[0m"  # Yellow for deletions
    else:
        orig_tokens = tokenize(original)
        corr_tokens = tokenize(corrected)
        return align_and_highlight(orig_tokens, corr_tokens)

# Main function to consume data from seq_alignment and process it
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

# --- TextTokenizer Class Integration ---

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
        # Improved regex to split cleanly into ANSI codes, spaces, and tokens
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
                # Process each character in the token
                for char in token:
                    if char == ' ':
                        # Spaces are always normal initially
                        self.tokens.append({'index': token_index, 'char': char, 'color': 'normal'})
                    else:
                        # All other characters inherit the current color
                        self.tokens.append({'index': token_index, 'char': char, 'color': current_color})
                    token_index += 1

        # Post-processing loop to fix spaces between contiguous blocks
        for i in range(1, len(self.tokens) - 1):
            current_token = self.tokens[i]
            prev_token = self.tokens[i - 1]
            next_token = self.tokens[i + 1]

            # Check if the current token is a space and its neighbors have the same color
            if current_token['char'] == ' ' and prev_token['color'] == next_token['color'] and prev_token['color'] != 'normal':
                # Inherit the color of the neighbors
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