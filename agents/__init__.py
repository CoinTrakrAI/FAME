"""FAME Advanced Reasoning Agents"""

try:
    from agents.tree_of_thoughts import TreeOfThoughts
    from agents.mcts_decision_maker import MCTSDecisionMaker
    from agents.graph_reasoner import KnowledgeGraphReasoner
    from agents.dual_process_architecture import DualProcessArchitecture, FastIntuitiveModel, SlowReasoningModel
    from agents.multi_agent_debate import MultiAgentDebate, SpecialistAgent, JudgeAgent
    from agents.fame_reasoning_engine import FAMEReasoningEngine
    
    __all__ = [
        'TreeOfThoughts',
        'MCTSDecisionMaker',
        'KnowledgeGraphReasoner',
        'DualProcessArchitecture',
        'FastIntuitiveModel',
        'SlowReasoningModel',
        'MultiAgentDebate',
        'SpecialistAgent',
        'JudgeAgent',
        'FAMEReasoningEngine'
    ]
except ImportError as e:
    # Components may not all be available
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Some advanced reasoning components not available: {e}")
    __all__ = []
