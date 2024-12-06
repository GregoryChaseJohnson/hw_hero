# renderer_data_loader.py

import re
from block_creation import ReplacementBlock, PinkBlock, SentenceEndBlock

ANSI_COLORS = {
    'normal': '\033[0m',
    'red': '\033[31m',
    'green': '\033[92m',
    'blue': '\033[34m',
    'pink': '\033[35m',
}



def calculate_ride_along(block, leading_edge):
    if not block.ride_along_eligible:
        return False
    required_threshold = block.ride_along_end
    return leading_edge >= required_threshold

def insert_ride_along(block, leading_edge, annotated_line, final_sentence):
    if isinstance(block, ReplacementBlock):
        start = block.red_end + 1
    else:
        raise ValueError(f"Unsupported block type: {block.type}")

    end = block.ride_along_end

    ride_along_text = final_sentence[start:end]

    # Append ride-along text to annotated_line
    while len(annotated_line) < leading_edge:
        annotated_line.append(" ")
    for char in ride_along_text:
        annotated_line.append(f"{ANSI_COLORS['pink']}{char}\033[0m")

    return end

#def find_last_pink_anchor(blocks):
    #for block in reversed(blocks):
        #if isinstance(block, PinkBlock):
            #return block.anchor_point
    #return None

#def is_orphaned_insert(block, idx, blocks):
    #return isinstance(block, InsertionBlock) and idx > 0 and isinstance(blocks[idx - 1], #SentenceEndBlock)

def render_corrections(final_sentence, blocks):
    annotated_line = []
    leading_edge = 0

    for idx, block in enumerate(blocks):
        if hasattr(block, "processed") and block.processed:
            continue

        #if isinstance(block, InsertionBlock):
            #corrected_text = block.insert_text
            #color = ANSI_COLORS["blue"]

            #if is_orphaned_insert(block, idx, blocks):
                #last_pink_anchor = find_last_pink_anchor(blocks)
                #if last_pink_anchor is not None:
                    #block.anchor_point = last_pink_anchor
                #insertion_point = max(leading_edge, block.anchor_point)
                #block.processed = True
            #else:
                #modified_anchor_point = block.anchor_point - 1
                #insertion_point = max(leading_edge, modified_anchor_point)
        elif isinstance(block, ReplacementBlock):
            corrected_text = block.replacement_text
            color = ANSI_COLORS["green"]
            insertion_point = max(leading_edge, block.anchor_point)
        else:
            continue  # Skip unsupported block types

        #if isinstance(block, InsertionBlock):
            #modified_anchor_point = block.anchor_point - 1
        #else:
            #modified_anchor_point = None

        # Ensure enough space in the annotated line
        while len(annotated_line) < insertion_point:
            annotated_line.append(" ")

        # Add corrected text
        for char in corrected_text:
            annotated_line.append(f"{color}{char}\033[0m")

        # Update leading edge
        leading_edge = insertion_point + len(corrected_text)
        if leading_edge < len(final_sentence):
            annotated_line.append(" ")
            leading_edge += 1

        # Determine if ride-along text should be inserted
        ride_along_required = calculate_ride_along(block, leading_edge)

        if ride_along_required:
            ride_along_text = final_sentence[block.red_end + 1:block.ride_along_end] if isinstance(block, ReplacementBlock) else final_sentence[block.anchor_point:block.ride_along_end]
            leading_edge = insert_ride_along(block, leading_edge, annotated_line, final_sentence)

    return "".join(annotated_line)

def process_sentences(data_loader):
    """
    Process and render multiple tokenized sentences and their blocks.

    Parameters:
    - data_loader: An instance of DataLoader providing sentences and blocks.
    """
    sentence_count = 1
    for final_sentence, blocks in data_loader:
        print(f"Sentence {sentence_count}:")
        annotated_line = render_corrections(final_sentence, blocks)
        print(annotated_line)               # Rendered corrections above
        print(final_sentence)   # Original sentence below
        print()                              # Blank line for separation
        sentence_count += 1
