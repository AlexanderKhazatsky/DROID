---
layout: default
title: Dataset Schema
nav_order: 5
---

# Dataset Schema

| Field | Datatype |
| --------- | -------- |
| steps | `Dataset` |
| steps/action | `Tensor(shape=(6,), dtype=float64)` |
| steps/action_dict | `FeaturesDict` |
|steps/action_dict/cartesian_position| `Tensor(shape=(6,), dtype=float64)` |
|steps/action_dict/cartesian_velocity| `Tensor(shape=(6,), dtype=float64)` |
|steps/action_dict/gripper_position| `Tensor(shape=(1,), dtype=float64)` |
|steps/action_dict/gripper_velocity| `Tensor(shape=(1,), dtype=float64)` |
|steps/action_dict/joint_position| `Tensor(shape=(7,), dtype=float64)` |
|steps/action_dict/joint_velocity| `Tensor(shape=(7,), dtype=float64)` |
|steps/discount| `Scalar(shape=(), dtype=float32)` |
|steps/is_first| `Scalar(shape=(), dtype=bool)` |
|steps/is_last| `Scalar(shape=(), dtype=bool)` |
|steps/is_terminal| `Scalar(shape=(), dtype=bool)` |
|steps/language_embedding| `Tensor(shape=(512,), dtype=float32)` |
|steps/language_embedding_2| `Tensor(shape=(512,), dtype=float32)` |
|steps/language_embedding_3| `Tensor(shape=(512,), dtype=float32)` |
|steps/language_instruction| `Text(shape=(), dtype=string)` |
|steps/language_instruction_2| `Text(shape=(), dtype=string)` |
|steps/language_instruction_3| `Text(shape=(), dtype=string)` |
|steps/observation| `FeaturesDict` |
|steps/observation/cartesian_position| `Tensor(shape=(6,), dtype=float64)` |
|steps/observation/exterior_image_1_left| `Image(shape=(180, 320, 3), dtype=uint8)` |
|steps/observation/exterior_image_2_left| `Image(shape=(180, 320, 3), dtype=uint8)` |
|steps/observation/gripper_position| `Tensor(shape=(1,), dtype=float64)` |
|steps/observation/joint_position| `Tensor(shape=(7,), dtype=float64)` |
|steps/observation/wrist_image_left| `Image(shape=(180, 320, 3), dtype=uint8)` |
|reward| `Scalar(shape=(), dtype=float32)` |

