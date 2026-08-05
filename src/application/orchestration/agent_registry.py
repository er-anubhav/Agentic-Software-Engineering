class AgentRegistry:
    """
    Registry for all engineering agents.
    """

    def __init__(self):
        self._agents = {}

    def register(self, name, agent):
        self._agents[name] = agent

    def get(self, name):
        return self._agents.get(name)

    def list_agents(self):
        return list(self._agents.keys())