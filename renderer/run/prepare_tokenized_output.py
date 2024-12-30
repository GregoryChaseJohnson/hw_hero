import json
import pickle

def compute_container_length(annotated_line, final_line):
    """
    Determine how wide the sentence container should be by finding
    the maximum index in both annotated_line and final_line, then
    adding 1 (assuming 0-based indexing, so +1 is total token count).
    """
    max_annotated_idx = max((t["index"] for t in annotated_line), default=0)
    max_final_idx = max((t["index"] for t in final_line), default=0)

    return max(max_annotated_idx, max_final_idx) + 1

def detect_blocks_by_type(tokens, valid_types=None):
    """
    Unchanged from your existing code. 
    Returns a list of blocks, each with "start", "end", etc.
    """
    if valid_types is None:
        valid_types = {"replace"}

    blocks = []
    block_start = None
    not_type_count = 0
    n = len(tokens)
    i = 0

    while i < n:
        ttype = tokens[i]["type"]
        if ttype in valid_types:
            not_type_count = 0
            if block_start is None:
                block_start = i
        else:
            not_type_count += 1
            if block_start is not None and not_type_count >= 2:
                # Close this block
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

    # If a block is still open by the end
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
    Unchanged from your existing code.
    """
    min_len = min(len(annotated_blocks), len(final_blocks))
    for idx in range(min_len):
        annotated_blocks[idx]["block_index"] = idx
        final_blocks[idx]["block_index"] = idx

def print_sentence_debug(
    sentence_idx,
    final_sentence,
    ann_blocks,
    fin_blocks,
    annotated_line
):
    """
    Unchanged from your existing code.
    Prints debug for final/annotated tokens, blocks, etc.
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
    for b in ann_blocks:
        c_text = "".join(t["char"] for t in b["tokens"])
        corrected_map[b["block_index"]] = {
            "start": b["start"],
            "end": b["end"],
            "text": c_text
        }

    replaced_map = {}
    for b in fin_blocks:
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

        print(f"  Block {bidx}:")
        print(f"    corrected='{corrected_text}' (start={c_start}, end={c_end})")
        print(f"    replaced ='{replaced_text}' (start={r_start}, end={r_end})")

def extend_final_tokens(final_tokens, up_to_index):
    """
    Pad the final tokens up to `up_to_index` if needed,
    using placeholders (type 'equal', char ' ').
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
    annotated_blocks_all,
    final_blocks_all,
    final_sentences,
    annotated_lines
):
    """
    Return final JSON structure with container_length.
    """
    sentences_data = []

    for sentence_index, (final_sentence, ann_blocks, fin_blocks) in enumerate(
        zip(final_sentences, annotated_blocks_all, final_blocks_all)
    ):
        ann_line = annotated_lines[sentence_index]

        # 1) Figure out the largest annotated block "end" from ann_blocks
        #    because detect_blocks_by_type only sets "start", "end" for each block in annotated_line
        if ann_blocks:
            max_anno_end = max(b["end"] for b in ann_blocks)
            # 2) Extend final tokens up to that index
            final_sentence = extend_final_tokens(final_sentence, max_anno_end)

        # 3) Compute container length
        container_len = compute_container_length(ann_line, final_sentence)

        # 4) Build blocks
        blocks = []
        for ann_block, fin_block in zip(ann_blocks, fin_blocks):
            blocks.append({
                "block_index": ann_block["block_index"],
                "final_start": fin_block["start"],
                "final_end": fin_block["end"],
                "replaced_text": "".join(tok["char"] for tok in fin_block["tokens"]),
                "annotated_start": ann_block["start"],
                "annotated_end": ann_block["end"],  # naming for final JSON
                "corrected_text": "".join(tok["char"] for tok in ann_block["tokens"])
            })

        # 5) Final sentence data
        sentences_data.append({
            "sentence_index": sentence_index,
            "final_sentence_tokens": final_sentence,
            "blocks": blocks,
            "container_length": container_len
        })

    return {"sentences": sentences_data}

if __name__ == "__main__":
    # 1) Load final_output.pkl
    with open("final_output.pkl", "rb") as f:
        data = pickle.load(f)
        annotated_lines = data["annotated_lines"]
        final_sentences = data["final_sentences"]

    # Assign indexes to final_sentences
    for sentence in final_sentences:
        for i, token in enumerate(sentence):
            token["index"] = i

    # Assign indexes to annotated_lines
    for ann_line in annotated_lines:
        for i, token in enumerate(ann_line):
            token["index"] = i

    # 2) Detect blocks
    annotated_blocks_all = []
    for ann_line in annotated_lines:
        ann_blocks = detect_blocks_by_type(ann_line, valid_types={"corrected"})
        annotated_blocks_all.append(ann_blocks)

    final_blocks_all = []
    for fin_line in final_sentences:
        fin_blocks = detect_blocks_by_type(fin_line, valid_types={"replace"})
        final_blocks_all.append(fin_blocks)

    # 3) Assign block indices
    for ann_blocks, fin_blocks in zip(annotated_blocks_all, final_blocks_all):
        assign_block_indices(ann_blocks, fin_blocks)

    # 4) Print debug info
    for idx, (ann_blocks, fin_blocks, final_line, annotated_line) in enumerate(
        zip(annotated_blocks_all, final_blocks_all, final_sentences, annotated_lines)
    ):
        print_sentence_debug(idx, final_line, ann_blocks, fin_blocks, annotated_line)

    # 5) Prepare final JSON
    output_data = prepare_json_output(
        annotated_blocks_all,
        final_blocks_all,
        final_sentences,
        annotated_lines
    )

    with open("output.json", "w") as f:
        json.dump(output_data, f, indent=4)

    print("\n[INFO] Wrote output.json successfully.")
