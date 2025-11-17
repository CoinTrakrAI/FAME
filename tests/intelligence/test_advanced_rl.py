import pytest

from intelligence.advanced_rl import HierarchicalRLAgent, MetaLearner, WorldModel, torch


def test_world_model_imagine():
    world = WorldModel()
    result = world.imagine(state={"s": 1}, action={"a": 0})
    assert "next_state" in result
    assert "reward" in result


def test_meta_learner_adapt():
    meta = MetaLearner()
    params = {"w": 1.0}
    grad = {"w": 0.1}
    updated = meta.adapt(params, grad)
    assert "w" in updated


@pytest.mark.skipif(torch is None, reason="Torch not available")
def test_hierarchical_agent_forward_with_torch():
    agent = HierarchicalRLAgent()
    state = torch.randn(2, 128)
    actions, skill_logits, value, skill_idx = agent(state)
    assert actions.shape[0] == 2
    assert skill_logits.shape[0] == 2

