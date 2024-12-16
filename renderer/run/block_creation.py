class ReplacementBlock:
    def __init__(self, red_start, red_end, red_text, replacement_text):
        self.type = 'replace'
        self.red_start = red_start
        self.red_end = red_end
        self.red_text = red_text
        self.replacement_text = replacement_text
        self.ride_along_end = None
        self.ride_along_eligible = False
        self.adjacent_to_next = False  # Will be set later if needed

class DeleteBlock:
    def __init__(self, pink_start):
        self.type = 'pink'
        self.pink_start = pink_start

class SentenceEndBlock:
    def __init__(self, red_start):
        self.type = 'sentence_end'
        self.red_start = red_start

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
            red_start = i
            red_text = ""
            replacement_text = ""
            red_end = None

            print(f"Starting replacement block at index {red_start}")

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
            blocks.append(ReplacementBlock(red_start, red_end, red_text, replacement_text))

        # Handle pink blocks
        elif tokens[i]['color'] == 'pink':
            pink_start = i
            print(f"Starting pink block at index {pink_start}")

            # Skip over contiguous pink tokens
            while i < len(tokens) and tokens[i]['color'] == 'pink':
                i += 1

            blocks.append(DeleteBlock(pink_start))

        # Handle sentence-end blocks
        elif is_sentence_end(tokens, i):
            red_start = i
            print(f"Creating sentence end block at index {red_start}")
            blocks.append(SentenceEndBlock(red_start))
            i += 2  # Skip punctuation and newline

        else:
            i += 1  # Ensure consistent incrementation

    # Adjust ride-along logic
    for j in range(len(blocks) - 1):
        current_block = blocks[j]
        next_block = blocks[j + 1]

        current_block_end = current_block.red_end if hasattr(current_block, 'red_end') else current_block.pink_start

        if hasattr(next_block, 'red_start'):
            distance = next_block.red_start - current_block_end
        else:
            continue

        if 3 < distance <= 19:
            current_block.ride_along_eligible = True
            current_block.ride_along_end = next_block.red_start
            print(f"Ride-along eligible: Block End={current_block_end}, RideAlongEnd={current_block.ride_along_end}")
        else:
            print(f"Not eligible: Block End={current_block_end}, Next Block Anchor={next_block.red_start}")

    print("\nCreated Blocks with Adjacency:")
    for block in blocks:
        print(vars(block))

    return blocks
