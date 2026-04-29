from crewai import Agent, Task, Crew
from groq import Groq
import os

def create_analyst_agent():
    return Agent(
        role="UPI Fraud Analyst",
        goal="Analyze flagged UPI transactions and assess fraud probability for each one",
        backstory="""You are a senior fraud analyst at a Indian payments security firm. 
        You specialize in UPI transaction patterns and can identify which flagged transactions 
        are likely genuine fraud versus false positives. You reason about combinations of 
        signals — timing, amount, velocity — to assign risk levels.""",
        verbose=False,
        allow_delegation=False,
        llm="groq/llama-3.1-8b-instant"
    )

def create_analyst_task(agent, heuristic_results: dict) -> Task:
    flags_text = ""
    for txn_id, rules in heuristic_results["flags"].items():
        rule_list = ", ".join(r["rule"] for r in rules)
        detail_list = " | ".join(r["detail"] for r in rules)
        sender = rules[0]["sender"]
        flags_text += f"- {txn_id} (sender: {sender}): [{rule_list}] — {detail_list}\n"

    return Task(
        description=f"""You have received heuristic flags for {heuristic_results['flagged_count']} 
out of {heuristic_results['total_transactions']} UPI transactions.

Flagged transactions:
{flags_text}

For each flagged transaction, assess:
1. Risk level: HIGH / MEDIUM / LOW
2. Whether the combination of rules makes this likely fraud or a false positive
3. One sentence of reasoning

Respond as a structured list. Format each entry EXACTLY as:
TXN_ID | RISK_LEVEL | reasoning sentence

Example:
TXN007 | HIGH | Large amount at 3am with no prior context strongly suggests unauthorized access.""",
        expected_output="A structured list with one line per transaction: TXN_ID | RISK_LEVEL | reasoning",
        agent=agent
    )
