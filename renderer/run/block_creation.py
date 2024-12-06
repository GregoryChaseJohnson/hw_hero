class ReplacementBlock:
    def __init__(self, anchor_point, red_end, red_text, replacement_text):
        self.type = 'replace'
        self.anchor_point = anchor_point
        self.red_end = red_end
        self.red_text = red_text
        self.replacement_text = replacement_text
        self.ride_along_end = None
        self.ride_along_eligible = False
        self.actual_start = None
        self.actual_end = None


class PinkBlock:
    def __init__(self, anchor_point):
        self.type = 'pink'
        self.anchor_point = anchor_point


class SentenceEndBlock:
    def __init__(self, anchor_point):
        self.type = 'sentence_end'
        self.anchor_point = anchor_point


SENTENCE_END_PUNCTUATION = ['.', '!', '?', '...', '"', "'"]

def is_sentence_end(tokens, index):
    """Check if the current token marks the end of a sentence."""
    if index + 2 >= len(tokens):
        return False
    return (
        tokens[index + 1]['char'] in SENTENCE_END_PUNCTUATION
        and tokens[index + 2]['char'] == '\n'
        and tokens[index + 1]['color'] == 'normal'
        and tokens[index + 2]['color'] == 'normal'
    )

def create_blocks(tokens):
    """
    Create blocks from tokenized text, handling only replacement and pink blocks.
    """
    blocks = []
    i = 0

    while i < len(tokens):
        # Handle replacement blocks
        if tokens[i]['color'] == 'red':
            anchor_point = i
            red_text = ""
            replacement_text = ""
            red_end = None

            print(f"Starting replacement block at index {anchor_point}")

            # Collect red text
            while i < len(tokens) and tokens[i]['color'] == 'red':
                red_text += tokens[i]['char']
                red_end = i
                i += 1

            # Collect green text (replacement)
            if i < len(tokens) and tokens[i]['color'] == 'green':
                green_start = i
                while i < len(tokens) and tokens[i]['color'] == 'green':
                    replacement_text += tokens[i]['char']
                    i += 1

                print(f"Collected green text: '{replacement_text}'")

                del tokens[green_start:i]
                i = green_start  # Reset i to account for removed tokens

            # Create replacement block
            blocks.append(ReplacementBlock(anchor_point, red_end, red_text, replacement_text))

        # Handle pink blocks
        elif tokens[i]['color'] == 'pink':
            anchor_point = i
            print(f"Starting pink block at index {anchor_point}")

            # Skip over contiguous pink tokens
            while i < len(tokens) and tokens[i]['color'] == 'pink':
                i += 1

            blocks.append(PinkBlock(anchor_point))

        # Handle sentence-end blocks
        elif is_sentence_end(tokens, i):
            anchor_point = i
            print(f"Creating sentence end block at index {anchor_point}")
            blocks.append(SentenceEndBlock(anchor_point))
            i += 2  # Skip punctuation and newline

        else:
            i += 1  # Ensure consistent incrementation

    # Adjust ride-along logic
    for j in range(len(blocks) - 1):
        current_block = blocks[j]
        next_block = blocks[j + 1]

        current_block_end = current_block.red_end if hasattr(current_block, 'red_end') else current_block.anchor_point

        if hasattr(next_block, 'anchor_point'):
            distance = next_block.anchor_point - current_block_end
        else:
            continue

        if 3 < distance <= 19:
            current_block.ride_along_eligible = True
            current_block.ride_along_end = next_block.anchor_point
            print(f"Ride-along eligible: Block End={current_block_end}, RideAlongEnd={current_block.ride_along_end}")
        else:
            print(f"Not eligible: Block End={current_block_end}, Next Block Anchor={next_block.anchor_point}")

    print("\nCreated Blocks:")
    for block in blocks:
        print(vars(block))

    return blocks
