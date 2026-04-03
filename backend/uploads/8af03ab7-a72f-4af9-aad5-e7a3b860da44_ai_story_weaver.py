import random

def ai_story_weaver(starting_sentence: str) -> str:
    """Generate a short story continuation (3–5 sentences) from a starting sentence."""
    continuations: list[str] = [
        "The sky turned shades of gold as the sun dipped below the horizon.",
        "A mysterious sound echoed from the forest nearby.",
        "Suddenly, a small bird landed gently on the windowsill.",
        "With every step, the path seemed to lead into the unknown.",
        "The world felt alive, buzzing with secrets waiting to be discovered.",
        "Then, without warning, everything changed in an instant.",
        "In the distance, laughter carried softly through the breeze.",
        "The gentle rustling of leaves hinted at a hidden presence.",
        "Each moment seemed to whisper a story of its own.",
        "And so, the adventure was only just beginning."
    ]

    # Randomly select 3–5 unique continuations
    story_sentences = random.sample(continuations, random.randint(3, 5))

    # Construct the story with smoother flow
    story = " ".join([starting_sentence] + story_sentences)
    return story


if __name__ == "__main__":
    print(ai_story_weaver("Once upon a time in a quiet village,"))
