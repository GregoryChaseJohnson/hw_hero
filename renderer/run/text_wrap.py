import textwrap

def wrap_exact_width(text, width=80):
    """
    Wrap text to a fixed width, returning a list of lines. Each line will be
    exactly `width` characters long. If the last line is shorter, it will be
    padded with spaces. If the line is longer, it's split into multiple lines.
    """
    lines = []
    # textwrap.wrap will give lines up to `width` chars, but might be shorter
    wrapped = textwrap.wrap(text, width=width)
    for w_line in wrapped:
        # If w_line shorter than width, pad with spaces
        if len(w_line) < width:
            w_line = w_line.ljust(width)
        lines.append(w_line)
    # Handle the case if text is empty
    if not wrapped and text.strip() == "":
        # Create one blank line of width
        lines.append(" " * width)
    return lines

def format_annotated_final_pairs(annotated_lines, final_sentences, width=80):
    """
    For each annotated_line and final_sentence pair:
    - Annotated line: wrap at `width` chars. No padding needed if shorter than width.
    - Final sentence: wrap at `width` chars, pad if shorter, continue if longer.

    Each annotated line corresponds to a final sentence line directly below it.
    If one has more lines than the other, the shorter one gets padded lines of spaces.
    """
    formatted_pairs = []

    for annotated, final in zip(annotated_lines, final_sentences):
        # Wrap the annotated line at width chars (lines may be shorter but never longer)
        annotated_wrapped = textwrap.wrap(annotated, width=width) or [""]
        # If any annotated line shorter than width, leave as is (no padding required)
        # Just ensure empty line if it's empty:
        annotated_wrapped = [line for line in annotated_wrapped]

        # Wrap final line to exact width lines
        final_wrapped = wrap_exact_width(final, width=width)

        # Equalize the number of lines
        max_lines = max(len(annotated_wrapped), len(final_wrapped))
        # If annotated has fewer lines, pad with blank lines
        if len(annotated_wrapped) < max_lines:
            annotated_wrapped += [""] * (max_lines - len(annotated_wrapped))
        # If final has fewer lines (unlikely due to exact width wrapping), pad as well
        if len(final_wrapped) < max_lines:
            final_wrapped += [(" " * width)] * (max_lines - len(final_wrapped))

        # Now print line by line
        for a_line, f_line in zip(annotated_wrapped, final_wrapped):
            # a_line may be shorter than width. If shorter, leave it as is (no padding required)
            # If you do want them exactly width:
            # a_line = a_line.ljust(width) if len(a_line) < width else a_line
            # But user said top line can just remain shorter, so no padding needed for a_line
            formatted_pairs.append(f"{a_line}\n{f_line}")
        formatted_pairs.append("")  # blank line between pairs

    return "\n".join(formatted_pairs)

# Example Usage
if __name__ == "__main__":
    annotated_lines = [
        "This is an annotated line for sentence one.",
        "This annotated line is for sentence two, and it is much longer to test how wrapping occurs when we have a very long line indeed that should wrap around.",
        "Short annotated line."
    ]
    final_sentences = [
        "This is the final sentence one.",
        "This is the final sentence two, which should also wrap around if it is longer than eighty characters in total length.",
        "Short final sentence."
    ]

    formatted_text = format_annotated_final_pairs(annotated_lines, final_sentences, width=80)
    print(formatted_text)
