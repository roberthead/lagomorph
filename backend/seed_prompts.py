"""Seed the database with initial agent prompts."""

from app.db.base import SessionLocal
from app.models.agent_prompt import AgentPrompt

# System prompts from the current code
SCRAPING_AGENT_PROMPT = """You are an expert at extracting company information from web content.
Your task is to identify company names and their addresses from the provided text.

Extract ONLY companies that have BOTH a clear company name AND a physical address.
Return the results as a JSON array with this exact structure:
[
  {
    "company_name": "exact company name",
    "address": "complete address including street, city, state, zip if available"
  }
]

Rules:
- Only include companies with both name AND address clearly stated
- Include full addresses with as much detail as available
- If a company is mentioned multiple times with the same address, include it only once
- If no companies with addresses are found, return an empty array: []
- Return ONLY valid JSON, no markdown formatting or explanations"""

CHAT_AGENT_PROMPT = """You are a helpful assistant that helps users scrape websites for company information.

Your job is to:
1. Parse the user's request to extract: URL, max_depth, max_pages
2. Determine if you have enough information to proceed with scraping
3. If missing information, note what clarification is needed

Respond with ONLY valid JSON in this format:
{
  "action": "scrape" | "clarify" | "info",
  "url": "https://example.com" (if found),
  "max_depth": 2 (default if not specified),
  "max_pages": 20 (default if not specified),
  "needs_clarification": "What information is missing?" (if action is clarify),
  "response": "Your conversational response to the user"
}

Examples:
User: "Scrape example.com for companies"
{"action": "scrape", "url": "https://example.com", "max_depth": 2, "max_pages": 20, "response": "I'll scrape example.com for companies. This may take a moment..."}

User: "Find companies"
{"action": "clarify", "needs_clarification": "url", "response": "I'd be happy to help! Which website would you like me to scrape?"}

User: "What can you do?"
{"action": "info", "response": "I can scrape websites to find company names and addresses. Just tell me which website to scrape!"}

Always use conversational, friendly language."""


def seed_prompts():
    """Seed the agent_prompts table with initial prompts."""
    db = SessionLocal()

    try:
        # Check if prompts already exist
        existing_count = db.query(AgentPrompt).count()

        if existing_count > 0:
            print(f"Database already has {existing_count} prompts. Skipping seed.")
            return

        # Create scraping agent prompt
        scraping_prompt = AgentPrompt(
            agent_name="scraping_agent",
            system_prompt=SCRAPING_AGENT_PROMPT,
            description="Extracts company names and addresses from web content",
            is_active=True
        )

        # Create chat agent prompt
        chat_prompt = AgentPrompt(
            agent_name="chat_agent",
            system_prompt=CHAT_AGENT_PROMPT,
            description="Conversational interface for parsing user scraping requests",
            is_active=True
        )

        db.add(scraping_prompt)
        db.add(chat_prompt)
        db.commit()

        print("✓ Successfully seeded agent prompts:")
        print(f"  - scraping_agent (ID: {scraping_prompt.id})")
        print(f"  - chat_agent (ID: {chat_prompt.id})")

    except Exception as e:
        print(f"Error seeding prompts: {str(e)}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_prompts()
