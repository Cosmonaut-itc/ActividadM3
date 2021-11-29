import numpy as np
# Model design
import agentpy as ap

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import IPython


class Vehicle(ap.Agent):
    def setup(self):
        self.grid = self.model.grid
        self.pos = [0, 0]
        self.road = 1
        self.side = [1, 0]
        self.speed = 1
        self.crossed = False

    def direction(self):
        self.pos = self.grid.positions[self]
        if self.pos[1] == 0:
            self.side = [0, 1]

    def movement(self):
        self.direction()
        return (self.speed * self.side[0], self.speed * self.side[1])

    def route_direction(self):
        self.pos = self.grid.positions[self]
        if self.pos[1] == 0:
            return 'HORIZONTAL'
        return 'VERTICAL'

class StopLight(ap.Agent):
    def setup(self):
        self.status = 1
        self.road = 3
        self.grid = self.model.grid
        self.pos = [0, 0]
        self.route = ''

    def positions(self):
        self.pos = self.grid.positions[self]

    def change_state(self):
        self.positions()
        grid_size = self.p['Grid']
        self.status = 2
        self.road = 2
        if self.model.cars_pos_1 > self.model.cars_pos_2:
            if self.pos[0] == int((grid_size / 2) + 1):
                self.status = 0
                self.road = 4
        elif self.model.cars_pos_1 < self.model.cars_pos_2:
            if self.pos[1] == int((grid_size / 2) + 1):
                self.status = 0
                self.road = 4
        else:
            if self.pos[1] == int((grid_size / 2) + 1):
                self.status = 0
                self.road = 4

class IntersectionModel(ap.Model):
    def setup(self):
        self.counter = 0
        # Define the grid. Hard coded 10x10
        grid_size = self.p['Grid']
        self.grid = ap.Grid(self, [grid_size] * 2, torus=True, track_empty=True)

        self.cars_pos_1 = 0
        self.cars_pos_2 = 0

        # Define the agents
        n_vehicles = self.p['Vehicles']
        n_roads = grid_size * 2

        # Define the agents representing the vehicles
        self.vehicles = ap.AgentList(self, n_vehicles, Vehicle)

        # Define the agent representing the stop sign
        self.stop_light = ap.AgentList(self, 2, StopLight)

        # Creates the atribute grid in both agent vehicles in order to acces values like position
        self.vehicles.grid = self.grid

        self.grid.add_agents(self.stop_light, positions=[(int((grid_size / 2) - 1), int((grid_size / 2) + 1)),
                                                         (int((grid_size / 2) + 1), int((grid_size / 2) - 1))])
        stop_light = self.stop_light
        for light in stop_light:
            if self.grid.positions[light][1] == 0:
                light.route_direction = 'VERTICAL'
            else:
                light.route_direction = 'HORIZONTAL'

        vehicles_positions = []
        for i in range(1, n_vehicles + 1):
            if i % 2 == 0:
                vehicles_positions.append((int(grid_size / 2), 0))
            else:
                vehicles_positions.append((0, int(grid_size / 2)))

    def step(self):

        grid_size = self.p['Grid']
        n_vehicles = self.p['Vehicles']
        if self.counter == 0:
            vehicles_pos = []
            positions = [(0, int(grid_size / 2)), (int(grid_size / 2), 0)]

            for i in range(n_vehicles):
                rand_pos = np.random.randint(0, 2)
                vehicles_pos.append(positions[rand_pos])

            new_car = ap.AgentList(self, 1, Vehicle)
            self.grid.add_agents(self.vehicles, vehicles_pos)
            self.counter += 1

        n_movements = 0
        move_cars = 0
        movement = True
        state = False
        cars_grid = self.vehicles

        for car in cars_grid:
            agent_pos = self.grid.positions[car]
            for i in range(1, int((grid_size / 2))):
                if (int(grid_size / 2) == agent_pos[0]) and (int(i) == agent_pos[1]):
                    self.cars_pos_1 += 1
                    state = True
                if (int(grid_size / 2) == agent_pos[1]) and (int(i) == agent_pos[0]):
                    self.cars_pos_2 += 1
                    state = True
        if state:
            stop_light = self.stop_light
            for light in stop_light:
                if state:
                    light.change_state()
                else:
                    light.status = 1
                    light.road = 3

        for agent in self.grid.agents:
            agent_pos = self.grid.positions[agent]
            movement = True
            if agent.type == 'Vehicle':
                for neighbor in self.grid.neighbors(agent):
                    if agent.route_direction() == 'VERTICAL':
                        if self.grid.positions[neighbor][1] == agent_pos[1] + 1 and self.grid.positions[neighbor][0] == \
                                agent_pos[0]:
                            if neighbor.type == 'Vehicle':
                                movement = False
                                break
                        if self.grid.positions[neighbor][1] == agent_pos[1] and self.grid.positions[neighbor][0] == \
                                agent_pos[0] + 1:
                            if neighbor.type == 'StopSign':
                                if neighbor.status == 2:
                                    movement = False
                                    break
                                else:
                                    self.cars_pos_1 -= 1
                                    break

                    if agent.route_direction() == 'VERTICAL':
                        if self.grid.positions[neighbor][0] == agent_pos[0] + 1 and self.grid.positions[neighbor][1] == \
                                agent_pos[1]:
                            if neighbor.type == 'Vehicle':
                                movement = False
                                break
                        if self.grid.positions[neighbor][0] == agent_pos[0] and self.grid.positions[neighbor][1] == \
                                agent_pos[1] + 1:
                            if neighbor.type == 'StopSign':
                                if neighbor.status == 2:
                                    movement = False
                                    break
                                else:
                                    self.cars_pos_2 -= 1
                                    break
                if movement:
                    coordinates_move = agent.movement()
                    self.grid.move_by(agent, coordinates_move)

    def end(self):
        pass


parameters = {
    'Vehicles': 15,
    'steps': 500,
    'Grid': 25,
}


def animation_plot(model, ax):
    attr_grid = model.grid.attr_grid('road')
    # 0 es verde claro, 1 es gris, 2 es rojo, 3 amarillo, 4 verde fuerte
    color_dict = {0: '#d5e5d5', 1: '#e5e5e5', 2: '#d62c2c', 3: '#FFFF00', 4: '#21d41e',
                  None: '#7FC97F'}  # '#d5e5d5' '#d62c2c'
    ap.gridplot(attr_grid, ax=ax, color_dict=color_dict, convert=True)


fig, ax = plt.subplots()
model = IntersectionModel(parameters)
animation = ap.animate(model, fig, ax, animation_plot)
IPython.display.HTML(animation.to_jshtml(fps=30))
