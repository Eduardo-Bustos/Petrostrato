import numpy as np


VALID_SHOCKS = [
    "None",
    "Hormuz Disruption",
    "Lebanon Escalation",
    "Sanctions Tightening",
    "Ceasefire",
]

VALID_NEGOTIATION_STATES = [
    "No Contact",
    "Indirect Talks",
    "Direct Talks",
    "Partial Agreement",
    "Breakdown",
]


def clamp(value, lower
