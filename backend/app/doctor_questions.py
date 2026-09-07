"""
Doctor-question suggestions. Deliberately templated/deterministic rather
than LLM-generated, per the locked priority (Step 7): safety + a reliable
demo matters more than feature breadth this close to the deadline. An LLM
call here would add a new failure point (latency, model availability,
inconsistent output) for a feature that works reliably as fixed templates.

If time allows after everything else is solid, this can be upgraded to an
LLM-generated version -- but the fallback should remain these templates.
"""

CATEGORY_QUESTIONS = {
    "CBC": [
        "Is this result something I should be concerned about right now?",
        "Should I repeat this test, and if so, when?",
    ],
    "Blood Sugar": [
        "Does this result suggest I need further diabetes screening?",
        "Should I make any changes to my diet based on this result?",
    ],
    "Lipid Profile": [
        "What does this mean for my heart health risk?",
        "Should I consider lifestyle changes or medication?",
    ],
    "Liver Function": [
        "Could this be related to something I'm taking or eating?",
        "Do I need any follow-up tests for my liver?",
    ],
    "Kidney Function": [
        "Does this affect how I should take my current medicines?",
        "Should I be tested again soon to monitor this?",
    ],
    "Thyroid": [
        "Could this explain any symptoms I've been having?",
        "Do I need to start or adjust any thyroid medication?",
    ],
    "Vitamins": [
        "Should I take a supplement for this?",
        "How long until I should retest this level?",
    ],
}

GENERIC_QUESTIONS = [
    "What does this result mean for my overall health?",
    "Is any follow-up test or action needed?",
]


def get_doctor_questions(category: str, abnormal_status: str):
    """
    Returns a list of suggested questions. Slightly different framing when
    the value is abnormal vs. normal vs. unclear, but never invents medical
    claims -- these are neutral, safe questions to bring to a doctor.
    """
    questions = list(CATEGORY_QUESTIONS.get(category, GENERIC_QUESTIONS))

    if abnormal_status in ("abnormal_low", "abnormal_high"):
        questions.insert(0, "This result is outside the reference range — what could be causing that?")
    elif abnormal_status == "range_unclear":
        questions.insert(0, "Can you help me understand where my result falls relative to normal?")

    return questions[:3]  # keep it short and focused
