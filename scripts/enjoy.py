import argparse
import time

import envs
import utils

# Parse arguments

parser = argparse.ArgumentParser()
parser.add_argument("--env", default="SEnv_D4LuIuBu",
                    help="name of the environment to be run (default: SEnv_D4LuIuBu)")
parser.add_argument("--model", required=True,
                    help="name of the trained model (REQUIRED)")
parser.add_argument("--seed", type=int, default=0,
                    help="random seed (default: 0)")
parser.add_argument("--deterministic", action="store_true", default=False,
                    help="action with highest probability is selected")
parser.add_argument("--pause", type=float, default=0.1,
                    help="pause duration between two consequent actions of the agent")
args = parser.parse_args()

# Set seed for all randomness sources

utils.seed(args.seed)

# Generate environment

env = envs.get_env(args.env, args.seed)

# Define agent

agent = utils.Agent(args.model, env.observation_space, env.action_space, args.deterministic)

# Run the agent

done = True

while True:
    if done:
        obs = env.reset()
        print("Instr:", obs["mission"])

    time.sleep(args.pause)
    renderer = env.render("human")

    action = agent.get_action(obs)
    obs, reward, done, _ = env.step(action)
    agent.analyze_feedback(reward, done)

    if renderer.window is None:
        break