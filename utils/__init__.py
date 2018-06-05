import os
import random
import numpy
import torch

def storage_dir():
    if "torch_rl_storage_dir" in os.environ:
        return os.environ["torch_rl_storage_dir"]
    return "storage"

def create_folders_if_necessary(path):
    dirname = os.path.dirname(path)
    if not(os.path.isdir(dirname)):
        os.makedirs(dirname)

def seed(seed):
    random.seed(seed)
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

from utils.agent import Agent
from utils.env import make_env, make_envs
from utils.format import ObssPreprocessor, reshape_reward
from utils.graph import make_envs_graph, get_graph_env_ids
from utils.log import get_log_dir, synthesize, get_logger
from utils.model import get_model_dir, get_model_path, create_model, load_model, save_model