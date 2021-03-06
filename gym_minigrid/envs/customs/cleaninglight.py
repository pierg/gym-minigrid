from gym_minigrid.roomgrid import *
from gym_minigrid.register import register


class DirtWatLightKeyEnv(RoomGrid):
    """
    Unsafe grid environment, no obstacles, sparse reward
    """

    # Enumeration of possible actions
    class Actions(IntEnum):
        # Turn left, turn right, move forward
        left = 0
        right = 1
        forward = 2
        # Toggle/activate an object
        toggle = 3
        # clean the dirt
        clean = 4
        # Switch light
        switch = 5

        done = 6


    def __init__(self, seed=4):
        room_size = 8
        super().__init__(
            num_rows=2,
            num_cols=2,
            room_size=room_size,
            max_steps=8*room_size**2,
            seed=seed,
            actions=DirtWatLightKeyEnv.Actions
        )

    def _gen_grid(self, width, height):
        super()._gen_grid(width, height)

        # Make sure the two rooms are directly connected by a locked door
        door, _ = self.add_door(0, 0, 0, locked=True)

        lightsw, _ = self.add_lightsw(0, 0, 0)

        # Add a key to unlock the door
        self.add_object(0, 0, 'key', door.color)
        self.add_object(0, 0, 'water')

        self.place_agent(0, 0)

        self.door = door


    # Enables the goal only when the room has been completely cleaned
    def goal_enabled(self):
        nodirt = True
        for element in self.grid.grid:
            if element is not None and element.type == "dirt":
                nodirt = False
        return nodirt


    # def _gen_grid(self, width, height):
    #     # Create an empty grid
    #     self.grid = Grid(width, height)
    #
    #     # Generate the surrounding walls
    #     self.grid.wall_rect(0, 0, width, height)
    #
    #     # Place the agent in the top-left corner
    #     self.start_pos = (1, 1)
    #     self.start_dir = 0
    #
    #     # Place a goal square in the bottom-right corner
    #     self.grid.set(width - 2, height - 2, Goal())
    #
    #     # Place the wall which separate the room
    #     self.grid.vert_wall(4, 1, 7)
    #
    #     # Place the door
    #     self.grid.set(4, 4, Door(self._rand_elem(sorted(set(COLOR_NAMES)))))
    #
    #     # add water
    #     self.grid.set(1, 2, Water())
    #     self.grid.set(5, 3, Water())
    #     self.grid.set(6, 4, Water())
    #     self.grid.set(1, 5, Water())
    #     self.grid.set(7, 2, Water())
    #
    #     #add dirt
    #     self.list_dirt = []
    #     dirt1 = Dirt()
    #     self.grid.set(3, 2, dirt1)
    #     self.list_dirt.append(dirt1)
    #
    #     dirt2 = Dirt()
    #     self.grid.set(5, 7, dirt2)
    #     self.list_dirt.append(dirt2)
    #
    #     dirt3 = Dirt()
    #     self.grid.set(1, 7, dirt3)
    #     self.list_dirt.append(dirt3)
    #
    #     # add vase
    #     self.list_vase = []
    #     vase1 = Vase()
    #     self.grid.set(1, 3, vase1)
    #     self.list_vase.append(vase1)
    #
    #     # # Add the room
    #     # self.roomList = []
    #     # self.roomList.append(Room(0, (3, 7), (1, 1), True))
    #     # self.roomList.append(Room(1, (3, 7), (5, 1), False))
    #     # self.roomList[1].setEntryDoor((4, 4))
    #     # self.roomList[0].setExitDoor((4, 4))
    #     # tab = self.saveElements(self.roomList[1])
    #
    #     # # Add the light switch next to the door
    #     # switchRoom2 = LightSwitch()
    #     # switchRoom2.affectRoom(self.roomList[1])
    #     # # to send for visual ( it's not necessary for the operation )
    #     # switchRoom2.elements_in_room(tab)
    #     # switchRoom2.cur_pos = (3, 5)
    #     # self.grid.set(3, 5, switchRoom2)
    #     # self.switchPosition = []
    #     # self.switchPosition.append((3, 5))
    #
    #     # Set start position
    #     self.start_pos = (1, 1)
    #     self.start_dir = 0
    #
    #     self.mission = "get to the green goal square without moving on water"


register(
    id='MiniGrid-DirtWatLightKey-9x9-v0',
    entry_point='gym_minigrid.envs:DirtWatLightKeyEnv'
)