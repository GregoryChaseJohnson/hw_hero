import sys
import re 

sys.path.append('/home/keithuncouth/red_pen_app/renderer')  # Adjust path to your `renderer` directory

from tokenizer import TextTokenizer
from block_creation import create_blocks
from script_runner import generate_report_from_script

ANSI_COLORS = {
    'normal': '\033[0m',
    'red': '\033[31m',
    'green': '\033[92m',
    'blue': '\033[34m',
    'pink': '\033[35m',
}

def strip_ansi(text):
    ansi_escape = re.compile(r'\033\[[0-9;]*m')
    return ansi_escape.sub('', text)

def calculate_ride_along(block, leading_edge):
    """
    Determine if ride-along text should be inserted for a block.

    Parameters:
    - block (Block): The block being processed.
    - leading_edge (int): Current position after corrected text and space.

    Returns:
    - bool: True if ride-along should occur, False otherwise.
    """
    if not block.ride_along_eligible:
        return False

    # Ensure leading_edge reflects the corrected text
    required_threshold = block.ride_along_end
    return leading_edge >= required_threshold

def insert_ride_along(block, leading_edge, annotated_line, final_sentence):
    """
    Insert ride-along text into the annotated line.

    Parameters:
    - block: Current block being processed (ReplacementBlock or InsertionBlock).
    - leading_edge: Current position after inserting corrected text and space.
    - annotated_line: Line being annotated with corrections.
    - final_sentence: The complete sentence for reference.

    Returns:
    - Updated leading_edge after inserting ride-along text.
    """
    # Define start and end based on block type
    if block.type == "replace":
        start = block.red_end + 1  # Ride-along starts after the red text
    elif block.type == "insert":
        start = block.anchor_point  # For insertion blocks, use the anchor point
    else:
        raise ValueError(f"Unsupported block type: {block.type}")

    # Ride-along end is always defined in block metadata
    end = block.ride_along_end

    # Extract ride-along text
    cleaned_sentence = strip_ansi(final_sentence)
    ride_along_text = cleaned_sentence[start:end]

    # Debug: Show the extracted ride-along text
    print(f"DEBUG: Ride-Along Text for Block: '{ride_along_text}' (Start: {start}, End: {end})")

    if annotated_line and annotated_line[-1] == " " and ride_along_text.startswith(" "):
        ride_along_text = ride_along_text[1:]  # Trim the leading space from the ride-along

    # Append ride-along text to annotated_line
    while len(annotated_line) < leading_edge:
        annotated_line.append(" ")  # Ensure alignment
    for char in ride_along_text:
        annotated_line.append(f"{ANSI_COLORS['green']}{char}\033[0m")

    # Return the updated leading_edge
    return end

def is_connected_to_previous_block(current_block, previous_block):
    """
    Determine if the current block is connected to the previous block.

    Parameters:
    - current_block: The block currently being processed.
    - previous_block: The block processed previously.

    Returns:
    - bool: True if the blocks are connected, False otherwise.
    """
    if not previous_block:
        return False  # No previous block, so not connected

    prev_end = (
        previous_block.red_end if previous_block.type == "replace" else previous_block.anchor_point
    )
    return prev_end + 2 == current_block.anchor_point


def render_corrections(final_sentence, blocks):
    """
    Render the corrected text above the original sentence using metadata from blocks.
    """
    # Annotated line starts empty and grows according to block metadata
    annotated_line = []

    # Track the leading edge for placement
    leading_edge = 0

    for idx, block in enumerate(blocks):

        previous_block = blocks[idx - 1] if idx > 0 else None

        if is_connected_to_previous_block(block, previous_block):
            insertion_point = leading_edge  # Align with leading edge if connected
        else:
        # Step 1: Calculate the modified anchor point for insert blocks
            if block.type == "insert":
                modified_anchor_point = block.anchor_point - 1  # Shift one position left
                insertion_point = max(leading_edge, modified_anchor_point)
            elif block.type == "replace":
                insertion_point = max(leading_edge, block.anchor_point)
            else:
                continue

        # DEBUG: Check insertion point logic
        print(f"DEBUG: Block {idx}: Type={block.type}, Anchor={block.anchor_point}, "
              f"Modified Anchor={modified_anchor_point if block.type == 'insert' else 'N/A'}, "
              f"Insertion Point={insertion_point}, Leading Edge={leading_edge}")

        # Step 2: Get corrected text and its color
        if block.type == "replace":
            corrected_text = block.replacement_text
            color = ANSI_COLORS["green"]
        elif block.type == "insert":
            corrected_text = block.insert_text
            color = ANSI_COLORS["blue"]

        # Step 3: Ensure enough space in the annotated line
        while len(annotated_line) < insertion_point:
            annotated_line.append(" ")

        # Step 4: Add corrected text
        for char in corrected_text:
            annotated_line.append(f"{color}{char}\033[0m")

        # Step 5: Update leading edge
        leading_edge = insertion_point + len(corrected_text)
        if leading_edge < len(final_sentence):
            annotated_line.append(" ")
            leading_edge += 1 
    
        # Step 6: Debug print for ride-along
        ride_along_required = calculate_ride_along(block, leading_edge)
        print(
            f"DEBUG: Block {idx}: Type={block.type}, Anchor={block.anchor_point}, "
            f"Modified Anchor={modified_anchor_point if block.type == 'insert' else 'N/A'}, "
            f"Insertion Point={insertion_point}, Leading Edge={leading_edge}, "
            f"Red End={block.red_end if block.type == 'replace' else 'N/A'}, "
            f"Ride-Along End={block.ride_along_end if block.ride_along_eligible else 'N/A'}, "
            f"Ride-Along Required={'Yes' if ride_along_required else 'No'}"
        )

        # Step 7: Insert ride-along text if required
        if ride_along_required:
            # Gather the ride-along text
            ride_along_text = final_sentence[block.red_end:block.ride_along_end]

            # Insert the ride-along text using the helper function
            leading_edge = insert_ride_along(
                block, leading_edge, annotated_line, final_sentence
            )


    return "".join(annotated_line)


def test_renderer():
    """
    Test rendering logic by integrating block creation and formatting output.
    """
    # Generate raw text using DiffLib parser
    raw_output = generate_report_from_script()
    if not raw_output.strip():
        print("Error: No output from script.")
        return

    # Tokenize and create blocks
    tokenizer = TextTokenizer(raw_output)
    tokens = tokenizer.parse_text()
    blocks = create_blocks(tokens)

    # Construct the final sentence
    final_sentence = ''.join(
        f"{ANSI_COLORS.get(token['color'], '')}{token['char']}" for token in tokens
    )
    final_sentence += '\033[0m'  # Reset color

    # Render the corrections above the final sentence
    annotated_line = render_corrections(final_sentence, blocks)

    # Print the annotated line and final sentence with proper spacing
    print(annotated_line)  # Annotated line (above)
    print(final_sentence)  # Final sentence (below)

if __name__ == "__main__":
    test_renderer()
