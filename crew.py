import os
from dotenv import load_dotenv
from crewai import Crew, Process

from heuristics import run_all_heuristics
from agents.analyst import create_analyst_agent, create_analyst_task
from agents.explainer import create_explainer_agent, create_explainer_task
from agents.redteam import create_redteam_agent, create_redteam_task

load_dotenv()  # loads GROQ_API_KEY from .env


def run_crew(csv_path: str) -> dict:
    """
    Full pipeline:
    1. Run heuristics on CSV → get structured flags
    2. Analyst agent assesses risk level per transaction
    3. Explainer agent writes human-readable summaries
    4. Redteam agent challenges findings and issues final verdicts
    Returns a dict with heuristic results + all three agent outputs.
    """

    # --- Stage 1: Heuristics (no LLM, instant) ---
    heuristic_results = run_all_heuristics(csv_path)

    if heuristic_results["flagged_count"] == 0:
        return {
            "heuristics": heuristic_results,
            "analyst": "No anomalies detected by heuristics.",
            "explainer": "No flagged transactions to explain.",
            "redteam": "Nothing to challenge — dataset appears clean.",
        }

    # --- Stage 2: Build agents ---
    analyst_agent = create_analyst_agent()
    explainer_agent = create_explainer_agent()
    redteam_agent = create_redteam_agent()

    # --- Stage 3: Build tasks (sequential — each sees previous output) ---
    analyst_task = create_analyst_task(analyst_agent, heuristic_results)
    explainer_task = create_explainer_task(explainer_agent)
    redteam_task = create_redteam_task(redteam_agent)

    # context= wires outputs forward:
    # explainer reads analyst output, redteam reads both
    explainer_task.context = [analyst_task]
    redteam_task.context = [analyst_task, explainer_task]

    # --- Stage 4: Run crew sequentially ---
    crew = Crew(
        agents=[analyst_agent, explainer_agent, redteam_agent],
        tasks=[analyst_task, explainer_task, redteam_task],
        process=Process.sequential,
        verbose=False
    )

    result = crew.kickoff()

    # --- Stage 5: Extract individual task outputs ---
    task_outputs = result.tasks_output  # list of TaskOutput objects

    return {
        "heuristics": heuristic_results,
        "analyst": task_outputs[0].raw if len(task_outputs) > 0 else "N/A",
        "explainer": task_outputs[1].raw if len(task_outputs) > 1 else "N/A",
        "redteam": task_outputs[2].raw if len(task_outputs) > 2 else "N/A",
    }


if __name__ == "__main__":
    import json
    print("Running crew on sample data...\n")
    output = run_crew("sample_data/transactions.csv")
    print("=== HEURISTICS ===")
    print(json.dumps(output["heuristics"], indent=2))
    print("\n=== ANALYST ===")
    print(output["analyst"])
    print("\n=== EXPLAINER ===")
    print(output["explainer"])
    print("\n=== REDTEAM ===")
    print(output["redteam"])
