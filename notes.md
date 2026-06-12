# Self Rising Robot Notes

Reference repo:
https://github.com/homemadegarbage/SelfRisingRobot

## What It Is

Tiny 2-servo robot that learns a get-up motion in MuJoCo simulation, then runs
the learned controller on a real M5Atom robot.

## How The Repo Works

1. `RL/robo1.xml` defines the physical robot in MuJoCo.
2. `RL/robo1_env.py` wraps the MuJoCo model as a Gymnasium RL environment.
3. A PPO policy is trained to get the robot upright from fallen poses.
4. The trained policy is exported to `Arduino/robo03/policy_network.h`.
5. `Arduino/robo03/robo03.ino` runs the policy on M5Atom and drives two servos.

## Policy Inputs And Outputs

Inputs:

- roll
- pitch
- servo1 target
- servo2 target

Outputs:

- servo1 target delta
- servo2 target delta

So the neural net is not doing vision. It is reading tilt and current servo
targets, then nudging the two servos.

## Hardware Notes

M5Atom is not like a Raspberry Pi. It is much closer to Arduino.

- M5Atom: ESP32 microcontroller board
- Raspberry Pi: Linux computer
- Arduino folder in the repo means Arduino IDE / Arduino-style firmware, not an
  Arduino Uno board

The code uses:

- M5Atom IMU for roll/pitch
- servo 1 on GPIO 26
- servo 2 on GPIO 32
- Wi-Fi access point `robo1`
- browser UI at `http://192.168.42.1`

## M5Atom Choice

Do not use Arduino Uno for this version. Uno lacks built-in Wi-Fi and IMU, has
less CPU/memory, and would need extra modules.

For this repo, prefer M5Stack Atom Matrix over Atom Lite because the code uses
`M5.IMU`.

- Atom Lite: ESP32, Wi-Fi, button, LED, Grove port, but no built-in IMU in the
  docs checked
- Atom Matrix: ESP32 plus built-in MPU6886 IMU

## IMU

IMU means inertial measurement unit.

It usually combines:

- accelerometer: tilt / acceleration
- gyroscope: rotation rate

For this robot, the IMU tells the controller whether the robot is fallen over or
upright.

## Discussion Notes

The public discussion confirms the basic plan:

1. Train with reinforcement learning first.
2. Test the learned behavior in simulation.
3. Export the neural network.
4. Load the neural network onto the microcontroller.
5. Run the real robot offline.

Offline means the robot does not call a cloud API while moving. The learned
policy is stored locally in `policy_network.h` and executed directly on the
M5Atom.

Mentioned future infrastructure:

- PufferLib RL
- MuJoCo baseline
- NVIDIA Warp

Those are about making RL training faster. They do not change the first build
plan.

## Local Simulation Status

Reference repo cloned locally:

`reference/SelfRisingRobot`

Local Python environment:

`.venv`

Installed packages from:

`reference/SelfRisingRobot/RL/requirements.txt`

Smoke test:

`sim_smoke_test.py`

Result:

- MuJoCo model loads
- trained PPO model loads
- environment resets from `roll_pos`
- policy steps the sim without crashing
- after 20 steps: upright score around `0.685`

Run from the RL folder:

```bash
../../.venv/bin/python ../../sim_smoke_test.py
```

## Quick PPO Training Run

Script:

`train_quick_ppo.py`

Run from the reference RL folder:

```bash
../../../.venv/bin/python train_quick_ppo.py
```

Training setup:

- algorithm: PPO
- policy: MLP
- timesteps: `20,000`
- device: CPU
- output: `robo1_getup_ppo_quick.zip`

Result:

- training completed in under a minute on this machine
- reward started very negative and improved during training
- this is a weak/quick policy, not a fully solved policy

Evaluation after training:

- `roll_pos`: best upright `0.900`, final upright `0.871`
- `roll_neg`: best upright `0.753`, final upright `0.700`
- `pitch_pos`: best upright `0.497`, final upright `0.358`
- `pitch_neg`: best upright `-0.157`, final upright `-0.370`

Interpretation:

The quick policy learned some useful motion for roll-based falls, but did not
learn a reliable full get-up behavior across all poses.

View the quick policy from the reference RL folder:

```bash
../../../.venv/bin/mjpython play_quick_policy.py --pose roll_pos
```
