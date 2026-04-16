"""Simple CLI smoke test for Google AI Studio (Gemini) API connectivity."""
import argparse
import os
from pathlib import Path
import sys


def _ensure_repo_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def _load_root_env() -> None:
    """Load root .env values if they are not already present in environment."""
    repo_root = Path(__file__).resolve().parents[3]
    env_path = repo_root / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Send a simple question to Google AI Studio and print the answer.",
    )
    parser.add_argument(
        "--question",
        default="Xin chao, hay tra loi ngan gon: 2 + 2 bang bao nhieu?",
        help="Question to send to Gemini model.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=256,
        help="Maximum output tokens.",
    )
    parser.add_argument(
        "--thinking-level",
        choices=["low", "medium", "high"],
        default=None,
        help="Gemini thinking level.",
    )
    return parser


def main() -> int:
    _load_root_env()
    _ensure_repo_on_path()

    from llm.config import LLMConfig
    from llm.models import ChatMessage, LLMRequest
    from llm.providers.google_gemini import GoogleGeminiProvider

    args = build_parser().parse_args()
    config = LLMConfig.from_env()
    provider = GoogleGeminiProvider(config)

    try:
        response = provider.generate(
            LLMRequest(
                messages=[ChatMessage(role="user", content=args.question)],
                temperature=args.temperature,
                max_output_tokens=args.max_output_tokens,
                thinking_level=args.thinking_level,
            )
        )
    except Exception as exc:
        print(f"[ERROR] Google AI Studio request failed: {exc}")
        return 1

    print("[OK] Request success")
    print(f"Provider: {response.provider}")
    print(f"Model: {response.model}")
    print("Answer:")
    print(response.text)
    if response.usage:
        print(f"Usage: {response.usage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())