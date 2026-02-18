"""
Simple quiz answering using LLM.
"""

import os
from anthropic import Anthropic


def answer_question(question: str, choices: dict[str, str]) -> str:
    """
    Answer a multiple choice question using Claude.
    
    Args:
        question: The question text
        choices: Dict mapping choice letters to choice text (e.g. {"A": "...", "B": "..."})
    
    Returns:
        The letter of the chosen answer (e.g. "A", "B", "C", "D")
    """
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    choices_text = "\n".join([f"{k}. {v}" for k, v in choices.items()])
    
    prompt = f"""Answer this multiple choice question. Reply with ONLY the letter (A, B, C, or D).

Question: {question}

Choices:
{choices_text}

Reply with only the letter of the correct answer."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        messages=[
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": "The correct answer is:"}
        ]
    )
    
    answer = message.content[0].text.strip()
    
    for char in answer:
        if char.upper() in choices:
            return char.upper()
    
    return list(choices.keys())[0]
