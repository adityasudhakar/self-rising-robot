from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback

from robo1_env import Robo1GetupEnv


class RewardPrinter(BaseCallback):
    def __init__(self, every_episodes=25):
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
                    flush=True,
                )
            self.current_reward = 0.0
        return True


def main():
    total_timesteps = 1_000_000
    output = Path("robo1_getup_ppo_large")
    checkpoint_dir = Path("checkpoints_large")
    checkpoint_dir.mkdir(exist_ok=True)

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

    checkpoint = CheckpointCallback(
        save_freq=100_000,
        save_path=str(checkpoint_dir),
        name_prefix="robo1_getup_large",
    )

    model.learn(
        total_timesteps=total_timesteps,
        callback=[RewardPrinter(), checkpoint],
    )
    model.save(output)
    print("saved", output.with_suffix(".zip"), flush=True)


if __name__ == "__main__":
    main()
