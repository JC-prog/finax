"""LangGraph StateGraph — wires Scout → Analyst → Alert pipeline."""

from langgraph.graph import END, StateGraph

from finax.agents.alert import alert_node
from finax.agents.analyst import analyst_node
from finax.agents.scout import scout_node
from finax.state import FinaxState


def _should_continue_to_analyst(state: FinaxState) -> str:
    return "analyst" if state["news_articles"] else END  # type: ignore[return-value]


def _should_continue_to_alert(state: FinaxState) -> str:
    return "alert" if state["analyzed_articles"] else END  # type: ignore[return-value]


def build_graph():
    builder = StateGraph(FinaxState)

    builder.add_node("scout", scout_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("alert", alert_node)

    builder.set_entry_point("scout")

    builder.add_conditional_edges(
        "scout",
        _should_continue_to_analyst,
        {"analyst": "analyst", END: END},
    )
    builder.add_conditional_edges(
        "analyst",
        _should_continue_to_alert,
        {"alert": "alert", END: END},
    )
    builder.add_edge("alert", END)

    return builder.compile()
