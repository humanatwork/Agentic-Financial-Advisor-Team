
from langchain_core.messages import HumanMessage

from agents.state import AgentState, show_agent_reasoning

import pandas as pd

import numpy as np

import json

from tools.api import get_insider_trades

##### Sentiment Agent #####
def sentiment_agent(state: AgentState):
    """Analyzes market sentiment and generates trading signals."""
    data = state["data"]
    end_date = data["end_date"]
    # Get the insider trades
    insider_trades = get_insider_trades(
        ticker=data["ticker"], 
        end_date=end_date,
        limit=5,
    )

    # Get the signals from the insider trades
    transaction_shares = pd.Series([t['transaction_shares'] for t in insider_trades]).dropna()
    bearish_condition = transaction_shares < 0
    signals = np.where(bearish_condition, "bearish", "bullish").tolist()

    # Determine overall signal
    bullish_signals = signals.count("bullish")
    bearish_signals = signals.count("bearish")
    if bullish_signals > bearish_signals:
        overall_signal = "bullish"
    elif bearish_signals > bullish_signals:
        overall_signal = "bearish"
    else:
        overall_signal = "neutral"

    # Calculate confidence level based on the proportion of indicators agreeing
    total_signals = len(signals)
    confidence = max(bullish_signals, bearish_signals) / total_signals

    message_content = {
        "signal": overall_signal,
        "confidence": f"{round(confidence * 100)}%",
        "reasoning": f"Bullish signals: {bullish_signals}, Bearish signals: {bearish_signals}"
    }

    # Print the reasoning if the flag is set
    if state["metadata"]["show_reasoning"]:
        show_agent_reasoning(message_content, "Sentiment Analysis Agent")

    # Create the sentiment message
    message = HumanMessage(
        content=json.dumps(message_content),
        name="sentiment_agent",
    )

    return {
        "messages": [message],
        "data": data,
    }