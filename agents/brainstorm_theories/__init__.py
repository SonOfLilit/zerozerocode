from pydantic_ai import Agent, RunContext

from llms import model, add_context_list
from models import Issue, Theory, TheoryData


brainstorm_theories_agent = Agent(
    model=model,
    deps_type=Issue,
    output_type=list[TheoryData],
    system_prompt=(),
)


@brainstorm_theories_agent.system_prompt
def system_prompt(ctx: RunContext[Issue]) -> str:
    return f"""\
Brainstorm theories for what causes this issue:

{ctx.deps.description}

Theories could be either specific (e.g. "the code that reads a document falsely assume that documents are non-empty") or significant narrowing down (e.g. "there's a bug in how we read a document" and "there's a bug in how we write a document").

First, brainstorm 10 theories. Finally, output a list of the likely theories and their odds."""


@add_context_list(Theory)
def brainstorm_theories(issue: Issue) -> list[TheoryData]:
    return brainstorm_theories_agent.run_sync(deps=issue).output


if __name__ == "__main__":
    import issues

    for issue_data in issues.ISSUES[3:]:
        project, issue = issue_data
        theories = brainstorm_theories(Issue(description=issue))
        for theory in theories:
            print(theory.odds, theory.description)
        breakpoint()
