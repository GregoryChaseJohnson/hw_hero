import json
import pickle
import re

def replace_double_quotes_in_tokens(tokens):
    """
    Replace double quotes used as apostrophes with single quotes in a list of tokens.
    Tokens are modified in place.
    """
    for token in tokens:
        token["char"] = re.sub(r'\b(\w+)"(\w+)\b', r"\1'\2", token["char"])
    return tokens


def compute_container_length(annotated_line, final_line):
    """
    Determine how wide the sentence container should be by finding
    the maximum index in both annotated_line and final_line,
    then adding 1 (assuming 0-based indexing, so +1 is total token count).
    """
    max_annotated_idx = max((t["index"] for t in annotated_line), default=0)
    max_final_idx = max((t["index"] for t in final_line), default=0)
    return max(max_annotated_idx, max_final_idx) + 1

def detect_blocks_by_type(tokens, valid_types=None):
    """
    General-purpose function to detect contiguous blocks of `valid_types`.
    Returns a list of dicts, each with "start", "end", "tokens", "block_index".
    """
    if valid_types is None:
        valid_types = {"replace"}  # default if nothing passed

    blocks = []
    block_start = None
    not_type_count = 0
    n = len(tokens)
    i = 0

    while i < n:
        ttype = tokens[i]["type"]
        # If token type is in our valid set, we may be in a block
        if ttype in valid_types:
            not_type_count = 0
            if block_start is None:
                block_start = i
        else:
            # We hit a token that isn't in our valid types, so possibly close a block
            not_type_count += 1
            if block_start is not None and not_type_count >= 2:
                # End the block two tokens before (contiguous region ended)
                end_idx = i - 2
                if end_idx >= block_start:
                    blocks.append({
                        "start": block_start,
                        "end": end_idx,
                        "tokens": tokens[block_start:end_idx + 1],
                        "block_index": None
                    })
                block_start = None
                not_type_count = 0
        i += 1

    # If a block was still open by the end
    if block_start is not None:
        blocks.append({
            "start": block_start,
            "end": n - 1,
            "tokens": tokens[block_start:],
            "block_index": None
        })

    return blocks

def assign_block_indices(annotated_blocks, final_blocks):
    """
    Assign indices only to overlapping blocks between annotated_blocks and final_blocks.
    This applies to replace/corrected pairs.
    """
    min_len = min(len(annotated_blocks), len(final_blocks))
    for idx in range(min_len):
        annotated_blocks[idx]["block_index"] = idx
        final_blocks[idx]["block_index"] = idx

def detect_replacement_blocks(annotated_tokens, final_tokens):
    """
    Detect matched `corrected` blocks in annotated_tokens
    and matched `replace` blocks in final_tokens.
    Then assign block indices.
    Returns a tuple (annotated_blocks, final_blocks).
    """
    ann_blocks = detect_blocks_by_type(annotated_tokens, valid_types={"corrected"})
    fin_blocks = detect_blocks_by_type(final_tokens, valid_types={"replace"})
    assign_block_indices(ann_blocks, fin_blocks)
    return ann_blocks, fin_blocks

def detect_insert_blocks(final_tokens):
    """
    Detect contiguous `insert` tokens in the final line.
    Assign an insert_block_index for reference.
    """
    blocks = detect_blocks_by_type(final_tokens, valid_types={"insert"})
    # Assign unique block indices
    for idx, blk in enumerate(blocks):
        blk["block_index"] = idx
    return blocks

def detect_delete_blocks(final_tokens):
    """
    Detect contiguous `delete` tokens in the final line.
    Assign a delete_block_index for reference.
    """
    blocks = detect_blocks_by_type(final_tokens, valid_types={"delete"})
    # Assign unique block indices
    for idx, blk in enumerate(blocks):
        blk["block_index"] = idx
    return blocks

def print_sentence_debug(sentence_idx, final_sentence,
                         replacement_ann_blocks, replacement_fin_blocks,
                         annotated_line):
    """
    Example debug printing for replace/corrected blocks, unchanged logic.
    If you want to debug insert/delete, you can do so similarly.
    """
    print(f"\n=== Sentence {sentence_idx + 1} ===")

    # Print final sentence tokens
    print("Final Sentence Tokens:")
    for i, tok in enumerate(final_sentence):
        print(f"  {i}: char='{tok['char']}', type='{tok['type']}'")

    print(f"\nAnnotated Tokens:")
    for i, tok in enumerate(annotated_line):
        print(f"  {i}: char='{tok['char']}', type='{tok['type']}'")

    corrected_map = {}
    for b in replacement_ann_blocks:
        c_text = "".join(t["char"] for t in b["tokens"])
        corrected_map[b["block_index"]] = {
            "start": b["start"],
            "end": b["end"],
            "text": c_text
        }

    replaced_map = {}
    for b in replacement_fin_blocks:
        r_text = "".join(t["char"] for t in b["tokens"])
        replaced_map[b["block_index"]] = {
            "start": b["start"],
            "end": b["end"],
            "text": r_text
        }

    # Gather all block indices
    all_block_ids = sorted(set(corrected_map.keys()) | set(replaced_map.keys()))
    print("Blocks:")
    for bidx in all_block_ids:
        c_info = corrected_map.get(bidx, {})
        r_info = replaced_map.get(bidx, {})
        corrected_text = c_info.get("text", "")
        replaced_text = r_info.get("text", "")
        c_start, c_end = c_info.get("start"), c_info.get("end")
        r_start, r_end = r_info.get("start"), r_info.get("end")

        print(f"  replacement_block {bidx}:")
        print(f"    corrected='{corrected_text}' (start={c_start}, end={c_end})")
        print(f"    replaced ='{replaced_text}' (start={r_start}, end={r_end})")

        # Print insert blocks
        print("\nInsert Blocks:")
        for blk in detect_insert_blocks(final_sentence):
            print(f"  insert_block_index={blk['block_index']}, "
                f"start={blk['start']}, end={blk['end']}, "
                f"text='{''.join(tok['char'] for tok in blk['tokens'])}'")

        # Print delete blocks
        print("\nDelete Blocks:")
        for blk in detect_delete_blocks(final_sentence):
            print(f"  delete_block_index={blk['block_index']}, "
                f"start={blk['start']}, end={blk['end']}, "
                f"text='{''.join(tok['char'] for tok in blk['tokens'])}'")


def extend_final_tokens(final_tokens, up_to_index):
    """
    Pad the final tokens up to `up_to_index` if needed,
    using placeholders (type 'equal', char=' ').
    """
    if not final_tokens:
        return final_tokens

    last_idx = final_tokens[-1]["index"]
    if up_to_index > last_idx:
        for idx in range(last_idx + 1, up_to_index + 1):
            final_tokens.append({
                "index": idx,
                "char": " ",
                "type": "equal"
            })
    return final_tokens

def prepare_json_output(
    replacement_ann_blocks_all,
    replacement_fin_blocks_all,
    insert_blocks_all,
    delete_blocks_all,
    final_sentences,
    annotated_lines
):
    """
    Return final JSON structure with container_length.
    Separate block categories:
      1) replacement_blocks (for replace/corrected)
      2) insert_blocks
      3) delete_blocks
    """
    sentences_data = []

    for sentence_index in range(len(final_sentences)):
        final_sentence = final_sentences[sentence_index]
        ann_line = annotated_lines[sentence_index]

        # Replacement blocks for this sentence
        ann_blocks = replacement_ann_blocks_all[sentence_index]
        fin_blocks = replacement_fin_blocks_all[sentence_index]

        # Insert blocks
        ins_blocks = insert_blocks_all[sentence_index]
        # Delete blocks
        del_blocks = delete_blocks_all[sentence_index]

        # Extend final tokens if needed, based on annotated blocks
        if ann_blocks:
            max_anno_end = max(b["end"] for b in ann_blocks)
            final_sentence = extend_final_tokens(final_sentence, max_anno_end)

        # Compute container length
        container_len = compute_container_length(ann_line, final_sentence)

        # Build replacement_blocks
        replacement_blocks = []
        for ann_block, fin_block in zip(ann_blocks, fin_blocks):
            replaced_text = "".join(tok["char"] for tok in fin_block["tokens"])
            corrected_text = "".join(tok["char"] for tok in ann_block["tokens"])
            
            replacement_blocks.append({
                "block_index": ann_block["block_index"],
                "final_start": fin_block["start"],
                "final_end":   fin_block["end"],
                "replaced_text": replaced_text,
                "annotated_start": ann_block["start"],
                "annotated_end":   ann_block["end"],
                "corrected_text":  corrected_text
            })

        # Build insert_blocks
        insert_blocks = []
        for blk in ins_blocks:
            text = "".join(tok["char"] for tok in blk["tokens"])
            insert_blocks.append({
                "insert_block_index": blk["block_index"],
                "final_start": blk["start"],
                "final_end":   blk["end"],
                "insert_text": text
            })

        # Build delete_blocks
        delete_blocks = []
        for blk in del_blocks:
            text = "".join(tok["char"] for tok in blk["tokens"])
            delete_blocks.append({
                "delete_block_index": blk["block_index"],
                "final_start": blk["start"],
                "final_end":   blk["end"],
                "delete_text": text
            })

        # Final sentence data
        sentences_data.append({
            "sentence_index": sentence_index,
            "final_sentence_tokens": final_sentence,
            "replacement_blocks": replacement_blocks,
            "insert_blocks": insert_blocks,
            "delete_blocks": delete_blocks,
            "container_length": container_len
        })

    return {"sentences": sentences_data}

if __name__ == "__main__":
    # Load final_output.pkl
    with open("final_output.pkl", "rb") as f:
        data = pickle.load(f)
        annotated_lines = data["annotated_lines"]
        final_sentences = data["final_sentences"]

    # Apply the double quote replacement to all tokens in annotated lines and final sentences
    annotated_lines = [replace_double_quotes_in_tokens(line) for line in annotated_lines]
    final_sentences = [replace_double_quotes_in_tokens(sentence) for sentence in final_sentences]

    # Assign indexes to final_sentences
    for sentence in final_sentences:
        for i, token in enumerate(sentence):
            token["index"] = i

    # Assign indexes to annotated_lines
    for ann_line in annotated_lines:
        for i, token in enumerate(ann_line):
            token["index"] = i

    # Detect replacement blocks for each sentence
    replacement_ann_blocks_all = []
    replacement_fin_blocks_all = []
    for ann_line, fin_line in zip(annotated_lines, final_sentences):
        ann_blocks, fin_blocks = detect_replacement_blocks(ann_line, fin_line)
        replacement_ann_blocks_all.append(ann_blocks)
        replacement_fin_blocks_all.append(fin_blocks)

    # Detect insert + delete blocks for each final line
    insert_blocks_all = []
    delete_blocks_all = []
    for fin_line in final_sentences:
        ins_blks = detect_insert_blocks(fin_line)
        del_blks = detect_delete_blocks(fin_line)
        insert_blocks_all.append(ins_blks)
        delete_blocks_all.append(del_blks)

    # Debug printing for replacement blocks only
    for idx, (ann_blocks, fin_blocks, final_line, annotated_line) in enumerate(
        zip(replacement_ann_blocks_all, replacement_fin_blocks_all,
            final_sentences, annotated_lines)
    ):
        print_sentence_debug(idx, final_line, ann_blocks, fin_blocks, annotated_line)

    # Prepare final JSON with separate block categories
    output_data = prepare_json_output(
        replacement_ann_blocks_all,
        replacement_fin_blocks_all,
        insert_blocks_all,
        delete_blocks_all,
        final_sentences,
        annotated_lines
    )

    # Write to output
    with open("output.json", "w") as f:
        json.dump(output_data, f, indent=4)

    print("\n[INFO] Wrote output.json successfully.")