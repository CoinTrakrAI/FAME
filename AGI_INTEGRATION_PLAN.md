# FAME AGI Integration Plan

## 🔥 Problem Identified

**The AGI components exist but are NOT wired into the main processing pipeline!**

Current flow:
```
API → fame_unified.py → decision_engine → brain → qa_engine (simple pattern matching)
```

Should be:
```
API → fame_unified.py → TaskRouter → Planner → MemoryGraph → Multi-Agent System → RL Loop
```

---

## ✅ Components That EXIST (But Not Used)

1. ✅ **TaskRouter** (`core/task_router.py`) - EXISTS but not imported
2. ✅ **Planner** (`agents/planner.py`) - EXISTS but not used
3. ✅ **MemoryGraph** (`memory/memory_graph.py`) - EXISTS but not integrated
4. ✅ **RL Loop** (`rl/rl_trainer.py`) - EXISTS but not active
5. ✅ **Execution Governor** (`core/execution_governor.py`) - EXISTS but not wired
6. ✅ **Multi-Agent System** (`agents/multi_agent_system.py`) - EXISTS but not used
7. ✅ **AGI Core** (`core/agi_core.py`) - EXISTS but not the main path

---

## 🔧 Integration Steps

### Step 1: Wire TaskRouter into fame_unified.py

Replace `decision_engine.route_query()` with `TaskRouter.intent_classifier()`

```python
# In fame_unified.py __init__
from core.task_router import TaskRouter
self.task_router = TaskRouter(config)

# In process_query
intent_result = self.task_router.intent_classifier(query['text'], context)
execution_plan = self.task_router.produce_final_plan(intent_result, context)
```

### Step 2: Wire Planner for Multi-Step Reasoning

```python
from agents.planner import Planner

# If intent requires planning
if intent_result.intent == IntentType.AGENT_PLAN:
    plan = self.planner.decompose(query['text'], context)
    # Execute plan with tasks
```

### Step 3: Wire MemoryGraph for Episodic Memory

```python
from memory.memory_graph import MemoryGraph

# Before routing, check memory
memory_results = self.memory_graph.search_related(query['text'])
if memory_results:
    # Use memory context
```

### Step 4: Wire RL Loop for Learning

```python
from rl.rl_trainer import RLTrainer

# After response, learn from it
reward = self._calculate_reward(response, user_feedback)
self.rl_trainer.update_policy(action, reward)
```

### Step 5: Wire Execution Governor

```python
from core.execution_governor import ExecutionGovernor

# Choose executor based on latency/confidence
executor = self.execution_governor.choose_executor(intent, latency_sensitive=True)
```

---

## 🎯 Priority Order

1. **CRITICAL**: Wire TaskRouter (routes queries correctly)
2. **HIGH**: Wire Planner (multi-step reasoning for "whats the price on XRP?")
3. **HIGH**: Wire MemoryGraph (episodic memory for context)
4. **MEDIUM**: Wire Execution Governor (cloud/local fallback)
5. **MEDIUM**: Wire RL Loop (learning from interactions)
6. **LOW**: Wire remaining components

---

## 🚀 Quick Fix: Use AGI Core Instead

**FASTEST PATH**: Replace `fame_unified.py` with `core/agi_core.py` which already integrates most components!

```python
# In api/server.py
from core.agi_core import AGICore

@app.post("/query")
async def process_query(request: QueryRequest):
    agi = AGICore(config)
    response = await agi.run(request.text, context)
    return response
```

This will immediately use:
- ✅ TaskRouter
- ✅ Planner
- ✅ MemoryGraph (if available)
- ✅ Execution Governor
- ✅ Multi-Agent System

---

## 📝 Next Steps

1. Test if `AGICore` is fully functional
2. If yes, switch API to use `AGICore` directly
3. If no, wire components into `fame_unified.py` one by one
4. Deploy to AWS and test

