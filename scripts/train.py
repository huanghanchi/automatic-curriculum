import argparse
import time
import datetime
import torch
import torch_rl
import tensorboardX

import envs
import utils

# Parse arguments

parser = argparse.ArgumentParser()
parser.add_argument("--env", default="SEnv_D4LuIuBu",
                    help="name of the environment to train on (default: SEnv_D4LuIuBu)")
parser.add_argument("--model", default=None,
                    help="name of the model (default: ENV_ALGO_TIME)")
parser.add_argument("--seed", type=int, default=1,
                    help="random seed (default: 1)")
parser.add_argument("--procs", type=int, default=16,
                    help="number of processes (default: 16)")
parser.add_argument("--frames", type=int, default=10**7,
                    help="number of frames of training (default: 10e7)")
parser.add_argument("--log-interval", type=int, default=1,
                    help="number of updates between two logs (default: 1)")
parser.add_argument("--save-interval", type=int, default=0,
                    help="number of updates between two saves (default: 0, 0 means no saving)")
parser.add_argument("--frames-per-proc", type=int, default=128,
                    help="number of frames per process before update (default: 128)")
parser.add_argument("--discount", type=float, default=0.99,
                    help="discount factor (default: 0.99)")
parser.add_argument("--lr", type=float, default=7e-4,
                    help="learning rate (default: 7e-4)")
parser.add_argument("--gae-tau", type=float, default=0.95,
                    help="tau coefficient in GAE formula (default: 0.95, 1 means no gae)")
parser.add_argument("--entropy-coef", type=float, default=0.01,
                    help="entropy term coefficient (default: 0.01)")
parser.add_argument("--value-loss-coef", type=float, default=0.5,
                    help="value loss term coefficient (default: 0.5)")
parser.add_argument("--max-grad-norm", type=float, default=0.5,
                    help="maximum norm of gradient (default: 0.5)")
parser.add_argument("--recurrence", type=int, default=1,
                    help="number of timesteps gradient is backpropagated (default: 1)")
parser.add_argument("--optim-eps", type=float, default=1e-5,
                    help="Adam and RMSprop optimizer epsilon (default: 1e-5)")
parser.add_argument("--optim-alpha", type=float, default=0.99,
                    help="RMSprop optimizer apha (default: 0.99)")
parser.add_argument("--clip-eps", type=float, default=0.2,
                    help="clipping epsilon (default: 0.2)")
parser.add_argument("--epochs", type=int, default=4,
                    help="number of epochs (default: 4)")
parser.add_argument("--batch-size", type=int, default=256,
                    help="batch size (default: 256)")
args = parser.parse_args()

# Set seed for all randomness sources

utils.seed(args.seed)

# Generate environments

envs = envs.get_envs(args.env, args.seed, args.procs)

# Define model name

suffix = datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
default_model_name = "{}_seed{}_{}".format(args.env, args.seed, suffix)
model_name = args.model or default_model_name

# Define obss preprocessor

obss_preprocessor = utils.ObssPreprocessor(model_name, envs[0].observation_space)

# Define actor-critic model

print(envs[0].action_space)
acmodel = utils.load_model(obss_preprocessor.obs_space, envs[0].action_space, model_name)
if torch.cuda.is_available():
    acmodel.cuda()

# Define actor-critic algo

algo = torch_rl.PPOAlgo(envs, acmodel, args.frames_per_proc, args.discount, args.lr, args.gae_tau,
                        args.entropy_coef, args.value_loss_coef, args.max_grad_norm, args.recurrence,
                        args.optim_eps, args.clip_eps, args.epochs, args.batch_size, obss_preprocessor,
                        utils.reshape_reward)

# Define logger and Tensorboard writer

log = utils.Logger(model_name)
writer = tensorboardX.SummaryWriter(utils.get_log_dir(model_name))

# Log command, availability of CUDA and model

log(args, to_print=False)
log("CUDA available: {}".format(torch.cuda.is_available()))
log(acmodel)

# Train model

num_frames = 0
total_start_time = time.time()
i = 0

while num_frames < args.frames:
    # Update parameters

    update_start_time = time.time()
    logs = algo.update_parameters()
    update_end_time = time.time()
    
    num_frames += logs["num_frames"]
    i += 1

    # Print logs

    if i % args.log_interval == 0:
        total_ellapsed_time = int(time.time() - total_start_time)
        fps = logs["num_frames"]/(update_end_time - update_start_time)
        duration = datetime.timedelta(seconds=total_ellapsed_time)
        return_per_episode = utils.synthesize(logs["return_per_episode"])
        rreturn_per_episode = utils.synthesize(logs["reshaped_return_per_episode"])
        num_frames_per_episode = utils.synthesize(logs["num_frames_per_episode"])

        log(
            "U {} | F {:06} | FPS {:04.0f} | D {} | rR:x̄σmM {: .2f} {: .2f} {: .2f} {: .2f} | F:x̄σmM {:.1f} {:.1f} {} {} | H {:.3f} | V {:.3f} | pL {: .3f} | vL {:.3f}"
            .format(i, num_frames, fps, duration,
                    *rreturn_per_episode.values(),
                    *num_frames_per_episode.values(),
                    logs["entropy"], logs["value"], logs["policy_loss"], logs["value_loss"]))
        writer.add_scalar("frames", num_frames, i)
        writer.add_scalar("FPS", fps, i)
        writer.add_scalar("duration", total_ellapsed_time, i)
        for key, value in return_per_episode.items():
            writer.add_scalar("return_" + key, value, i)
        for key, value in rreturn_per_episode.items():
            writer.add_scalar("rreturn_" + key, value, i)
        for key, value in num_frames_per_episode.items():
            writer.add_scalar("num_frames_" + key, value, i)
        writer.add_scalar("entropy", logs["entropy"], i)
        writer.add_scalar("value", logs["value"], i)
        writer.add_scalar("policy_loss", logs["policy_loss"], i)
        writer.add_scalar("value_loss", logs["value_loss"], i)

    # Save obss preprocessor vocabulary and model

    if args.save_interval > 0 and i % args.save_interval == 0:
        obss_preprocessor.vocab.save()

        if torch.cuda.is_available():
            acmodel.cpu()
        utils.save_model(acmodel, model_name)
        if torch.cuda.is_available():
            acmodel.cuda()