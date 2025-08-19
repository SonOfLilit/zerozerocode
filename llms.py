import os
import logging
from typing import Callable, Generic, ParamSpec, Type, TypeVar

import logfire
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.settings import ModelSettings

load_dotenv()

logfire.configure(token=os.environ["PYDANTIC_LOGFIRE_API_KEY"])
logfire.instrument_pydantic_ai()
logfire.instrument_httpx(capture_all=True)
logging.basicConfig(level=logging.DEBUG)

model = GoogleModel(
    "gemini-2.5-flash", provider="google-gla", settings=ModelSettings(max_tokens=5000)
)


P = ParamSpec("P")  # Captures parameter specification
M = TypeVar("M", bound=BaseModel)  # Captures return type


class ContextualModel(BaseModel, Generic[M]):
    """Base class for models that extend another model with context"""

    pass


C = TypeVar("C", bound=ContextualModel)


def add_context(new_model: Type[C]) -> Callable[[Callable[P, M]], Callable[P, C]]:
    def wrapper(func: Callable[P, M]) -> Callable[P, C]:
        key = "issue"

        def wrapped(*args: P.args, **kwargs: P.kwargs) -> C:
            context = args[0]

            result = func(*args, **kwargs)
            return new_model(**result.model_dump(), **{key: context})

        return wrapped

    return wrapper


def add_context_list(
    new_model: Type[C],
) -> Callable[[Callable[P, list[M]]], Callable[P, list[C]]]:
    def wrapper(func: Callable[P, list[M]]) -> Callable[P, list[C]]:
        key = "issue"

        def wrapped(*args: P.args, **kwargs: P.kwargs) -> list[C]:
            assert len(args) == 1
            context = args[0]

            with logfire.span(func.__name__, input=context) as span:
                results = func(*args, **kwargs)
                span.set_attribute("output", results)
            return [
                new_model(**result.model_dump(), **{key: context}) for result in results
            ]

        return wrapped

    return wrapper
