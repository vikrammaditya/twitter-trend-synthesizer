"""
Model Fallback Engine
---------------------
Provides resilient LLM invocation with automatic model rotation on rate-limit errors.

Strategy:
  - Maintain an ordered list of Gemini model names.
  - For each model, retry up to N times (3 by default, 5 for the last model).
  - On a rate-limit (HTTP 429 / ResourceExhausted) error, wait with exponential backoff
    before retrying. After exhausting retries, move to the next model.
  - If ALL models and retries are exhausted, raise a clear error so the caller can
    notify the user and exit gracefully.
"""

import sys
import time
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from config import Config

# Ordered list of Gemini models to attempt, from most preferred to least.
# Only models with active API quota are listed. The last model gets extra
# retries (5 instead of 3).
#
# Quota caps (free tier):
#   gemini-3.5-flash      — RPM: 5,  TPM: 250K, RPD: 20
#   gemini-2.5-flash      — RPM: 5,  TPM: 250K, RPD: 20
#   gemini-3.1-flash-lite — RPM: 15, TPM: 250K, RPD: 500  (best headroom)
GEMINI_MODEL_CHAIN = [
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-3.1-flash-lite",
]

DEFAULT_RETRIES = 3
LAST_MODEL_RETRIES = 5

# Patterns that indicate a rate-limit / quota error OR a model availability
# error (case-insensitive). Model-not-found (404) is included so the engine
# cascades to the next model instead of propagating as a fatal error.
_RATE_LIMIT_PATTERNS = [
    r"429",
    r"rate.?limit",
    r"resource.?exhausted",
    r"quota",
    r"too many requests",
    r"retry.?after",
    r"is not found for API version",
    r"404",
]


def _is_rate_limit_error(error: Exception) -> bool:
    """Return True if the exception looks like a rate-limit / quota error."""
    error_str = str(error).lower()
    for pattern in _RATE_LIMIT_PATTERNS:
        if re.search(pattern, error_str, re.IGNORECASE):
            return True
    return False


def _is_model_not_found(error: Exception) -> bool:
    """Return True if the error indicates the model doesn't exist / is deprecated."""
    error_str = str(error).lower()
    return "is not found for api version" in error_str or "not supported for generatecontent" in error_str


def _build_llm(model_name: str, temperature: float = 0.3) -> ChatGoogleGenerativeAI:
    """Instantiate a LangChain Gemini LLM for the given model name.
    
    max_retries=0 disables LangChain's own internal retry-with-backoff so that
    our fallback engine has full, clean control over retry timing and model
    switching decisions.
    """
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=Config.GEMINI_API_KEY,
        temperature=temperature,
        max_retries=0,
    )


class AllModelsExhaustedError(Exception):
    """Raised when every model in the fallback chain has been exhausted."""
    pass


def invoke_with_fallback(chain_factory, temperature=0.3, invoke_kwargs=None):
    """
    Invoke a LangChain chain with automatic model fallback on rate-limit errors.

    Parameters
    ----------
    chain_factory : callable(llm) -> chain
        A function that receives an LLM instance and returns a ready-to-invoke
        LangChain chain (e.g.  ``lambda llm: prompt | llm | parser``).
    temperature : float
        Temperature setting forwarded to every model.
    invoke_kwargs : dict
        Keyword arguments passed to ``chain.invoke()``.

    Returns
    -------
    result
        The parsed result from the first successful invocation.

    Raises
    ------
    AllModelsExhaustedError
        If every model in the chain has been tried and all retries exhausted.
    """
    if invoke_kwargs is None:
        invoke_kwargs = {}

    total_models = len(GEMINI_MODEL_CHAIN)

    for model_idx, model_name in enumerate(GEMINI_MODEL_CHAIN):
        is_last_model = (model_idx == total_models - 1)
        max_retries = LAST_MODEL_RETRIES if is_last_model else DEFAULT_RETRIES

        print(f"\n🤖 Attempting model: {model_name} "
              f"({'last resort — ' if is_last_model else ''}"
              f"max {max_retries} retries)")

        for attempt in range(1, max_retries + 1):
            try:
                llm = _build_llm(model_name, temperature)
                chain = chain_factory(llm)
                result = chain.invoke(invoke_kwargs)
                print(f"✅ Success with model '{model_name}' on attempt {attempt}.")
                return result

            except Exception as exc:
                if _is_model_not_found(exc):
                    # Model is deprecated or unavailable — skip to next immediately.
                    print(f"   ⛔ Model '{model_name}' is not available (404). "
                          f"Skipping to next model …")
                    break  # break out of retry loop for this model

                elif _is_rate_limit_error(exc):
                    backoff = min(2 ** attempt, 30)  # 2, 4, 8, 16, 30 …
                    print(f"⚠️  Rate-limit hit on '{model_name}' "
                          f"(attempt {attempt}/{max_retries}): {exc}")
                    if attempt < max_retries:
                        print(f"   ⏳ Waiting {backoff}s before retry …")
                        time.sleep(backoff)
                    else:
                        print(f"   ❌ All {max_retries} retries exhausted for '{model_name}'.")
                        if not is_last_model:
                            print(f"   🔄 Switching to next model …")
                else:
                    # Non-rate-limit error — propagate immediately.
                    raise

    # If we reach here, every model + every retry has been exhausted.
    msg = (
        "\n" + "=" * 60 + "\n"
        "🚨 ALL MODELS EXHAUSTED — UNABLE TO COMPLETE REQUEST\n"
        "=" * 60 + "\n"
        "The system attempted the following Gemini models, each with\n"
        "multiple retries, but every attempt was rejected due to\n"
        "rate-limiting / quota errors:\n\n"
    )
    for idx, m in enumerate(GEMINI_MODEL_CHAIN):
        retries = LAST_MODEL_RETRIES if idx == total_models - 1 else DEFAULT_RETRIES
        msg += f"  • {m}  ({retries} retries)\n"
    msg += (
        "\nPossible actions:\n"
        "  1. Wait a few minutes and try again.\n"
        "  2. Check your Gemini API quota at https://aistudio.google.com/\n"
        "  3. Upgrade your API plan for higher rate limits.\n"
        "=" * 60
    )
    print(msg)
    raise AllModelsExhaustedError(msg)
