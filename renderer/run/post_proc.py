from block_creation import ReplacementBlock
from renderer import apply_colors, render_corrections

class Block:
    """
    Represents a block with red text (final sentence) and its associated green text search area (annotated line).
    """
    def __init__(self, red_start, red_end, search_start, search_end):
        self.red_start = red_start
        self.red_end = red_end
        self.search_start = search_start
        self.search_end = search_end

    def extract_green_segment(self, annotated_line):
        """t
        Extract the green text segment for this block without modifying the line.
        """
        return annotated_line[self.search_start:self.search_end]

    def transform_green_segment(self, segment):
        """
        Reduce spaces in the green text segment using the space-reduction logic.
        """
        return reduce_extra_spaces(segment)

    def validate(self):
        """
        Optional debug info for block boundaries.
        """
        print(f"[DEBUG] Block Red: Start={self.red_start}, End={self.red_end}, "
              f"Green: Start={self.search_start}, End={self.search_end}")

def find_red_blocks(final_sentence):
    def is_red(token):
        return token['color'] == 'red'
    
    def is_space_char(token):
        return token['char'] == ' '
    
    def add_block(blocks, start, end):
        if start is not None and end >= start:
            blocks.append({'block_start': start, 'block_end': end})

    blocks = []
    block_start = None
    space_count = 0

    for idx, token in enumerate(final_sentence):
        if is_red(token):
            if block_start is None:
                block_start = idx
            space_count = 0
        elif is_space_char(token):
            space_count += 1
            if space_count > 1:
                # More than one space breaks the block before these spaces
                add_block(blocks, block_start, idx - space_count)
                block_start = None
                space_count = 0
        else:
            # Non-red, non-space ends the block before this token
            add_block(blocks, block_start, idx - 1 - space_count)
            block_start = None
            space_count = 0

    # Close any remaining block
    add_block(blocks, block_start, len(final_sentence) - 1 - space_count)
    return blocks

def get_green_search_area(red_blocks, current_block_index, annotated_line_length):
    """
    Determine the search area for a given red block in the annotated line.
    """
    search_start = red_blocks[current_block_index]['block_start']
    if current_block_index + 1 < len(red_blocks):
        search_end = red_blocks[current_block_index + 1]['block_start']
    else:
        search_end = annotated_line_length
    if search_end < search_start:
        search_end = search_start
    return search_start, search_end

def reduce_extra_spaces(tokens):
    """
    Reduce consecutive spaces to a single space, without merging non-space tokens.
    Prevent leading spaces by only adding a space if there's already something in result.
    """
    result = []
    last_was_space = False
    for token in tokens:
        if token['char'].isspace():
            # Only add a space if we already have some tokens in result (no leading space)
            if not last_was_space and result:
                result.append(token)
                last_was_space = True
        else:
            result.append(token)
            last_was_space = False
    return result

def insert_transformed_segment(new_annotated_line, red_start, transformed_segment):
    """
    Insert transformed_segment at red_start in new_annotated_line, extending if needed.
    """
    required_length = red_start + len(transformed_segment)
    current_length = len(new_annotated_line)


    for i, token in enumerate(new_annotated_line[:red_start+20]):  # Show up to 20 chars after red_start
        print(f"  {i}: char='{token['char']}', color='{token['color']}'")
    print("[DEBUG] Transformed segment to insert:", ''.join([t['char'] for t in transformed_segment]))

    # Extend line if needed
    if current_length < required_length:
        extension_size = required_length - current_length
        new_annotated_line.extend([{'char': ' ', 'color': 'normal'}] * extension_size)
        print(f"[DEBUG] Extended line by {extension_size} spaces. New length={len(new_annotated_line)}")

    # Perform insertion
    for i, token in enumerate(transformed_segment):
        new_annotated_line[red_start + i] = token

    # Verify what we inserted
    inserted_text = ''.join([t['char'] for t in new_annotated_line[red_start:red_start + len(transformed_segment)]])
    print(f"[DEBUG] Inserted segment at red_start={red_start}, claimed_length={len(transformed_segment)}")
    print(f"[DEBUG] Actual inserted text at [{red_start}:{red_start + len(transformed_segment)}]: '{inserted_text}'")

    return new_annotated_line

def process_sentence(annotated_line, final_sentence):
    """
    Process a single sentence:
    1. Find red blocks and their search areas.
    2. Print block boundaries.
    3. Extract and transform each block’s segment independently.
    4. After all transformations, rebuild the annotated line once at the correct red_start positions.
    """
    red_blocks = find_red_blocks(final_sentence)

    print("[DEBUG] Block Boundaries:")
    for idx, red_block in enumerate(red_blocks):
        search_start, search_end = get_green_search_area(red_blocks, idx, len(annotated_line))
        print(f"  Block {idx}: red_start={red_block['block_start']}, red_end={red_block['block_end']} | "
              f"search_start={search_start}, search_end={search_end}")

    # Extract and transform all segments first
    transformed_segments = []
    for idx, red_block in enumerate(red_blocks):
        search_start, search_end = get_green_search_area(red_blocks, idx, len(annotated_line))
        block = Block(red_block['block_start'], red_block['block_end'], search_start, search_end)
        segment = block.extract_green_segment(annotated_line)
        transformed_segment = block.transform_green_segment(segment)
        # Store just red_start and the transformed segment (we no longer need original_length)
        transformed_segments.append((block.red_start, transformed_segment))

    # Rebuild the annotated line from scratch
    if transformed_segments:
        new_annotated_line = []
        # Insert each transformed segment exactly at its red_start
        for (red_start, transformed_segment) in transformed_segments:
            new_annotated_line = insert_transformed_segment(new_annotated_line, red_start, transformed_segment)

        # Print the final rebuilt line for debugging
        print("[DEBUG] Final Rebuilt Annotated Line Tokens:")
        for i, t in enumerate(new_annotated_line):
            print(f"  {i}: char='{t['char']}', color='{t['color']}'")

        annotated_line = new_annotated_line

    return annotated_line

def post_process(annotated_lines, final_sentences, blocks_by_sentence):
    """
    Post-process each sentence using the described approach.
    """
    for i, (annotated_line, final_sentence, blocks) in enumerate(zip(annotated_lines, final_sentences, blocks_by_sentence)):
        print(f"\n--- Sentence {i + 1} ---")

        # Print final sentence tokens before processing
        print("Final Sentence Tokens:")
        for idx, t in enumerate(final_sentence):
            print(f"  {idx}: char='{t['char']}', color='{t['color']}'")

        # Print annotated line tokens before transformations
        print("Annotated Tokens Before:")
        for idx, t in enumerate(annotated_line):
            print(f"  {idx}: char='{t['char']}', color='{t['color']}'")

        # Process the sentence with the new method
        annotated_line = process_sentence(annotated_line, final_sentence)

        updated_data = {
            "annotated_lines": annotated_lines,
            "final_sentences": final_sentences,
            "blocks_by_sentence": blocks_by_sentence
        }

        with open("post_processed_output.pkl", "wb") as f:
            pickle.dump(updated_data, f)

        print("Updated data written to post_processed_output.pkl")

        # Print the updated annotated line (colored)
        print("Updated Annotated Line (Colored):")
        print(apply_colors(annotated_line))

        # Print the final sentence (colored)
        
        print(apply_colors(final_sentence))

if __name__ == "__main__":
    import pickle
    # Load data from renderer_output.pkl without changes
    with open("renderer_output.pkl", "rb") as f:
        data = pickle.load(f)
        annotated_lines = data["annotated_lines"]
        final_sentences = data["final_sentences"]
        blocks_by_sentence = data["blocks_by_sentence"]

    # Print tokens for inspection before processing
    print("=== Annotated Lines Tokens ===")
    for i, line in enumerate(annotated_lines):
        print(f"\nAnnotated line {i}:")
        for idx, token in enumerate(line):
            print(f"  {idx}: {token}")

    print("=== Final Sentences Tokens ===")
    for i, sentence in enumerate(final_sentences):
        print(f"\nFinal sentence {i}:")
        for idx, token in enumerate(sentence):
            print(f"  {idx}: {token}")

    # Now call post_process as before
    post_process(annotated_lines, final_sentences, blocks_by_sentence)
