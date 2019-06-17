import random
import os
import numpy
import torch
import collections


def get_storage_dir():
    if "SOPH_CURRI_STORAGE" in os.environ:
        return os.environ["SOPH_CURRI_STORAGE"]
    return "storage"


def get_model_dir(model_name):
    return os.path.join(get_storage_dir(), "models", model_name, "")


def get_csv_config_path():
    return os.path.join(get_storage_dir(), "config.csv")


def get_stats_dir():
    return os.path.join(get_storage_dir(), "stats", "")


def create_folders_if_necessary(path):
    dirname = os.path.dirname(path)
    if not os.path.isdir(dirname):
        os.makedirs(dirname)


def seed(seed):
    random.seed(seed)
    numpy.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def synthesize(array):
    d = collections.OrderedDict()
    d["mean"] = numpy.mean(array)
    d["std"] = numpy.std(array)
    d["min"] = numpy.amin(array)
    d["max"] = numpy.amax(array)
    return d
