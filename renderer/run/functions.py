def insert_spaces_for_overhang(final_sentence, red_end, overhang):
    """
    Insert spaces into the final sentence based on overhang, starting at red_end + 1.
    """
    if overhang <= 0:
        return final_sentence  # No overhang, no modification

    spaces_to_insert = overhang  
    insertion_point = red_end + 1

    # Ensure the sentence has enough room for insertion
    spaces = [{'char': ' ', 'color': 'normal'}] * spaces_to_insert
    final_sentence = final_sentence[:insertion_point] + spaces + final_sentence[insertion_point:]

    print(f"[DEBUG] Inserting {spaces_to_insert} spaces at position {insertion_point}")
    return final_sentence


def process_blocks(annotated_line, final_sentence, blocks):
    """
    Process blocks in a sentence:
    - Measure overhang
    - Insert spaces dynamically in the bottom line
    - Build the top line (replacement text) separately at the end
    """
    updated_final_sentence = final_sentence[:]
    updated_annotated_line = [''] * len(annotated_line)  # Dynamic top line

    for i, block in enumerate(blocks):
    

        # Measure overhang
        overhang = block.get_overhang()
        if overhang > 0:
            updated_final_sentence = insert_spaces_for_overhang(updated_final_sentence, block.red_end, overhang)

    # Once spaces are inserted, place replacement text on the annotated line
    for block in blocks:
        replacement_text = block.replacement_text
        red_start = block.red_start
        for i, token in enumerate(replacement_text):
            updated_annotated_line[red_start + i] = token

    return updated_annotated_line, updated_final_sentence
