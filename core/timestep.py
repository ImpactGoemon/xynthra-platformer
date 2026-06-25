"""Fixed-timestep accumulator.

Decouples physics/update from render rate so the simulation is deterministic
regardless of how fast a machine renders. This class is pure (no pygame) so it
can be unit-tested without a window.
"""


class FixedTimestep:
    def __init__(self, dt, max_frame_time=0.25):
        if dt <= 0:
            raise ValueError("dt must be positive")
        self.dt = dt
        self.max_frame_time = max_frame_time
        self.accumulator = 0.0
        self.steps_taken = 0

    def advance(self, frame_time):
        """Add elapsed real time; return how many fixed steps to run now."""
        if frame_time < 0:
            frame_time = 0.0
        if frame_time > self.max_frame_time:
            frame_time = self.max_frame_time  # clamp: avoid spiral of death
        self.accumulator += frame_time
        steps = 0
        while self.accumulator >= self.dt:
            self.accumulator -= self.dt
            steps += 1
        self.steps_taken += steps
        return steps

    @property
    def alpha(self):
        """Interpolation factor [0,1) for render blending between fixed steps."""
        return self.accumulator / self.dt
