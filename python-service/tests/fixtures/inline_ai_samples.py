"""
Sample texts and fixtures for testing in-line AI features.

Provides realistic test data for all operations.
"""

# ============================================================================
# PROOFREAD SAMPLES
# ============================================================================

PROOFREAD_SAMPLES = {
    "email_with_typos": {
        "original": """Hey john, I hope your doing well. I wanted to touch base about the project we discused yesterday. Their were some intresting points you raised, and I think we should definately consider them. Let me know if your available for a quick call tommorrow.""",
        "expected_corrections": ["John", "you're", "discussed", "There", "interesting", "definitely", "you're", "tomorrow"]
    },

    "technical_doc": {
        "original": """The API endpoint recieve JSON payloads and returns a responce with the data. Its important to validate the input before processing. The server should handel errors gracefully and return appropiate status codes.""",
        "expected_corrections": ["receives", "response", "It's", "handle", "appropriate"]
    },

    "casual_message": {
        "original": """thanks alot for the help! I really apreciate it. Lets catch up soon, maybe next week? I'll be in the office on wendsday and thursday.""",
        "expected_corrections": ["Thanks", "a lot", "appreciate", "Let's", "Wednesday", "Thursday"]
    },

    "formal_business": {
        "original": """Dear Sir or Madam, I am writing to enquire about the possition advertised on your website. I beleive my experiance in software development makes me an ideal candiate. I would be greatful for the oppertunity to discuss this further.""",
        "expected_corrections": ["position", "believe", "experience", "candidate", "grateful", "opportunity"]
    },

    "already_perfect": {
        "original": """This text is already perfect and has no spelling or grammar errors. It should be returned unchanged.""",
        "expected_corrections": []
    }
}


# ============================================================================
# REWRITE SAMPLES
# ============================================================================

REWRITE_SAMPLES = {
    "formal_to_friendly": {
        "original": """I am writing to formally request your assistance with this matter. I would be grateful if you could provide guidance at your earliest convenience. Please let me know if you require any additional information.""",
        "tone": "friendly",
        "expected_elements": ["Hey", "help", "appreciate", "Thanks"]
    },

    "friendly_to_professional": {
        "original": """Hey! Just wanted to check in and see if you're free to hop on a quick call later? We should totally discuss that bug you mentioned. Let me know!""",
        "tone": "professional",
        "expected_elements": ["schedule", "discuss", "appreciate", "convenient"]
    },

    "verbose_to_concise": {
        "original": """In my personal opinion, I think that perhaps we might want to consider the possibility of implementing this feature at some point in the near future, if it seems like a good idea and if we have the necessary resources available to us.""",
        "style": "concise",
        "expected_max_length": 100
    },

    "concise_to_detailed": {
        "original": """Ship feature next week.""",
        "style": "detailed",
        "expected_min_length": 100
    }
}


# ============================================================================
# SUMMARIZE SAMPLES
# ============================================================================

SUMMARIZE_SAMPLES = {
    "long_article": {
        "original": """Artificial intelligence has made remarkable progress in recent years, transforming industries from healthcare to transportation. Machine learning algorithms can now diagnose diseases with accuracy matching or exceeding human experts, drive cars autonomously in complex urban environments, and even create original artwork that is indistinguishable from human-created pieces.

However, these advances also raise important ethical questions about privacy, bias, and the future of work. AI systems trained on historical data can perpetuate existing biases, leading to unfair outcomes in hiring, lending, and criminal justice. The increasing automation of tasks previously performed by humans raises concerns about job displacement and economic inequality.

Moreover, the use of AI in surveillance and facial recognition technologies has sparked debates about privacy and civil liberties. As AI systems become more powerful and ubiquitous, society must grapple with how to ensure they are developed and deployed responsibly, with appropriate safeguards to protect individual rights and promote the common good.

Researchers and policymakers are working to address these challenges through technical solutions like fairness-aware algorithms, transparency requirements, and governance frameworks. However, much work remains to be done to ensure that AI benefits all of humanity rather than exacerbating existing inequalities.""",
        "expected_length_range": (50, 200)
    },

    "meeting_notes": {
        "original": """Meeting started at 10:00 AM. Attendees: Sarah (PM), John (Engineering), Lisa (Design), Mike (QA).

Sarah presented the Q4 roadmap, highlighting three major initiatives: mobile app redesign, API v2 migration, and analytics dashboard.

Team discussion on mobile app redesign:
- Lisa showed initial mockups, team gave positive feedback
- Concerns raised about iOS 15 compatibility
- Decided to conduct user testing with beta group
- Timeline: Design completion by Oct 15, development by Nov 30

API v2 migration discussion:
- John expressed concerns about breaking changes
- Agreed to maintain v1 support for 6 months
- Mike to create comprehensive test suite
- Documentation to be completed before launch

Action items:
1. Sarah to draft detailed spec for mobile app (due Oct 1)
2. John to prototype API v2 authentication (due Sept 25)
3. Lisa to schedule user testing sessions (due Sept 28)
4. Mike to hire additional QA contractor (due Oct 5)

Next meeting: Friday, September 22 at 2:00 PM.
Meeting adjourned at 11:30 AM.""",
        "expected_length_range": (50, 150)
    },

    "technical_explanation": {
        "original": """The React component lifecycle consists of several phases: mounting, updating, and unmounting. During the mounting phase, the constructor is called first, followed by render(), and then componentDidMount(). The updating phase occurs when props or state change, triggering render() and componentDidUpdate(). Finally, componentWillUnmount() is called before the component is removed from the DOM. Understanding these lifecycle methods is crucial for managing side effects, fetching data, and cleaning up resources in React applications.""",
        "expected_length_range": (40, 100)
    }
}


# ============================================================================
# KEY POINTS SAMPLES
# ============================================================================

KEY_POINTS_SAMPLES = {
    "product_feature": {
        "original": """The new dashboard feature will significantly improve user experience by reducing load times from 5 seconds to under 1 second. This requires refactoring the backend API to use GraphQL instead of REST, which will enable more efficient data fetching. The frontend needs to be updated to use React Query for caching and state management. We estimate 3 weeks for backend development, 2 weeks for frontend work, and 1 week for comprehensive testing. Once launched, we expect this feature to increase user engagement by approximately 25% based on our A/B test results.""",
        "expected_points": 4
    },

    "project_update": {
        "original": """Project status as of September 15: We've completed 75% of the planned features. Authentication module is fully implemented and tested. Payment integration is 90% complete, pending final approval from legal team. Admin dashboard is in progress, currently at 60% completion. Two critical bugs identified in the user profile section, both being addressed by the team. We're on track to meet the October 31 deadline, but we'll need to prioritize ruthlessly in the final weeks.""",
        "expected_points": 5
    }
}


# ============================================================================
# FORMATTING SAMPLES
# ============================================================================

FORMATTING_SAMPLES = {
    "paragraph_to_list": {
        "original": """For the party, we need to buy balloons, streamers, paper plates, cups, napkins, a cake, candles, and party favors. Don't forget to pick up ice for the drinks and extra chairs from storage.""",
        "expected_format": "list"
    },

    "steps_to_numbered_list": {
        "original": """To reset your password, first go to the login page. Then click on 'Forgot Password'. Enter your email address. Check your email for the reset link. Click the link and create a new password. Finally, log in with your new password.""",
        "expected_format": "numbered_list"
    },

    "data_to_table": {
        "original": """In Q1, Revenue was $1.2M with expenses of $800K. Q2 saw revenue of $1.5M and expenses of $900K. Q3 revenue reached $1.8M with expenses of $950K. Q4 revenue was $2.0M and expenses were $1.1M.""",
        "expected_format": "table",
        "expected_columns": ["Quarter", "Revenue", "Expenses"]
    },

    "unstructured_to_headings": {
        "original": """Introduction
This document describes the new feature. We'll cover the requirements, implementation details, and testing strategy.

Requirements
The feature must support authentication, authorization, and audit logging. Performance should not degrade with scale.

Implementation
We'll use JWT tokens for auth, role-based access control for authorization, and a separate audit service for logging.

Testing
Unit tests for all components, integration tests for the full flow, and performance tests under load.""",
        "expected_format": "headings"
    }
}


# ============================================================================
# COMPOSE SAMPLES
# ============================================================================

COMPOSE_SAMPLES = {
    "follow_up_email": {
        "prompt": """Write a follow-up email to John thanking him for yesterday's meeting and confirming we'll send the proposal by Friday.""",
        "expected_elements": ["thank", "meeting", "proposal", "Friday", "regards"]
    },

    "meeting_request": {
        "prompt": """Compose an email requesting a 30-minute meeting next week to discuss the Q4 roadmap. Suggest Tuesday or Wednesday afternoon.""",
        "expected_elements": ["meeting", "30 minutes", "Q4", "Tuesday", "Wednesday"]
    },

    "status_update": {
        "prompt": """Write a brief status update for the team saying the feature is 80% complete, testing will start Monday, and we're on track for the deadline.""",
        "expected_elements": ["80%", "testing", "Monday", "on track"]
    },

    "apology_message": {
        "prompt": """Write an apology message for missing the deadline, explain the technical issues we faced, and commit to delivery by tomorrow.""",
        "expected_elements": ["apologize", "technical", "tomorrow", "commit"]
    },

    "creative_short_story": {
        "prompt": """Write a short story (3-4 paragraphs) about a developer who discovers a mysterious bug that only appears at midnight.""",
        "expected_min_length": 200
    }
}


# ============================================================================
# EDGE CASE SAMPLES
# ============================================================================

EDGE_CASE_SAMPLES = {
    "very_long_text": " ".join(["This is a sentence."] * 1000),  # ~5000 words

    "very_short_text": "Hi",

    "empty_text": "",

    "only_punctuation": "!!! ??? ... --- !!!",

    "unicode_characters": """Café résumé naïve Zürich São Paulo Москва 北京 東京 🎉 🚀 ❤️""",

    "code_snippet": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",

    "markdown_formatted": """# Heading 1
## Heading 2

**Bold text** and *italic text*

- List item 1
- List item 2

```python
print("Hello")
```

[Link](https://example.com)""",

    "mixed_languages": """Hello world. Bonjour le monde. Hola mundo. こんにちは世界. 你好世界.""",

    "html_content": """<div class="container">
    <h1>Title</h1>
    <p>This is a <strong>paragraph</strong> with <em>formatting</em>.</p>
</div>""",

    "email_with_signature": """Hi there,

Thanks for reaching out!

Best regards,
--
John Doe
Senior Developer
Company Name
john@example.com
(555) 123-4567""",

    "bulleted_list_already": """• Item one
• Item two
• Item three
• Item four""",

    "numbered_list_already": """1. First step
2. Second step
3. Third step
4. Fourth step""",

    "table_already": """| Name | Age | City |
|------|-----|------|
| John | 30  | NYC  |
| Jane | 25  | LA   |""",

    "excessive_whitespace": """This    has    too    many    spaces.


And  too   many   newlines.



Should be normalized.""",

    "all_caps": """THIS ENTIRE TEXT IS IN ALL CAPS AND SHOULD PROBABLY BE CONVERTED TO NORMAL CASE.""",

    "all_lowercase": """this entire text is in lowercase and has no punctuation or capitalization whatsoever""",

    "special_characters": """Testing special characters: @#$%^&*()_+-=[]{}|;:'",.<>?/~`""",

    "numbers_and_data": """Revenue: $1,234,567.89
Users: 10,000+
Growth: 25.5%
Date: 2024-09-15
Time: 14:30:00""",

    "multiple_languages_mixed": """The système operates at 高效率 with 100% надежность."""
}


# ============================================================================
# ERROR CASE SAMPLES
# ============================================================================

ERROR_CASE_SAMPLES = {
    "null_text": None,

    "invalid_unicode": "Invalid \udcff unicode",

    "extremely_long": "a" * 100000,  # 100K characters

    "binary_data": b'\x00\x01\x02\x03',

    "json_blob": '{"key": "value", "nested": {"data": [1, 2, 3]}}',

    "xml_data": '<?xml version="1.0"?><root><item>data</item></root>',

    "sql_injection": "'; DROP TABLE users; --",

    "script_injection": '<script>alert("xss")</script>',
}


# ============================================================================
# REALISTIC SCENARIOS
# ============================================================================

REALISTIC_SCENARIOS = {
    "email_reply_casual": {
        "original": """hey sarah! yeah i can totally make it to the meeting tomorrow at 2. should i bring anything? also did you get a chance to look at my proposal? thanks!""",
        "action": "proofread",
        "expected_improvements": ["capitalization", "punctuation", "greeting"]
    },

    "meeting_notes_to_summary": {
        "original": """Discussed Q4 priorities. Team agreed mobile is #1. Sarah to spec by Oct 1. John prototyping auth. Mike hiring QA. Lisa scheduling tests. Blocker: need legal approval for payments. Next meeting Friday 2pm.""",
        "action": "summarize",
        "expected_length_range": (40, 80)
    },

    "technical_doc_to_friendly": {
        "original": """The implementation requires instantiation of the singleton pattern with lazy initialization to ensure thread safety. Utilize the double-checked locking mechanism to minimize synchronization overhead.""",
        "action": "rewrite",
        "params": {"tone": "friendly"},
        "expected_changes": ["simpler vocabulary", "less jargon"]
    },

    "brainstorm_to_list": {
        "original": """Ideas for the hackathon: build a chatbot, create a mobile app, develop a browser extension, make a data visualization tool, try machine learning project, build a game""",
        "action": "make_list",
        "expected_format": "bulleted_list"
    },

    "instructions_to_numbered": {
        "original": """To deploy: run tests, build the project, tag the release, push to GitHub, wait for CI/CD, verify in staging, promote to production, monitor metrics""",
        "action": "make_numbered_list",
        "expected_format": "numbered_list"
    },

    "sales_data_to_table": {
        "original": """January sales were $50K in US, $30K in EU, $20K in Asia. February was $55K US, $35K EU, $25K Asia. March hit $60K US, $40K EU, $30K Asia.""",
        "action": "make_table",
        "expected_columns": 4  # Month + 3 regions
    },

    "compose_thank_you": {
        "prompt": """Write a thank you note to the interviewer Sarah for the great conversation about the Senior Engineer role, mention excitement about the team and technology stack""",
        "action": "compose",
        "expected_elements": ["thank you", "Sarah", "conversation", "Senior Engineer", "excited", "team"]
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_sample(category: str, name: str) -> dict:
    """Get a specific sample from a category"""
    samples = {
        "proofread": PROOFREAD_SAMPLES,
        "rewrite": REWRITE_SAMPLES,
        "summarize": SUMMARIZE_SAMPLES,
        "key_points": KEY_POINTS_SAMPLES,
        "formatting": FORMATTING_SAMPLES,
        "compose": COMPOSE_SAMPLES,
        "edge_cases": EDGE_CASE_SAMPLES,
        "error_cases": ERROR_CASE_SAMPLES,
        "scenarios": REALISTIC_SCENARIOS
    }

    if category not in samples:
        raise ValueError(f"Unknown category: {category}")

    if name not in samples[category]:
        raise ValueError(f"Unknown sample '{name}' in category '{category}'")

    return samples[category][name]


def get_all_samples(category: str) -> dict:
    """Get all samples from a category"""
    samples = {
        "proofread": PROOFREAD_SAMPLES,
        "rewrite": REWRITE_SAMPLES,
        "summarize": SUMMARIZE_SAMPLES,
        "key_points": KEY_POINTS_SAMPLES,
        "formatting": FORMATTING_SAMPLES,
        "compose": COMPOSE_SAMPLES,
        "edge_cases": EDGE_CASE_SAMPLES,
        "error_cases": ERROR_CASE_SAMPLES,
        "scenarios": REALISTIC_SCENARIOS
    }

    if category not in samples:
        raise ValueError(f"Unknown category: {category}")

    return samples[category]


def list_categories() -> list:
    """List all available sample categories"""
    return [
        "proofread",
        "rewrite",
        "summarize",
        "key_points",
        "formatting",
        "compose",
        "edge_cases",
        "error_cases",
        "scenarios"
    ]


def list_samples(category: str) -> list:
    """List all sample names in a category"""
    return list(get_all_samples(category).keys())


# Example usage:
if __name__ == "__main__":
    print("Available categories:", list_categories())
    print("\nProofread samples:", list_samples("proofread"))
    print("\nSample:", get_sample("proofread", "email_with_typos"))
