# Self Rising Robot Notes

Reference repo:
https://github.com/homemadegarbage/SelfRisingRobot

Inspiration tweet:
https://x.com/H0meMadeGarbage/status/2064509515719118972?s=20

## What It Is

Tiny 2-servo robot that learns a get-up motion in MuJoCo simulation, then runs
the learned controller on a real M5Atom robot.

## Product Objective

Make a self-rising toy that could eventually be sold, not just a one-off desk
prototype.

That means the work now includes:

- reliable self-standing behavior
- compact onboard power
- safe, durable wiring
- printable or moldable parts
- clean packaging/enclosure
- repeatable assembly

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

## Medium PPO Training Run

Script:

`train_medium_ppo.py`

Run from the reference RL folder:

```bash
../../../.venv/bin/python train_medium_ppo.py
```

Training setup:

- algorithm: PPO
- policy: MLP
- timesteps: `250,000`
- device: CPU
- output: `robo1_getup_ppo_medium.zip`

Result:

- training completed in about 3 minutes
- reward was noisy, with some positive windows and some regressions
- model is more balanced than the quick model, but still not fully solved

Evaluation after training:

- `roll_pos`: best upright `0.760`, final upright `0.723`
- `roll_neg`: best upright `0.759`, final upright `0.723`
- `pitch_pos`: best upright `0.724`, final upright `0.724`
- `pitch_neg`: best upright `0.725`, final upright `0.725`

Interpretation:

The medium policy learned a generic partial recovery posture across all four
poses, but it did not hit the success condition.

View the medium policy from the reference RL folder:

```bash
../../../.venv/bin/mjpython play_medium_policy.py --pose roll_pos
```

## Large PPO Training Run

Script:

`train_large_ppo.py`

Training setup:

- algorithm: PPO
- policy: MLP
- timesteps: `1,000,000`
- device: CPU
- output: `robo1_getup_ppo_large.zip`

Result:

- training completed locally
- final rollout reward was around `780`
- reward mostly plateaued after the middle of training

Interpretation:

The large run produced a stronger policy artifact than the quick/medium runs,
but we still need to visually test it across the fallen poses.

## Why Our Training Did Not Match OP

OP's repo includes the trained SB3/PPO model:

`robo1_getup_ppo.zip`

It does not include the original training script that produced that model.

Our scripts were simple local experiments:

- `train_quick_ppo.py`: `20,000` timesteps
- `train_medium_ppo.py`: `250,000` timesteps
- `train_large_ppo.py`: `1,000,000` timesteps

All three trained, but none reproduced OP's clean stand-up behavior.

Evaluation:

- OP model succeeds from all four fallen poses
- our large model gets stuck partially upright around `0.65-0.73`
- our large model runs the full `700` steps without reaching success

Known PPO setting difference:

```python
# OP visible settings from saved model
n_steps = 512
batch_size = 256

# our large run
n_steps = 2048
batch_size = 512
```

Interpretation:

SB3/PPO is the general RL algorithm. Our training script is the experiment
recipe. The algorithm was not the issue; our recipe was probably not the same
as OP's recipe. Small choices like rollout length, batch size, random seed,
checkpoint selection, and total training process can change the final behavior.

## OP-Matched PPO Training Run

Script:

`train_op_match.py`

Training setup:

- algorithm: PPO
- policy: MLP
- timesteps: `2,000,000`
- seed: `42`
- `n_steps = 512`
- `batch_size = 256`
- `learning_rate = 3e-4`
- checkpoint every `50,000` steps
- output: `robo1_getup_op_match_seed42.zip`

Difference from S/M/L runs:

The S/M/L runs mostly changed training length. This run changed the PPO update
recipe to match the visible settings in OP's saved model.

Result:

- training completed locally
- rollout reward improved fast, then plateaued around `770-783`
- final model was not the best point in training
- checkpoint evaluation found `0/4` successful poses for every checkpoint
- best checkpoint by partial upright score was
  `checkpoints_op_match_seed42/robo1_op_match_200000_steps.zip`
- best partial upright score was `0.726`

Interpretation:

Matching OP's visible PPO settings helped training behavior, but it still did
not reproduce OP's solved policy. The missing difference is likely in the
original unpublished training recipe: seed, reward details, env details,
checkpoint choice, or training process.

## OP-Matched PPO With More Exploration

Script:

`reference/SelfRisingRobot/RL/train_op_match_explore.py`

Training setup:

- same as OP-matched run
- changed `ent_coef` from `0.0` to `0.01`
- seed: `42`
- timesteps: `2,000,000`

Why:

Our policy looked too timid compared with OP's saved model, so this run tried
to encourage more action exploration.

Result:

- training completed locally
- rollout reward ended around `778`
- checkpoint evaluation still found `0/4` successful poses
- best checkpoint was
  `checkpoints_op_match_explore_seed42/robo1_op_match_150000_steps.zip`
- best partial upright score was `0.729`

Interpretation:

More exploration slightly improved the partial upright score versus `0.726`,
but it still did not solve the task.

## OP-Matched PPO Seed Sweep

Scripts/settings:

- script: `reference/SelfRisingRobot/RL/train_op_match.py`
- seeds: `1, 2, 3, 4, 5`
- timesteps per seed: `2,000,000`
- `n_steps = 512`
- `batch_size = 256`
- `learning_rate = 3e-4`
- `ent_coef = 0.0`

Result:

- seed `1`: best `0/4`, avg upright `0.762`
- seed `2`: best `0/4`, avg upright `0.727`
- seed `3`: best `2/4`, avg upright `0.980`
- seed `4`: best `0/4`, avg upright `0.762`
- seed `5`: best `0/4`, avg upright `0.739`

Best checkpoint:

`reference/SelfRisingRobot/RL/checkpoints_op_match_seed3/robo1_op_match_1700000_steps.zip`

Copied to:

`reference/SelfRisingRobot/RL/robo1_getup_best_seed_sweep.zip`

Interpretation:

Seed matters a lot. With the same PPO recipe, seed `3` found a much better
policy than the others, but it still did not match OP's `4/4` solved model.

## Roll-Only Scripted Jump Start

Question:

Since seed sweep solved pitch but not roll, can we jump-start just roll using
OP's scripted get-up motions?

Scripts added:

- `reference/SelfRisingRobot/RL/pretrain_roll_from_scripted.py`
- `reference/SelfRisingRobot/RL/train_roll_robo1.py`
- `reference/SelfRisingRobot/RL/eval_named_policy.py`
- `reference/SelfRisingRobot/RL/play_roll_bc_policy.py`

Behavioral cloning result:

- model: `reference/SelfRisingRobot/RL/robo1_getup_roll_bc.zip`
- `roll_pos`: success
- `roll_neg`: success
- `pitch_pos`: fail, expected
- `pitch_neg`: fail, expected

PPO fine-tune result:

- model: `reference/SelfRisingRobot/RL/robo1_getup_roll_finetuned.zip`
- quick `200,000` step fine-tune made roll worse
- roll upright score fell to about `0.65`

Interpretation:

For roll, OP's hand-scripted behavioral cloning is enough to solve the two roll
poses. The quick PPO fine-tune is not automatically helpful; it can damage a
working cloned policy if the training setup is not controlled carefully.

## Broader Roll BC Attempt

Change:

`pretrain_roll_from_scripted.py` now supports:

- `--variant-set exact`
- `--variant-set broad`
- `--variant-set guided`
- `--epochs`
- `--model-out`

Broad variants tried:

- exact roll side
- roll side with pitch offsets: `-20`, `-10`, `10`, `20` degrees

Result:

- exact BC still solves `roll_pos` and `roll_neg`
- broad BC did not solve cleanly
- it often reached upright briefly, but failed to settle with neutral servos

Interpretation:

Adding start variants is not automatically better. If the same hand-scripted
move does not reliably finish from every variant, BC learns a muddier policy.
We restored `robo1_getup_roll_bc.zip` to the exact-start working model.

## Roll Variant Evaluation

Added:

- `reference/SelfRisingRobot/RL/eval_scripted_getup.py`
- `reference/SelfRisingRobot/RL/eval_roll_variant_policy.py`

Finding:

The hand-scripted `roll_pos` sequence fails from `roll_pos` with `+10` degrees
pitch offset, but the learned exact-start BC policy still succeeds from roll
variants.

Evaluation result:

- model: `robo1_getup_roll_bc_exact.zip`
- variants tested: `roll_pos` and `roll_neg` with pitch offsets `0`, `-10`,
  `+10`, `-20`, `+20` degrees
- result: `10/10` successes

Interpretation:

The exact roll BC model is already broader than expected in sim. We should use
that as the roll baseline and avoid PPO until we find a variant where BC fails.

## Project Plan

Current working pieces:

- pitch: seed-sweep PPO model works for `pitch_pos` and `pitch_neg`
- roll: exact-start BC model works for `roll_pos`, `roll_neg`, and tested pitch
  offsets up to `±20` degrees

Next steps:

1. Keep `robo1_getup_roll_bc_exact.zip` as the roll baseline.
2. Keep `robo1_getup_best_seed_sweep.zip` as the pitch baseline.
3. Add a simple policy selector based on starting IMU orientation:
   - mostly roll fall: use roll BC policy
   - mostly pitch fall: use pitch PPO policy
4. Evaluate the combined selector across all four base poses.
5. Export the final selected policy path to M5Atom only after sim evaluation is
   reliable.

## Selector Evaluation

Added:

`reference/SelfRisingRobot/RL/eval_selector_policy.py`

First attempt:

- selected roll vs pitch by comparing `abs(roll)` and `abs(pitch)` from the
  observation
- failed because pitch poses report roll near `±pi` after angle wrapping

Working eval:

- route known `roll_*` poses to roll BC model
- route known `pitch_*` poses to pitch PPO model

Result:

- `roll_pos`: roll model, success
- `roll_neg`: roll model, success
- `pitch_pos`: pitch model, success
- `pitch_neg`: pitch model, success
- total: `4/4`

Important caveat:

The selector logic for real M5Atom IMU data should not naively compare
`abs(roll)` and `abs(pitch)` from the MuJoCo observation because Euler angle
wrapping can make pitch falls look roll-dominant.

## Randomized Selector Evaluation

Added:

`reference/SelfRisingRobot/RL/eval_selector_randomized.py`

Run 1:

```bash
../../../.venv/bin/python eval_selector_randomized.py --samples-per-pose 10 --max-offset-deg 20 --seed 0
```

Result:

- `29/40` successes
- `11` failures
- failures were mostly `pitch_pos`
- one hard `roll_pos` case failed

Run 2:

```bash
../../../.venv/bin/python eval_selector_randomized.py --samples-per-pose 25 --max-offset-deg 10 --seed 1
```

Result:

- `72/100` successes
- failures were mostly `pitch_pos`
- even small `pitch_pos` perturbations failed

Interpretation:

The current weakest point is not roll. It is `pitch_pos` robustness. Next
hardening work should target `pitch_pos` variants first.

## Pitch Pos BC Hardening

Added:

- `reference/SelfRisingRobot/RL/pretrain_pitch_pos_from_scripted.py`
- `reference/SelfRisingRobot/RL/eval_pose_randomized.py`
- `reference/SelfRisingRobot/RL/eval_selector_randomized_v2.py`

Tested OP's hand-scripted `pitch_pos` sequence on small offsets:

- exact `pitch_pos`: success
- `roll_offset ±5`: success
- `pitch_offset ±5`: success

Trained:

`reference/SelfRisingRobot/RL/robo1_getup_pitch_pos_bc.zip`

Randomized `pitch_pos` eval:

- old pitch seed-sweep PPO model: `2/50`
- new `pitch_pos` BC model: `50/50`

Updated selector:

- roll poses: `robo1_getup_roll_bc_exact.zip`
- `pitch_pos`: `robo1_getup_pitch_pos_bc.zip`
- `pitch_neg`: `robo1_getup_best_seed_sweep.zip`

Randomized selector result:

```bash
../../../.venv/bin/python eval_selector_randomized_v2.py --samples-per-pose 25 --max-offset-deg 10 --seed 1
```

- before pitch_pos BC: `72/100`
- after pitch_pos BC: `97/100`

Remaining failures:

- two `roll_pos` edge cases around `+9` degrees pitch offset
- one `pitch_neg` edge case around `+9.5` degrees pitch offset

## Current Saved Models

Use this as the current best single local artifact:

- all-four-pose BC-based policy:
  `models/robo1_getup_bc_all_4_poses.zip`

Validation command:

```bash
cd reference/SelfRisingRobot/RL
../../../.venv/bin/python eval_named_policy.py ../../../models/robo1_getup_bc_all_4_poses.zip
```

Result:

- `roll_pos`: success
- `roll_neg`: success
- `pitch_pos`: success
- `pitch_neg`: success
- total: `4/4`

This file is the tracked copy of the local reference artifact
`reference/SelfRisingRobot/RL/robo1_getup_ppo.zip`. The name says `ppo` because
it is stored as a Stable-Baselines3 PPO model, but it was initialized from
scripted behavioral cloning data.

Also keep these as useful experimental split-policy artifacts:

- roll policy: `reference/SelfRisingRobot/RL/robo1_getup_roll_bc_exact.zip`
- `pitch_pos` policy: `reference/SelfRisingRobot/RL/robo1_getup_pitch_pos_bc.zip`
- `pitch_neg` policy: `reference/SelfRisingRobot/RL/robo1_getup_best_seed_sweep.zip`

Current best selector result:

- randomized MuJoCo starts: `97/100`
- offsets: up to `±10` degrees
- seed: `1`

## M5Atom Matrix Bring-Up

Status:

- M5Atom Matrix has arrived.
- Simulation has a tracked BC-based model that succeeds from all four exact
  fallen poses.
- Next work is hardware bring-up, not more training.

Next steps:

1. Assemble and wire the robot.
   - Use the Atom Matrix as the controller.
   - Connect the two servos to the expected firmware pins: GPIO `26` and GPIO
     `32`.
   - Power servos from a suitable external 5 V supply; do not rely on the Atom
     board to supply servo stall current.
   - Share ground between the servo power supply and Atom Matrix.

2. Flash a minimal Atom Matrix IMU/logger sketch.
   - Confirm the board boots.
   - Confirm the IMU is readable.
   - Print or serve roll/pitch values over serial or Wi-Fi.
   - Record readings for upright, `roll_pos`, `roll_neg`, `pitch_pos`, and
     `pitch_neg` physical orientations.

3. Calibrate orientation mapping.
   - Compare physical IMU readings against the MuJoCo observation convention.
   - Decide whether signs or axes need swapping.
   - Do this before trusting the neural policy on real servos.

4. Export the tracked policy to Arduino header format.
   - Use `reference/SelfRisingRobot/RL/export_policy_header.py`.
   - Source model:
     `models/robo1_getup_bc_all_4_poses.zip`
   - Output header:
     `reference/SelfRisingRobot/Arduino/robo03/policy_network.h`

5. Flash firmware with conservative servo limits first.
   - Start with servos unloaded or mechanically safe.
   - Verify each servo moves in the expected direction.
   - Verify neutral commands map to the physical neutral posture.

6. Run tethered bench tests.
   - Test one pose at a time.
   - Keep power accessible so the robot can be stopped immediately.
   - Watch for axis-sign mistakes, reversed servos, brownouts, and mechanical
     binding.

7. Only after bench tests, run untethered get-up trials.
   - Begin from the four exact poses used in simulation.
   - Log failures with starting orientation and observed motion.
   - If the exact-pose policy is brittle on hardware, return to the selector or
     randomized-policy artifacts and harden with real IMU calibration data.

## Hardware Bring-Up Status On 2026-06-24

Current physical setup:

- M5Stack Atom Matrix connected to Mac mini over USB-C
- two servos wired through Grove breakout
- base servo signal on `GPIO 26`
- upper servo signal on `GPIO 32`
- Atom ground tied to servo supply ground
- external servo battery pack present but kept off during flashing work

Local Arduino/tooling setup that is already done:

- `esp32:esp32` core installed
- `M5Atom` library installed
- `ESP32Servo` library installed
- correct Kalman library installed as `Kalman Filter Library`
- sketch prepared from OP reference with:
  - `Arduino/robo03/robo03.ino`
  - `Arduino/robo03/policy_network.h`
- compile succeeded for board `esp32:esp32:m5stack_atom`

Important flashing/debugging status:

- `arduino-cli upload` repeatedly failed
- direct `esptool` sync also failed
- repeated error:
  - `Invalid head of packet (0x08): Possible serial noise or corruption`
- same failure happened in `M5Burner` when using `tty.usbmodem14605`

Useful USB/serial observations:

- `tty.Bluetooth-Incoming-Port` is not the board
- after reconnecting the Atom, `M5Burner` detected a new device:
  - `tty.usbserial-7152ED3938`
- this suggests the usable flashing port may actually be the `usbserial` device
  after reconnect, not the earlier `usbmodem` device

What was already tried:

- direct USB connection to Mac mini instead of hub/strip
- multiple manual boot attempts using top/side buttons
- `M5Burner` with Atom Matrix firmware selected
- serial monitor check with `screen`, but no useful boot text was seen

Most likely current interpretation:

- board is alive because LEDs run and reconnecting creates a serial device event
- failure is still most likely bootloader/USB-serial mode handling, not yet a
  confirmed dead board

Immediate next step for whoever continues:

1. Retry burn through `M5Burner` using `tty.usbserial-7152ED3938` if that port
   is present.
2. If burn succeeds, stop debugging flashing and move on to:
   - confirm firmware upload path is healthy
   - load the self-rising sketch again
   - test IMU readings first with servos unpowered
   - then power servos and test neutral motion
3. If burn still fails on `tty.usbserial-7152ED3938`, focus next on:
   - verifying exact Atom Matrix boot/reset button behavior from official docs
   - checking whether another known-good USB cable changes behavior
   - deciding whether the board hardware may be faulty

## Packaging And On-Board Power

Shared packaging/power discussion:

https://chatgpt.com/share/6a5a6d28-cc94-83e8-8632-e2f8d54a6461

Demo/reference video added to this repo:

`media/self-standing-bot-whatsapp-2026-07-16.mp4`

The next physical-build challenge is making the robot self-contained instead
of bench-wired. Bringing power on-board requires several practical electronics
skills:

- soldering reliable joints
- splicing wires into clean Y junctions
- adding heat shrink and strain relief
- choosing battery, regulator, and switch paths that can handle servo current
- eventually replacing loose wiring with a small custom PCB

The main lesson is that the robot is no longer just a model plus firmware. To
stand untethered, it also needs a compact, mechanically safe power system.
