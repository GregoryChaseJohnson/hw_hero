import pickle
from renderer import apply_colors

class Block:
    """
    Represents a red block and its associated replacement text.
    """
    def __init__(self, block_id, red_start, red_end, replacement_text=None):
        self.block_id = block_id  # Numerical identifier
        self.red_start = red_start
        self.red_end = red_end
        self.replacement_text = replacement_text if replacement_text else []

    def compute_overhang(self):
        """
        Calculate overhang as (len(replacement_text) - block_length).
        """
        block_length = self.red_end - self.red_start + 1
        # Overhang is based on how many tokens exceed the block_length
        return max(len(self.replacement_text) - block_length, 0)

    def __str__(self):
        repl_str = "".join([t['char'] for t in self.replacement_text]) if self.replacement_text else "None"
        return f"Block(id={self.block_id}, red_start={self.red_start}, red_end={self.red_end}, replacement_text='{repl_str}')"


def identify_red_blocks(final_sentence):
    """
    Identify red blocks allowing a single space inside the block.
    Red tokens define a block. A single space is allowed within a block.
    More than one consecutive space or a non-red, non-space token ends the block.
    """
    def is_red(token):
        return token.get('color', 'normal') == 'red'
    def is_space_char(token):
        return token['char'].isspace()

    def add_block(blocks, start, end):
        if start is not None and end is not None and end >= start:
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
                # More than one consecutive space ends the block
                add_block(blocks, block_start, idx - space_count)
                block_start = None
                space_count = 0
        else:
            # Non-red, non-space ends the block
            add_block(blocks, block_start, idx - 1 - space_count)
            block_start = None
            space_count = 0

    # Close any remaining block
    add_block(blocks, block_start, len(final_sentence) - 1 - space_count)

    return blocks

def get_green_search_area(red_blocks, current_block_index, annotated_line_length):
    """
    Determine the search area for a given red block.
    """
    search_start = red_blocks[current_block_index]['block_start']
    if current_block_index + 1 < len(red_blocks):
        search_end = red_blocks[current_block_index + 1]['block_start']
    else:
        search_end = annotated_line_length
    if search_end < search_start:
        search_end = search_start
    return search_start, search_end

def extract_replacement_text(annotated_line, red_blocks, block_index):
    search_start, search_end = get_green_search_area(red_blocks, block_index, len(annotated_line))
    segment = annotated_line[search_start:search_end]

    collected = []
    consecutive_spaces = 0

    for token in segment:
        col = token.get('color', 'normal')
        ch = token['char']

        if col == 'replacement':
            consecutive_spaces = 0
            collected.append(token)
        elif col == 'normal' and ch.isspace():
            if collected:
                consecutive_spaces += 1
                if consecutive_spaces == 1:
                    collected.append(token)
                else:
                    # Two consecutive spaces -> stop collecting
                    collected = collected[:-1]
                    break
            # else ignore spaces before any replacement token
        else:
            # Any other token breaks the sequence
            break

    # Trim trailing spaces at the end of collected tokens if any
    while collected and collected[-1]['char'].isspace():
        collected.pop()

    return collected

def define_blocks(annotated_line, final_sentence):
    """
    Define red blocks and associate replacement text.
    """
    red_blocks = identify_red_blocks(final_sentence)
    blocks = []

    for i, rb in enumerate(red_blocks):
        replacement_text = extract_replacement_text(annotated_line, red_blocks, i)
        blocks.append(Block(i, rb['block_start'], rb['block_end'], replacement_text))

    return blocks

def insert_spaces(final_sentence, blocks):
    """
    Insert spaces into the final sentence based on overhang,
    and then adjust subsequent blocks' positions accordingly.
    """
    # We'll process blocks in order, updating final_sentence and subsequent blocks as we go.
    for i, block in enumerate(blocks):
        overhang = block.compute_overhang()
        if overhang > 0:
            insertion_point = block.red_end + 1
            spaces = [{'char': ' ', 'color': 'normal'}] * overhang
            final_sentence = final_sentence[:insertion_point] + spaces + final_sentence[insertion_point:]

            # Update this block's final_sentence indices are stable, but we must shift subsequent blocks.
            # Since we inserted 'overhang' spaces at insertion_point, all tokens after insertion_point move right.
            # This means every subsequent block with indices beyond block.red_end must shift by 'overhang'.
            for j in range(i + 1, len(blocks)):
                blocks[j].red_start += overhang
                blocks[j].red_end += overhang

    return final_sentence


def place_replacement_text(blocks, annotated_line_length):
    """
    Place replacement text on the annotated line.
    """
    annotated_line = [{'char': ' ', 'color': 'normal'} for _ in range(annotated_line_length)]

    for block in blocks:
        for idx, token in enumerate(block.replacement_text):
            target_idx = block.red_start + idx
            if target_idx < len(annotated_line):
                annotated_line[target_idx] = token

    return annotated_line

def finalize_transformation(annotated_lines, final_sentences):
    """
    Perform the final transformation for each sentence.
    """
    for i, (annotated_line, final_sentence) in enumerate(zip(annotated_lines, final_sentences)):
        print(f"\n--- Sentence {i + 1} ---")

        # Print initial tokens
        print("Initial Final Sentence Tokens:")
        for idx, tok in enumerate(final_sentence):
            print(f"  {idx}: {tok}")

        # Define blocks and associate replacement text
        blocks = define_blocks(annotated_line, final_sentence)

        # Print initial block information and overhang
        print("Initial Blocks and Overhang:")
        for block in blocks:
            print(block)
            print("Overhang:", block.compute_overhang())

        # Insert spaces based on overhang
        final_sentence = insert_spaces(final_sentence, blocks)

        # Print final sentence after spaces insertion
        print("\nFinal Sentence After Spaces Insertion:")
        for idx, tok in enumerate(final_sentence):
            print(f"  {idx}: {tok}")

        # Print updated blocks
        print("\nUpdated Blocks and Overhang:")
        for block in blocks:
            print(block)
            print("Overhang:", block.compute_overhang())

        # Place replacement text after adjusting positions
        annotated_line = place_replacement_text(blocks, len(final_sentence))

        # Print results
        print("\nFinal Annotated Line (Colored):")
        print(apply_colors(annotated_line))
        # Print final sentence tokens in colored form
        print(apply_colors(final_sentence))

if __name__ == "__main__":
    with open("post_processed_output.pkl", "rb") as f:
        data = pickle.load(f)
        annotated_lines = data["annotated_lines"]
        final_sentences = data["final_sentences"]

    finalize_transformation(annotated_lines, final_sentences)
