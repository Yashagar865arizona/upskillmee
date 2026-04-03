
import random

def generate_story(prompt):
    # Sample story continuations
    continuations = [
        " suddenly discovered a hidden world full of wonders.",
        " met an unexpected friend who changed everything.",
        " embarked on a journey that would change their life forever.",
        " found a mysterious object that glowed with strange light.",
        " realized that their dreams were more than just dreams."
    ]
    return prompt + random.choice(continuations)

def main():
    print("Welcome to AI Story Weaver!")
    while True:
        user_input = input("\nEnter your story starter (or type 'quit' to exit): ")
        if user_input.lower() == 'quit':
            print("Thanks for using AI Story Weaver! Goodbye!")
            break
        story = generate_story(user_input)
        print("\nHere's your story:")
        print(story)

if __name__ == "__main__":
    main()
