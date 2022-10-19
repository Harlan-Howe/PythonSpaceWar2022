
class Bullet:

    def __init__(self, x:float, y:float, vx:float, vy:float, owner_id:int, bullet_id:int, lifetime:float):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.owner_id = owner_id
        self.bullet_id = bullet_id
        self.lifetime = lifetime

    def public_info(self) -> str:
        return f"BULLET\t{self.bullet_id}\t{self.x}\t{self.y}\t{self.vx}\t{self.vy}\t{owner_id}"

    def __repr__(self):
        return self.public_info()

    def update(self, delta_t: float) -> None:
        self.x += self.vx * delta_t
        self.y += self.vy * delta_t
        self.x = (self.x + 800) % 800
        self.y = (self.y + 800) % 800
        self.lifetime -= delta_t


