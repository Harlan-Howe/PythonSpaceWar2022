import math
import random
import time

angular_velocity = 1.5 * math.pi
acceleration = 30
max_v = 60
max_v_squared = max_v **2

class PlayerShip:

    def __init__(self, id:int, name:str):
        self.x = random.randrange(800)
        self.y = random.randrange(800)
        self.vx = 0
        self.vy = 0
        self.bearing = random.random() * 2 * math.pi - math.pi
        self.controls = 0
        self.my_id = id
        self.health = 100
        self.name = name
        self.last_shot_taken = time.time()

    def update(self, delta_t: float) -> None:
        self.x += self.vx * delta_t
        self.y += self.vy * delta_t
        self.x = (self.x + 800) % 800
        self.y = (self.y + 800) % 800

        angular_thrust = ((self.controls & 2)/2 - (self.controls & 1))
        self.bearing += angular_velocity * delta_t * angular_thrust
        # self.bearing = (self.bearing + 3 * math.pi) % (2*math.pi) - math.pi

        thrust = ((self.controls & 8) / 8 - (self.controls & 4) / 4) * acceleration
        self.vx += thrust * math.cos(self.bearing) * delta_t
        self.vy += thrust * math.sin(self.bearing) * delta_t
        speed_squared = self.vx ** 2 + self.vy ** 2
        if speed_squared > max_v_squared:
            speed = math.sqrt(speed_squared)
            factor = max_v/speed
            self.vx *= factor
            self.vy *= factor

    def ok_to_fire(self) -> bool:
        now = time.time()
        if now - self.last_shot_taken > 0.25:
            self.last_shot_taken = now
            return True
        return False

    def __repr__(self):
        return f"id: {self.my_id}\tcontrols{format(self.controls,'#010b')}"

    def public_info(self):
        thrusting = min(self.controls & 12, 1)
        return f"PLAYER\t{self.my_id}\t{self.x}\t{self.y}\t{self.bearing}\t{thrusting}\t{self.health}\t{self.name}"
