import os
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """
You will be given a word. Reverse the order of its letters and output ONLY the reversed word, with no other text.

Study these examples of how to reverse a word by first splitting it into individual letters:

Example 1:
Input: apple
Split: a - p - p - l - e
Reversed: e - l - p - p - a
Final: elppa

Example 2:
Input: python
Split: p - y - t - h - o - n
Reversed: n - o - h - t - y - p
Final: nohtyp

Example 3:
Input: beautifulsoup
Split: b - e - a - u - t - i - f - u - l - s - o - u - p
Reversed: p - u - o - s - l - u - f - i - t - u - a - e - b
Final: puoslufituaeb

Now apply the same letter-splitting process in your head for the given word, but for your actual response, output ONLY the final reversed word on its own — do not show the split or reasoning steps.
"""

USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)