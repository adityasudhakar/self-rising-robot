from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from robo1_env import Robo1GetupEnv


class RewardPrinter(BaseCallback):
    def __init__(self, every_episodes=10):
        super().__init__()
        self.every_episodes = every_episodes
        self.episode_rewards = []
        self.current_reward = 0.0

    def _on_step(self):
        self.current_reward += float(self.locals["rewards"][0])
        if self.locals["dones"][0]:
            self.episode_rewards.append(self.current_reward)
            if len(self.episode_rewards) % self.every_episodes == 0:
                recent = self.episode_rewards[-self.every_episodes :]
                print(
                    "episodes",
                    len(self.episode_rewards),
                    "mean_reward",
                    round(sum(recent) / len(recent), 2),
                )
            self.current_reward = 0.0
        return True


def main():
    total_timesteps = 250_000
    output = Path("robo1_getup_ppo_medium")

    env = Robo1GetupEnv("robo1.xml")
    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        device="cpu",
        n_steps=2048,
        batch_size=512,
        learning_rate=3e-4,
    )

    model.learn(total_timesteps=total_timesteps, callback=RewardPrinter())
    model.save(output)
    print("saved", output.with_suffix(".zip"))


if __name__ == "__main__":
    main()
