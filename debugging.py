import logging


from llms import add_context, add_context_list
from models import (
    ExperimentDesign,
    ExperimentDesignData,
    ExperimentEstimate,
    ExperimentEstimateData,
    ExperimentResultData,
    Issue,
    ExperimentResult,
    Failure,
    Theory,
)
from agents.brainstorm_theories import brainstorm_theories


logger = logging.getLogger(__name__)

DEBUG_ROUNDS = 5
ODDS_FACTOR = 1
COST_FACTOR = 1


def debug_issue(issue: Issue) -> ExperimentResult | Failure:
    original_issue = issue
    lab_log: list[ExperimentResult] = []
    lab_log_summary = ""
    for i in range(DEBUG_ROUNDS):
        theories = brainstorm_theories(issue)
        experiments_with_estimates = []
        for theory in theories:
            experiments = brainstorm_experiments(theory)
            experiments_with_estimates += [
                estimate_cost_and_odds(e) for e in experiments
            ]
        experiments_worth_running = choose_experiments_worth_running(
            experiments_with_estimates
        )
        falsified_theories = set()
        for experiment in experiments_worth_running:
            if experiment.theory.key in falsified_theories:
                logger.info(
                    f"Skipping experiment {experiment}, theory already falsified"
                )
                continue
            result = run_experiment(experiment)
            if result.is_theory_correct:
                return result
            if result.is_theory_correct is not None:
                falsified_theories.add(experiment.theory.key)
            lab_log.append(result)
            # TODO: adjust estimates based on what we learned?
        lab_log_summary = summarize_lab_log(lab_log)
        issue = Issue(description=f"{original_issue.description}\n\n{lab_log_summary}")
    return Failure(
        issue=issue,
        summary=f"Failed to debug issue.\n\n{lab_log_summary}",
        lab_log=lab_log,
    )


@add_context_list(ExperimentDesign)
def brainstorm_experiments(theory: Theory) -> list[ExperimentDesignData]:
    return [
        ExperimentDesign(theory=theory, description="read the code"),
        ExperimentDesign(theory=theory, description="run it and see what happens"),
    ]


@add_context(ExperimentEstimate)
def estimate_cost_and_odds(experiment: ExperimentDesign) -> ExperimentEstimateData:
    return ExperimentEstimate(experiment=experiment, odds=1, cost=0)


@add_context_list(ExperimentDesign)
def choose_experiments_worth_running(
    estimates: list[ExperimentEstimate],
) -> list[ExperimentDesign]:
    sorted_estimates = sorted(estimates, key=lambda e: e.roi_estimate)
    return [
        e.experiment
        for i, e in enumerate(sorted_estimates)
        if i < 3 or e.roi_estimate > 0
    ]


@add_context(ExperimentResult)
def run_experiment(experiment: ExperimentDesign) -> ExperimentResultData:
    return ExperimentResultData(is_theory_correct=None, summary="", detailed_log="")


def summarize_lab_log(results: list[ExperimentResult]) -> str:
    return "\n\n".join([r.summary for r in results])
