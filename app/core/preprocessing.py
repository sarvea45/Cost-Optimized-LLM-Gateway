import re

def clean_prompt(prompt: str) -> str:
    """
    Strips leading/trailing whitespace and reduces multiple consecutive 
    newline characters (\n\n\n+) to a maximum of two.
    """
    # Strip leading/trailing whitespace
    prompt = prompt.strip()
    
    # Replace 3 or more newlines with exactly 2 newlines
    prompt = re.sub(r'\n{3,}', '\n\n', prompt)
    
    return prompt
