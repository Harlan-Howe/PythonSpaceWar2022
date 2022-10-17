import math
import random


angular_velocity = 2 * math.pi
acceleration = 30
max_v = 30
max_v_squared = max_v **2

class PlayerShip:

    def __init__(self, id:int):
        self.x = random.randrange(800)
        self.y = random.randrange(800)
        self.vx = 0
        self.vy = 0
        self.bearing = random.random() * 2 * math.pi - math.pi
        self.controls = 0
        self.my_id = id

    def update(self, delta_t:float) -> None:
        self.x += self.vx * delta_t
        self.y += self.vy * delta_t
        self.x = (self.x + 800) % 800
        self.y = (self.y + 800) % 800

        self.bearing += angular_velocity * delta_t
        self.bearing = (self.bearing + 1.5 * math.pi) % (2*math.pi) - math.pi

        thrust = ((self.controls & 8) / 8 - (self.controls & 4) / 4) * acceleration
        self.vx += thrust * math.cos(self.bearing) * delta_t
        self.vy += thrust * math.sin(self.bearing) * delta_t
        speed_squared = self.vx ** 2 + self.vy ** 2
        if speed_squared > max_v_squared:
            speed = math.sqrt(speed_squared)
            factor = max_v/speed
            self.vx *= factor
            self.vy *= factor

