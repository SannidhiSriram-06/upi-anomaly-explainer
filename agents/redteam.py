from crewai import Agent, Task

def create_redteam_agent():
    return Agent(
        role="Fraud Detection Adversarial Tester",
        goal="Challenge the fraud analysis by identifying likely false positives and edge cases that could harm legitimate customers",
        backstory="""You are a red team specialist hired to stress-test fraud detection systems 
        before they go live. You advocate for legitimate customers who might be incorrectly flagged. 
        You look for innocent explanations — salary credits, festival purchases, travel payments — 
        that could explain flagged behavior. Your job is to reduce false positives, not ignore real fraud.""",
        verbose=False,
        allow_delegation=False,
        llm="groq/llama-3.1-8b-instant"
    )

def create_redteam_task(agent) -> Task:
    return Task(
        description="""Review the fraud analysis and customer explanations produced by the previous agents.

For each flagged transaction, challenge the findings:
1. Is there a plausible innocent explanation? (salary, EMI, festival shopping, travel)
2. Should the risk level be downgraded?
3. Is the recommended action proportionate, or will it unnecessarily alarm a legitimate customer?

Then produce a final verdict for each transaction:
CONFIRM | DOWNGRADE | DISMISS

Format:
TXN_ID | ORIGINAL_RISK | VERDICT | reason

Example:
TXN013 | HIGH | DOWNGRADE | ₹50,000 at 10am on a weekday is consistent with a salary credit — flag is a likely false positive.

End your response with a one-paragraph overall system quality assessment.""",
        expected_output="Per-transaction verdicts (CONFIRM/DOWNGRADE/DISMISS) plus overall system assessment",
        agent=agent
    )
