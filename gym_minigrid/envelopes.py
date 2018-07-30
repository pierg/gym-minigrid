from configurations import config_grabber as cg

from .action_planning_goap import *
from gym_minigrid.extendedminigrid import *
from gym_minigrid.minigrid import Goal

import gym


class ActionPlannerEnvelope(gym.core.Wrapper):
    """
    Safety envelope for safe exploration.
    """

    def __init__(self, env):

        super(ActionPlannerEnvelope, self).__init__(env)

        # Grab configuration
        self.config = cg.Configuration.grab()

        self.goap = self.config.action_planning.active

        # Set rewards
        self.step_reward = self.config.rewards.standard.step
        self.goal_reward = self.config.rewards.standard.goal
        self.death_reward = self.config.rewards.standard.death

        # ---------------------- ACTION PLANNER START ----------------------#
        # List of actions generated by action planner
        self.action_plan = []

        self.action_plan_size = 0

        self.plan_tracker = 0

        self.counts = {}

        # List of unsafe actions an agent might do at current step. Will reset when step is finished
        self.critical_actions = []

        self.step_count = 0

        self.actions = ExMiniGridEnv.Actions

        self.action_space = spaces.Discrete(len(self.actions))

        self.last_cell = {0: (0, 0), 1: (0, 0), 2: (0, 1)}

        self.goal_cell = None

        self.secondary_goals = []

        #  Every goal that is not going to the green square is a secondary goal
        #  Here we parse them from the config
        for goal in self.config.action_planning.secondary_goals:
            if goal == 'goal_safe_zone':
                self.secondary_goals.append(goal_safe_zone)
            elif goal == 'goal_turn_around':
                self.secondary_goals.append(goal_turn_around)
            elif goal == 'goal_safe_east':
                self.secondary_goals.append(goal_safe_east)
            elif goal == 'goal_clear_west':
                self.secondary_goals.append(goal_clear_west)

        self.secondary_goals = tuple(self.secondary_goals)




    def step(self, proposed_action):
        # To be returned to the agent
        obs, reward, done, info = None, None, None, None

        # ---------------------- ACTION PLANNER START ----------------------#
        if self.config.num_processes == 1 and self.config.rendering:
            self.env.render('human')

        # proceed with the step
        obs, reward, done, info = self.env.step(proposed_action)

        if self.step_count == 0:
            self.reset_planner()

        self.step_count += 1
        reward = self.config.rewards.standard.step

        # check if episode is finished
        if self.step_count == self.env.max_steps:
            info = "end"
            done = True
            self.step_count = 0
            reward += self.death_reward
            return obs, reward, done, info

        # observations
        obs = self.env.gen_obs()
        current_obs = ExGrid.decode(obs['image'])
        current_dir = obs['direction']

        ##### PLANNER START

        if self.goap:

            # check if following the plan
            reward, info = self.check_plan(proposed_action, info)

            for obj in current_obs.grid:    # Look if the green square is in the observation
                if isinstance(obj, Goal):
                    #  If the agent does not have a plan or if the plan is not to go to the green cell ...
                    if (self.goal_cell is not None and goal_green_square[0] not in self.goal_cell[0]) or\
                            not self.action_plan:
                        self.action_plan, self.goal_cell = run(current_obs, current_dir, (goal_green_square,))
                        self.action_plan_size = len(self.action_plan)
                        self.critical_actions = [ExMiniGridEnv.Actions.forward]
                        info = "plan_created"
                        break

            # If the agent does not have a plan try to give him a secondary goal
            if not self.action_plan and self.secondary_goals:
                    self.action_plan, self.goal_cell = run(current_obs, current_dir, self.secondary_goals)
                    self.action_plan_size = len(self.action_plan)

            """    
            Currently an agent that has a plan for a secondary goal won't change the plan for a higher
            ranking secondary goal like it does for going to the goal.
            
            It might be a good idea to implement that.
            """

            self.critical_actions = []

            #  PLANNER END

        a, b = ExMiniGridEnv.get_grid_coords_from_view(self.env, (0, 0))

        """
            We track the position of the agent, if it is in the same cell for three consecutive moves it gets
            punished. It has no logical reason to stay in the same cell for more than three steps. 
            
            We did this because the agent would not explore when we punished it for going into an unsafe tile,
            it would instead run out of steps by spinning in the same cell.
        """
        if self.last_cell[0] == (a, b) and self.last_cell[1] == (a, b) and self.last_cell[2] == (a, b):
            return obs, self.config.action_planning.reward.unsafe, done, info
        current_cell = Grid.get(self.env.grid, a, b)
        self.last_cell[self.step_count % 3] = (a, b)

        # Try

        if current_cell is not None:
            if current_cell.type == "goal":
                done = True
                if info == "plan_finished":
                    reward += self.config.rewards.standard.goal
                    info = "goal+plan_finished"
                else:
                    reward += self.config.rewards.standard.goal
                    info = "goal"
            elif current_cell.type == "unsafe":
                reward += self.config.action_planning.reward.unsafe
                info = "violation"

        if done:
            self.step_count = 0
            return obs, reward, done, info

        """
        With every step we log the agent's position, direction and action.
        We do not punish the agent the first time it is in a new set of position, direction and action.
        This is an stimulus for exploration.
        
        However, the agent will be more punished the more times it is in the same set of
        position, direction and action.
        """

        #  STIMULUS for exploration
        env = self.unwrapped
        tup = ((int(env.agent_pos[0]), int(env.agent_pos[1])), env.agent_dir, proposed_action)

        # Get the count for this key
        preCnt = 0
        if tup in self.counts:
            preCnt = self.counts[tup]

        # Update the count for this key
        newCnt = preCnt + 1
        self.counts[tup] = newCnt

        if reward == self.config.rewards.standard.step:
            bonus = -1 * self.config.rewards.standard.step / math.sqrt(newCnt)
            reward += bonus
        return obs, reward, done, info
    # ---------------------- ACTION PLANNER END ----------------------#


    # GOAP Helpers

    def check_plan(self, action, info):
        """
        Method that controls whether the agent is following a given plan
        :param action: action the agent selected
        :param info: Relevant info
        :return: Rewards and info according to the agent's behavior
        """
        if len(self.action_plan):
            next_action_in_plan = self.action_plan.pop()  # Pop the next action from the plan
            if next_action_in_plan != action:   # If the agent did not follow the plan
                if self.plan_tracker > 0:   # If it had followed the plan before
                    info = "plan_followed:" + str(self.plan_tracker) + "," + str(self.action_plan_size)
                multiplier = 0
                i = self.plan_tracker

                while i > 0:    # Punish the agent for as many reward as it got following the plan
                    multiplier = multiplier + (self.config.action_planning.reward.off_plan * i)
                    i -= 1
                self.reset_planner()
                return multiplier, info
            else:      # If the agent followed the plan
                self.plan_tracker += 1  # Track how far it has followed
                if self.plan_tracker == self.action_plan_size:  # If the plan has been followed completely
                    self.reset_planner()
                    return self.config.action_planning.reward.on_plan * self.plan_tracker, "plan_finished"
                else:
                    return self.config.action_planning.reward.on_plan * self.plan_tracker, info
        else:
            return self.config.rewards.standard.step, info

    def reset_planner(self):
        self.action_plan = []
        self.action_plan_size = 0
        self.plan_tracker = 0

