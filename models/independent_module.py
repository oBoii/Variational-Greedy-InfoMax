from typing import List
from torch import Tensor
import torch
import torch.nn as nn

from configs.config_classes import OptionsConfig
# https://github.com/AntixK/PyTorch-VAE/blob/master/models/vanilla_vae.py,
# https://medium.com/dataseries/convolutional-autoencoder-in-pytorch-on-mnist-dataset-d65145c132ac

from models import (
    cnn_encoder,
    loss_InfoNCE,
    autoregressor
)


class IndependentModule(nn.Module):
    def __init__(
            self, opt: OptionsConfig,
            enc_kernel_sizes, enc_strides, enc_padding, nb_channels_cnn, nb_channels_regress, predict_distributions,
            enc_input=1, max_pool_k_size=None, max_pool_stride=None, calc_accuracy=False, prediction_step=12):
        super(IndependentModule, self).__init__()

        self.opt = opt
        self.calc_accuracy = calc_accuracy
        self.nb_channels_cnn = nb_channels_cnn
        self.nb_channels_regressor = nb_channels_regress
        self.predict_distributions = predict_distributions

        # encoder, out: B x L x C = (22, 55, 512)
        self.encoder = cnn_encoder.CNNEncoder(
            opt=opt,
            inp_nb_channels=enc_input,
            out_nb_channels=nb_channels_cnn,
            kernel_sizes=enc_kernel_sizes,
            strides=enc_strides,
            padding=enc_padding,
            max_pool_k_size=max_pool_k_size,
            max_pool_stride=max_pool_stride,
        )

        # hidden dim of the encoder is the input dim of the loss
        self.loss = loss_InfoNCE.InfoNCE_Loss(
            opt, hidden_dim=self.nb_channels_cnn, enc_hidden=self.nb_channels_cnn, calc_accuracy=calc_accuracy,
            prediction_step=prediction_step)

    def get_latents(self, x) -> (Tensor, Tensor):
        (c_mu, c_log_var), (z_mu, z_log_var) = self._get_latent_params(x)

        if self.predict_distributions:
            sample = self._reparameterize(c_mu, c_log_var)
        else:
            sample = c_mu

        # return [(mu, log_var), (mu, log_var)]
        return sample, sample

    def _get_latent_params(self, x: Tensor) -> ((Tensor, Tensor), (Tensor, Tensor)):
        """
        Calculate the latent representation of the input (using both the encoder and the autoregressive model)
        :param x: batch with sampled audios (dimensions: B x C x L)
        :return: c - latent representation of the input (either the output of the autoregressor,
                if use_autoregressor=True, or the output of the encoder otherwise)
                z - latent representation generated by the encoder (or x if self.use_encoder=False)
                both of dimensions: B x L x C
        """
        # encoder in and out: B x C x L, permute to be  B x L x C
        mu, log_var = self.encoder(x)  # (b, 512, 55), (b, 512, 55)

        mu = mu.permute(0, 2, 1)  # (b, 55, 512)
        log_var = log_var.permute(0, 2, 1)

        return (mu, log_var), (mu, log_var)

    def _reparameterize(self, mu: Tensor, logvar: Tensor) -> Tensor:
        """
        Reparameterization trick to sample from N(mu, var) from
        N(0,1).
        :param mu: (Tensor) Mean of the latent Gaussian [B x D]
        :param logvar: (Tensor) Standard deviation of the latent Gaussian [B x D]
        :return: (Tensor) [B x D]
        """
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return eps * std + mu

    def forward(self, x):
        """
        combines all the operations necessary for calculating the loss and accuracy of the network given the input
        :param x: batch with sampled audios (dimensions: B x C x L)
        :return: total_loss - average loss over all samples, timesteps and prediction steps in the batch
                accuracies - average accuracies over all samples, timesteps and predictions steps in the batch
                c - latent representation of the input (either the output of the autoregressor,
                if use_autoregressor=True, or the output of the encoder otherwise)
        """

        # B x L x C = Batch size x #channels x length
        (c_mu, c_log_var), (z_mu, z_log_var) = self._get_latent_params(x)  # B x L x C

        if self.predict_distributions:
            c = self._reparameterize(c_mu, c_log_var)  # (B, L, 512)
            z = self._reparameterize(z_mu, z_log_var)

            log_var = c_log_var
            mu = c_mu

            # KL-divergence loss
            kld_loss = torch.mean(-0.5 * torch.sum(1 + log_var - mu ** 2 - log_var.exp(), dim=1), dim=0)
            kld_loss = kld_loss.mean()  # shape: (1)

            # reconstruction loss
            total_loss, accuracies = self.loss.get_loss(z, c)

            kld_weight = self.opt.encoder_config.kld_weight

            # Combine the losses
            total_loss = total_loss + kld_weight * kld_loss

        else:
            # consider the mean of the distribution as the latent representation, we ignore the variance
            c = c_mu
            z = z_mu

            total_loss, accuracies = self.loss.get_loss(z, c)

        # for multi-GPU training
        total_loss = total_loss.unsqueeze(0)
        accuracies = accuracies.unsqueeze(0)

        return total_loss, accuracies, z
