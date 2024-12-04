# test_renderer.py

import re
from block_creation import ReplacementBlock, InsertionBlock, PinkBlock, SentenceEndBlock

ANSI_COLORS = {
    'normal': '\033[0m',
    'red': '\033[31m',    # Red for deletions
    'green': '\033[92m',  # Green for replacements
    'blue': '\033[34m',   # Blue for insertions
    'pink': '\033[35m',   # Pink for ride-along text
}

def strip_ansi(text):
    """Remove ANSI escape codes from a string."""
    ansi_escape = re.compile(r'\033\[[0-9;]*m')
    return ansi_escape.sub('', text)

def calculate_ride_along(block, leading_edge):
    """
    Determine if ride-along text should be inserted for a block.
    """
    if not block.ride_along_eligible:
        return False
    return leading_edge >= block.ride_along_end

def insert_ride_along(block, leading_edge, annotated_line, final_sentence):
    """
    Insert ride-along text into the annotated line.
    """
    if isinstance(block, ReplacementBlock):
        start = block.red_end + 1  # Ride-along starts after the red text
    elif isinstance(block, InsertionBlock):
        start = block.anchor_point  # For insertion blocks, use the anchor point
    else:
        raise ValueError(f"Unsupported block type: {type(block).__name__}")

    end = block.ride_along_end
    cleaned_sentence = strip_ansi(final_sentence)
    ride_along_text = cleaned_sentence[start:end]

    while len(annotated_line) < leading_edge:
        annotated_line.append(" ")
    for char in ride_along_text:
        annotated_line.append(f"{ANSI_COLORS['pink']}{char}\033[0m")

    return end

def find_last_pink_anchor(blocks):
    """
    Find the anchor point of the last pink block in the block list.
    """
    for block in reversed(blocks):
        if isinstance(block, PinkBlock):
            return block.anchor_point
    return None

def is_orphaned_insert(block, idx, blocks):
    """
    Check if an insert block is orphaned (occurs after a SentenceEndBlock).
    """
    return isinstance(block, InsertionBlock) and idx > 0 and isinstance(blocks[idx - 1], SentenceEndBlock)

def render_corrections(final_sentence, blocks):
    """
    Render the corrected text above the original sentence using metadata from blocks.
    """
    annotated_line = []
    leading_edge = 0

    for idx, block in enumerate(blocks):
        if hasattr(block, "processed") and block.processed:
            continue

        if isinstance(block, InsertionBlock):
            corrected_text = block.insert_text
            color = ANSI_COLORS["blue"]

            if is_orphaned_insert(block, idx, blocks):
                last_pink_anchor = find_last_pink_anchor(blocks)
                if last_pink_anchor is not None:
                    block.anchor_point = last_pink_anchor
                insertion_point = max(leading_edge, block.anchor_point)
                block.processed = True
            else:
                modified_anchor_point = block.anchor_point - 1
                insertion_point = max(leading_edge, modified_anchor_point)
        elif isinstance(block, ReplacementBlock):
            corrected_text = block.replacement_text
            color = ANSI_COLORS["green"]
            insertion_point = max(leading_edge, block.anchor_point)
        else:
            continue

        while len(annotated_line) < insertion_point:
            annotated_line.append(" ")

        for char in corrected_text:
            annotated_line.append(f"{color}{char}\033[0m")

        leading_edge = insertion_point + len(corrected_text)
        if leading_edge < len(final_sentence):
            annotated_line.append(" ")
            leading_edge += 1

        if calculate_ride_along(block, leading_edge):
            leading_edge = insert_ride_along(block, leading_edge, annotated_line, final_sentence)

    return "".join(annotated_line)

def render_multiple_sentences(sentences, blocks_list):
    """
    Process and render multiple sentences with their corresponding blocks.
    """
    rendered_sentences = [] 
    for sentence_tokens, blocks in zip(sentences, blocks_list):
        final_sentence_colored = ''.join(
            f"{ANSI_COLORS.get(token['color'], '')}{token['char']}{ANSI_COLORS['normal']}" for token in sentence_tokens
        )
        annotated_line = render_corrections(final_sentence_colored, blocks)
        final_sentence_clean = ''.join(token['char'] for token in sentence_tokens)
        rendered_sentences.append((annotated_line, final_sentence_clean))  # Append results
  
    return rendered_sentences

def test_renderer(sentences, blocks_list):
    """
    Test rendering logic by integrating block creation and formatting output.
    """
    rendered_results = render_multiple_sentences(sentences, blocks_list)
    for annotated_line, final_sentence_clean in rendered_results:
        print(annotated_line)
        print(final_sentence_clean)
        print()


if __name__ == "__main__":
    test_renderer()