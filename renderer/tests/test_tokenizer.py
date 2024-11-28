import sys
sys.path.append('/home/keithuncouth/red_pen_app/renderer')  # Add renderer dir to path

from tokenizer import TextTokenizer  # Import tokenizer prototype
from script_runner import generate_report_from_script  # Import script runner

def test_tokenizer():
    # Run sentence_parse.py via script_runner
    raw_output = generate_report_from_script()
    
    # Ensure the script produced some output
    if not raw_output.strip():
        print("Error: No output from sentence_parse.py")
        return
    
    # Tokenize the output
    tokenizer = TextTokenizer(raw_output)
    tokens = tokenizer.parse_text()
    
    # Print tokens for verification
    print("Tokens:")
    for token in tokens:
        print(token)

if __name__ == "__main__":
    test_tokenizer()
