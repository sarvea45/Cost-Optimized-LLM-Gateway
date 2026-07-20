from app.core.preprocessing import clean_prompt

def test_clean_prompt_strips_whitespace():
    assert clean_prompt("  hello world  ") == "hello world"

def test_clean_prompt_reduces_newlines():
    assert clean_prompt("hello\n\n\n\nworld") == "hello\n\nworld"
    assert clean_prompt("hello\n\nworld") == "hello\n\nworld"
    assert clean_prompt("hello\nworld") == "hello\nworld"
