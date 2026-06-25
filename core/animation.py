"""Frame/state animation driver. Advances frames on the fixed timestep."""


class Animator:
    def __init__(self, animations):
        # animations: name -> {"left":[surf...], "right":[surf...], "fps":int,
        #                      "loop":bool, "frames":int}
        self.animations = animations
        self.name = None
        self.frame = 0
        self.elapsed = 0.0
        self.finished = False

    def play(self, name, restart=False):
        if name not in self.animations:
            raise KeyError(name)
        if name == self.name and not restart:
            return
        self.name = name
        self.frame = 0
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt):
        if self.name is None:
            return
        a = self.animations[self.name]
        frame_time = 1.0 / a["fps"]
        n = a["frames"]
        loop = a["loop"]
        self.elapsed += dt
        while self.elapsed >= frame_time:
            self.elapsed -= frame_time
            if loop:
                self.frame = (self.frame + 1) % n
            elif self.frame < n - 1:
                self.frame += 1
            else:
                self.finished = True
                break

    def image(self, facing):
        a = self.animations[self.name]
        frames = a[facing]
        return frames[min(self.frame, len(frames) - 1)]
