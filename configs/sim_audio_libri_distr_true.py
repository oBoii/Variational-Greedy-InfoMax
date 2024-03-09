import os

import torch
from config_code.config_classes import OptionsConfig, Dataset
from config_code.sim_setup import SIMSetup


def _get_options(experiment_name) -> OptionsConfig:
    config_file = os.path.basename(__file__)
    sim_setup = SIMSetup(predict_distributions=True, dataset=Dataset.LIBRISPEECH, config_file=config_file)
    options = sim_setup.get_options(experiment_name)

    return options


if __name__ == '__main__':
    print(f"Cuda is available: {torch.cuda.is_available()}")
