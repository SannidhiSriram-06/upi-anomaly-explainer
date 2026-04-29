from crewai import Agent, Task

def create_explainer_agent():
    return Agent(
        role="Fraud Communication Specialist",
        goal="Translate technical fraud findings into clear, human-readable explanations for bank customers and compliance teams",
        backstory="""You work in the customer trust division of a major Indian bank. 
        Your job is to take technical fraud analysis and turn it into plain English 
        that a non-technical person can understand. You write clearly, avoid jargon, 
        and always explain WHY something looks suspicious without being alarmist.""",
        verbose=False,
        allow_delegation=False,
        llm="groq/llama-3.1-8b-instant"
    )

def create_explainer_task(agent, analyst_output_placeholder: str = "") -> Task:
    return Task(
        description="""You will receive a structured fraud analysis from the analyst agent.
        
For each HIGH and MEDIUM risk transaction, write a clear explanation block with:
1. A one-line summary a customer would understand
2. What specific behavior triggered the alert
3. Recommended action (e.g. "Contact your bank immediately", "Verify this transaction", "Likely safe")

Format each block as:
---
Transaction: TXN_ID
Risk: RISK_LEVEL  
Summary: <one line plain English summary>
Why flagged: <what the system detected>
Action: <recommended next step>
---

Skip LOW risk transactions entirely. Be concise — each block should be 4-5 lines max.""",
        expected_output="Formatted explanation blocks for each HIGH and MEDIUM risk transaction",
        agent=agent
    )
