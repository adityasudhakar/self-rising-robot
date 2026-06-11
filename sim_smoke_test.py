from stable_baselines3 import PPO

from robo1_env import Robo1GetupEnv


def main():
    env = Robo1GetupEnv("robo1.xml")
    model = PPO.load("robo1_getup_ppo")

    obs, info = env.reset(options={"pose": "roll_pos"})
    print("initial_pose", info["pose"])

    for _ in range(20):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)

    print("upright", round(info["upright"], 3))
    print("target", [round(float(x), 3) for x in info["target"]])
    print("done", terminated, truncated)


if __name__ == "__main__":
    main()
