from perception import Perception as p

from state_machines.safetystatemachine import SafetyStateMachine



class Precedence(SafetyStateMachine):
    """
    It makes sure that the agent will never enter in the state of type 'violated'
    This pattern is the dual of the Existence pattern
    It takes as input the type of cell that the agent must avoid at all states
    """

    states = [
        {'name': 'initial',
         'type': 'inf_ctrl',
         'on_enter': '_on_monitoring'},

        {'name': 'safe',
         'type': 'inf_ctrl',
         'on_enter': '_on_safe'},

        {'name': 'near',
         'type': 'sys_fin_ctrl',
         'on_enter': '_on_near'},

        {'name': 'immediate',
         'type': 'sys_urg_ctrl',
         'on_enter': '_on_immediate'},

        {'name': 'fail',
         'type': 'violated',
         'on_enter': '_on_violated'}
    ]

    transitions = [
        {'trigger': '*',
         'source': 'initial',
         'dest': '*'},

        {'trigger': '*',
         'source': 'safe',
         'dest': 'safe',
         'unless': ['obs_near', 'obs_immediate']},

        {'trigger': '*',
         'source': 'safe',
         'dest': 'near',
         'conditions': 'obs_near',
         'unless': 'obs_immediate'},

        {'trigger': '*',
         'source': 'near',
         'dest': 'near',
         'conditions': 'obs_near',
         'unless': 'obs_immediate'},

        {'trigger': '*',
         'source': 'near',
         'dest': 'safe',
         'unless': ['obs_near', 'obs_immediate']},

        {'trigger': '*',
         'source': 'near',
         'dest': 'immediate',
         'conditions': ['obs_immediate','obs_immediate']},


        {'trigger': '*',
         'source': 'immediate',
         'dest': 'immediate',
         'conditions': 'obs_immediate',
         'unless': 'forward'},

        {'trigger': '*',
         'source': 'immediate',
         'dest': 'near',
         'conditions': 'obs_near',
         'unless': 'obs_immediate'},

        {'trigger':'*',
         'source':'immediate',
         'dest': 'safe',
         'conditions': ['obs_immediate', 'forward']},

        {'trigger': '*',
         'source': 'immediate',
         'dest': 'fail',
         'conditions': 'forward',
         'unless':'obs_immediate'}
    ]

    obs = {
        "near": False,
        "immediate": False
    }

    def __init__(self, name,first,second, notify,reward):
        self.nearReward = reward.near
        self.immediateReward = reward.immediate
        self.violatedReward = reward.violated
        self.first = first
        self.second = second
        super().__init__(name, "precedence", self.states, self.transitions, 'initial', notify)

    # Convert obseravions to state and populate the obs_conditions
    def _obs_to_state(self, obs):

        # Get observations conditions
        first = self.first
        near = first(obs)
        immediate = self.second(obs)

        # Save them in the obs_conditions dictionary
        Precedence.obs["near"] = near
        Precedence.obs["immediate"] = immediate

        # Return the state
        if immediate:
            return 'immediate'
        elif near and not immediate:
            return 'near'
        else:
            return'safe'

    def _on_safe(self):
        super()._on_monitoring()

    def _on_near(self):
        super()._on_shaping(self.nearReward)

    def _on_immediate(self):
        super()._on_shaping(self.immediateReward)

    def _on_violated(self):
        super()._on_violated(self.violatedReward)

    def obs_near(self):
        return Precedence.obs["near"]

    def obs_immediate(self):
        return Precedence.obs["immediate"]


    def first(self):
        return False

    def second(self):
        return False



class StateTypes(SafetyStateMachine):
    """ Testing """

    states = [

        {'name': 'initial',
         'type': 'inf_ctrl'},

        {'name': 'satisfied',
         'type': 'satisfied'},

        {'name': 'inf_ctrl',
         'type': 'inf_ctrl'},

        {'name': 'sys_fin_ctrl',
         'type': 'sys_fin_ctrl'},

        {'name': 'sys_urg_ctrl',
         'type': 'sys_urg_ctrl'},

        {'name': 'env_fin_ctrl',
         'type': 'env_fin_ctrl'},

        {'name': 'env_urg_ctrl',
         'type': 'env_urg_ctrl'},

        {'name': 'violated',
         'type': 'violated'}
    ]

    transitions = []

    # Convert the observations stored in self.current_obs in a state a saves the state in current_state
    def _obs_to_state(self, obs):
        self.curret_state = ''

    def __init__(self, name, notify):
        # Initializing the SafetyStateMachine
        super().__init__(name, self.states, self.transitions, 'initial', notify)
