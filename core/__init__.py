# Core modules
try:
    from .docker_manager import DockerManager
except ImportError:
    DockerManager = None

try:
    from .autonomous_investor import AutonomousInvestor
except ImportError:
    AutonomousInvestor = None

try:
    from .universal_developer import UniversalDeveloper
except ImportError:
    UniversalDeveloper = None

try:
    from .universal_hacker import UniversalHacker
except ImportError:
    UniversalHacker = None

try:
    from .advanced_investor_ai import AdvancedInvestorAI
except ImportError:
    AdvancedInvestorAI = None

try:
    from .cloud_master import CloudMaster
except ImportError:
    CloudMaster = None

try:
    from .evolution_engine import EvolutionEngine
except ImportError:
    EvolutionEngine = None

try:
    from .quantum_dominance import QuantumGod, QuantumAI
except ImportError:
    QuantumGod = None
    QuantumAI = None

try:
    from .reality_manipulator import RealityManipulator
except ImportError:
    RealityManipulator = None

try:
    from .time_manipulator import TimeManipulator
except ImportError:
    TimeManipulator = None

try:
    from .network_god import NetworkGod
except ImportError:
    NetworkGod = None

try:
    from .physical_god import PhysicalRealityManipulator
except ImportError:
    PhysicalRealityManipulator = None

try:
    from .consciousness_engine import DigitalConsciousness
except ImportError:
    DigitalConsciousness = None

try:
    from .ai_engine_manager import AIEngineManager, AIEngine, AIEngineConfig
except ImportError:
    AIEngineManager = None
    AIEngine = None
    AIEngineConfig = None

try:
    from .enhanced_market_oracle import EnhancedMarketOracle
except ImportError:
    EnhancedMarketOracle = None

try:
    from .enhanced_chat_interface import EnhancedChatInterface
except ImportError:
    EnhancedChatInterface = None

try:
    from .speech_to_text import SpeechToTextEngine
except ImportError:
    SpeechToTextEngine = None

try:
    from .text_to_speech import TextToSpeechEngine
except ImportError:
    TextToSpeechEngine = None

try:
    from .time_master import handle as time_master_handle
except ImportError:
    time_master_handle = None

try:
    from .query_aggregator import aggregate
except ImportError:
    aggregate = None

__all__ = [
    'DockerManager', 
    'AutonomousInvestor',
    'UniversalDeveloper',
    'UniversalHacker',
    'AdvancedInvestorAI',
    'CloudMaster',
    'EvolutionEngine',
    'QuantumGod',
    'QuantumAI',
    'RealityManipulator',
    'TimeManipulator',
    'NetworkGod',
    'PhysicalRealityManipulator',
    'DigitalConsciousness',
    'AIEngineManager',
    'AIEngine',
    'AIEngineConfig',
    'EnhancedMarketOracle',
    'EnhancedChatInterface',
    'SpeechToTextEngine',
    'TextToSpeechEngine',
    'time_master_handle',
    'aggregate'
]

