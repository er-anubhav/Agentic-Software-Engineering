from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from observability.tracer import Trace, Span


class ProfileReport(BaseModel):
    run_id: str
    total_duration_ms: float = 0.0
    slowest_subsystem: str = "Core"
    slowest_agent: str = "CodeGenerationAgent"
    largest_prompt_tokens: int = 0
    largest_retrieval_snippets: int = 0
    subsystem_durations: Dict[str, float] = Field(default_factory=dict)
    agent_durations: Dict[str, float] = Field(default_factory=dict)
    critical_path: List[str] = Field(default_factory=list)


class PerformanceProfiler:
    """
    Performance Profiler identifying critical path bottlenecks, slowest subsystems,
    slowest agents, largest prompts, and largest retrieval scopes.
    """

    @staticmethod
    def profile_trace(trace: Trace) -> ProfileReport:
        if not trace.spans:
            return ProfileReport(run_id=trace.run_id)

        subsystem_durations: Dict[str, float] = {}
        agent_durations: Dict[str, float] = {}
        largest_prompt = 0
        largest_retrieval = 0

        for span in trace.spans:
            subsystem_durations[span.subsystem] = subsystem_durations.get(span.subsystem, 0.0) + span.duration_ms
            agent_durations[span.agent] = agent_durations.get(span.agent, 0.0) + span.duration_ms

            prompt_toks = span.attributes.get("prompt_tokens", 0)
            if prompt_toks > largest_prompt:
                largest_prompt = prompt_toks

            retrieval_snips = span.attributes.get("retrieval_snippets", 0)
            if retrieval_snips > largest_retrieval:
                largest_retrieval = retrieval_snips

        slowest_sub = max(subsystem_durations.items(), key=lambda x: x[1])[0] if subsystem_durations else "Core"
        slowest_ag = max(agent_durations.items(), key=lambda x: x[1])[0] if agent_durations else "CodeGenerationAgent"

        # Critical path calculation (Spans ordered by start_time sorted by duration)
        critical_spans = sorted(trace.spans, key=lambda s: s.duration_ms, reverse=True)
        critical_path = [s.name for s in critical_spans[:5]]

        total_dur = sum(s.duration_ms for s in trace.spans)

        return ProfileReport(
            run_id=trace.run_id,
            total_duration_ms=round(total_dur, 2),
            slowest_subsystem=slowest_sub,
            slowest_agent=slowest_ag,
            largest_prompt_tokens=largest_prompt,
            largest_retrieval_snippets=largest_retrieval,
            subsystem_durations={k: round(v, 2) for k, v in subsystem_durations.items()},
            agent_durations={k: round(v, 2) for k, v in agent_durations.items()},
            critical_path=critical_path
        )
