DEFAULT_QUESTIONS = {
    str(i+1): {
        "text": q,
        "options": [
            "Strongly Agree",
            "Agree",
            "Somewhat Agree",
            "Neutral",
            "Somewhat Disagree",
            "Disagree",
            "Strongly Disagree",
        ],
    }
    for i, q in enumerate([
        # Personality / Work Style
        "I enjoy working in teams.",
        "I prefer solving logical problems over creative tasks.",
        "I get energy from social interactions.",
        "I feel comfortable taking risks.",
        "I prefer structured tasks over open-ended ones.",
        "I stay calm under pressure.",
        "I often take initiative without being asked.",
        "I like following step-by-step instructions.",
        "I am comfortable making quick decisions.",
        "I adapt easily to new situations.",
        # Motivation & Goals
        "I am motivated by competition.",
        "I set clear long-term goals for myself.",
        "I like being recognized for my achievements.",
        "I enjoy learning new skills.",
        "I prefer short-term tasks over long-term projects.",
        "I work best when I have deadlines.",
        "I enjoy mentoring or teaching others.",
        "I am motivated by financial rewards.",
        "I prefer meaningful work over high-paying work.",
        "I push myself to achieve beyond expectations.",
        # Cognitive Preferences
        "I enjoy analyzing data and numbers.",
        "I prefer working with abstract concepts.",
        "I enjoy creative problem-solving.",
        "I like visualizing ideas through diagrams or charts.",
        "I learn better through hands-on experience.",
        "I find it easy to memorize facts.",
        "I prefer trial-and-error learning.",
        "I enjoy reading and writing tasks.",
        "I learn faster when collaborating with others.",
        "I prefer independent learning over group learning."
    ])
}