from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

import yaml
from telegram import Bot


LOGGER = logging.getLogger(__name__)


def load_settings(path: str = "configs/settings.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def format_alert_message(result: Dict[str, Any]) -> str:
    state = result["state"]
    signal = result["signal"]
    negotiation = result["negotiation"]
    behavior = result["behavior"]
    alerts = result["alerts"]

    lines = [
        "*PetroStratum Alert*",
        "",
        f"*Signal:* {signal['signal']}",
        f"*Regime:* {signal['regime']}",
        f"*Confidence:* {float(signal['confidence']):.2f}",
        "",
        "*State:*",
        f"- SG: {float(state['sg']):.3f}",
        f"- CP: {float(state['cp']):.3f}",
        f"- Theta_eff: {float(state['theta_eff']):.3f}",
        f"- P(Break): {float(state['p_break']):.3f}",
        "",
        "*Behavior:*",
        f"- Effective risk: {float(behavior['effective_risk']):.3f}",
        f"- Confidence: {float(behavior['confidence']):.3f}",
        "",
        "*Negotiation:*",
        f"- P(Agreement): {float(negotiation['p_agreement']):.3f}",
        f"- P(Execution): {float(negotiation['p_execution']):.3f}",
        f"- State: {negotiation['state']}",
        "",
        "*Alerts:*",
    ]

    for a in alerts:
        lines.append(f"- [{a['severity']}] {a['title']}: {a['message']}")

    return "\n".join(lines)


async def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "Markdown",
) -> None:
    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=parse_mode,
        disable_web_page_preview=True,
    )


def send_alert_sync(
    result: Dict[str, Any],
    settings_path: str = "configs/settings.yaml",
) -> None:
    settings = load_settings(settings_path)
    tg = settings["telegram"]

    if not tg.get("enabled", False):
        LOGGER.info("Telegram disabled in settings.")
        return

    message = format_alert_message(result)

    asyncio.run(
        send_telegram_message(
            bot_token=tg["bot_token"],
            chat_id=tg["chat_id"],
            text=message,
            parse_mode=tg.get("parse_mode", "Markdown"),
        )
    )
