from pydantic import BaseModel


class Issue(BaseModel):
    description: str


class TheoryData(BaseModel):
    description: str
    odds: float

    @property
    def key(self):
        return self.description


class Theory(TheoryData):
    issue: Issue


class ExperimentDesignData(BaseModel):
    description: str


class ExperimentDesign(ExperimentDesignData):
    theory: Theory


class ExperimentEstimateData(BaseModel):
    odds: float
    cost: float


class ExperimentEstimate(ExperimentEstimateData):
    experiment: ExperimentDesign

    @property
    def roi_estimate(self):
        # ROI = 1 [value of success] * odds [of success, 0-1] - cost
        return (
            ODDS_FACTOR * self.experiment.theory.odds * self.odds
            - COST_FACTOR * self.cost
        )


class ExperimentResultData(BaseModel):
    is_theory_correct: bool | None
    summary: str
    detailed_log: str


class ExperimentResult(ExperimentResultData):
    experiment: ExperimentDesign


class Failure(BaseModel):
    issue: Issue
    summary: str
    lab_log: list[ExperimentResult]
