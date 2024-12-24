# prepare_tokenized_output.py

import json
import pickle

def detect_blocks_by_type(tokens, valid_types=None):
    """
    Detect blocks in a line of tokens using the two-consecutive-nonvalid logic.
    Returns a list of blocks, each:
      {
        "start": int,
        "end": int,
        "tokens": list of tokens in [start..end],
        "block_index": None (assigned later)
      }
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
    Pair up annotated/final blocks by index, setting block_index on each.
    We assume both lists are in the same order logically.
    """
    min_len = min(len(annotated_blocks), len(final_blocks))
    for idx in range(min_len):
        annotated_blocks[idx]["block_index"] = idx
        final_blocks[idx]["block_index"] = idx

def print_sentence_debug(
    sentence_idx,
    final_sentence,
    ann_blocks,
    fin_blocks
):
    """
    Print debug info for this sentence:
      - Final Sentence tokens
      - Combined block info: block_index, corrected text, replaced text, etc.
    """
    print(f"\n=== Sentence {sentence_idx + 1} ===")

    # 1) Print final sentence tokens for validation
    print("Final Sentence Tokens:")
    for i, tok in enumerate(final_sentence):
        print(f"  {i}: char='{tok['char']}', type='{tok['type']}'")

    # 2) Print block info in a combined way
    #    We'll map block_index -> corrected text (from ann_blocks)
    #                         -> replaced text (from fin_blocks)
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

    # Gather all block indices from both sides
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

def prepare_json_output(
    annotated_blocks_all,
    final_blocks_all,
    final_sentences
):
    """
    Return final JSON structure with enhanced info:
      {
        "sentences": [
           {
             "sentence_index": int,
             "final_sentence_tokens": [...],
             "blocks": [
                 {
                     "block_index": int,
                     "final_start": int,
                     "final_end": int,
                     "replaced_text": str,
                     "annotated_start": int,
                     "annotated_end": int,
                     "corrected_text": str
                 },
                 ...
             ]
           },
           ...
        ]
      }
    """
    sentences_data = []

    for sentence_index, (final_sentence, ann_blocks, fin_blocks) in enumerate(zip(final_sentences, annotated_blocks_all, final_blocks_all)):
        # Construct block data for this sentence
        blocks = []
        for ann_block, fin_block in zip(ann_blocks, fin_blocks):
            blocks.append({
                "block_index": ann_block["block_index"],  # Same as fin_block["block_index"]
                "final_start": fin_block["start"],
                "final_end": fin_block["end"],
                "replaced_text": "".join(tok["char"] for tok in fin_block["tokens"]),
                "annotated_start": ann_block["start"],
                "annotated_end": ann_block["end"],
                "corrected_text": "".join(tok["char"] for tok in ann_block["tokens"])
            })

        # Add the sentence data
        sentences_data.append({
            "sentence_index": sentence_index,
            "final_sentence_tokens": final_sentence,
            "blocks": blocks
        })

    return { "sentences": sentences_data }


if __name__ == "__main__":
    # 1) Load final_output.pkl
    with open("final_output.pkl", "rb") as f:
        data = pickle.load(f)
        annotated_lines = data["annotated_lines"]
        final_sentences = data["final_sentences"]

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

    # 4) Print debug info (without flattening logic)
    # We only show final sentence tokens, and combined block info
    for idx, (ann_blocks, fin_blocks, final_line) in enumerate(zip(
        annotated_blocks_all, final_blocks_all, final_sentences
    )):
        print_sentence_debug(idx, final_line, ann_blocks, fin_blocks)

    # 5) Prepare final JSON
    output_data = prepare_json_output(annotated_blocks_all, final_blocks_all, final_sentences)
    with open("output.json", "w") as f:
        json.dump(output_data, f, indent=4)
    print("\n[INFO] Wrote output.json successfully.")
