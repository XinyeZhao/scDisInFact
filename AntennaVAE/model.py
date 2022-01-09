import torch
import torch.nn as nn
import torch.nn.functional as F

import collections
from typing import Iterable, List

from torch.nn.parameter import Parameter

class FC(nn.Module):
    def __init__(self, features = [1000, 500, 500], use_batch_norm = True, dropout_rate = 0.0, negative_slope = 0.0, use_bias = True, act_func='relu'):
        super().__init__()

        self.features = features
        self.fc_layers = []

        # create fc layers according to the layers_dim
        self.fc_layers = nn.Sequential(
            collections.OrderedDict(
                [
                    (
                        "Layer {}".format(i),
                        nn.Sequential(
                            collections.OrderedDict(
                                [
                                    ("linear", nn.Linear(n_in, n_out) if use_bias else nn.Linear(n_in, n_out, bias = False),),
                                    ("batchnorm", nn.BatchNorm1d(n_out, momentum=0.01, eps=0.001) if use_batch_norm else None,),
                                    ("relu", nn.ReLU() if negative_slope <= 0 else nn.LeakyReLU(negative_slope = negative_slope),),
                                    ("dropout", nn.Dropout(p=dropout_rate) if dropout_rate > 0 else None,),
                                ]
                            )
                        ),
                    )
                    for i, (n_in, n_out) in enumerate(zip(self.features[:-1], self.features[1:]))
                ]
            )
        )

    def forward(self, x):
        # loop through all layers
        for layers in self.fc_layers:
            # loop through linear, batchnorm, relu, dropout, etc
            for layer in layers:
                if layer is not None:
                    x = layer(x)
        return x

class FC_PI(FC):
    def __init__(self, features=[1000, 500, 500], use_batch_norm=True, dropout_rate=0, negative_slope=0, use_bias=True, act_func='relu'):
        super().__init__(features=features, use_batch_norm=use_batch_norm, dropout_rate=dropout_rate, negative_slope=negative_slope, use_bias=use_bias, act_func=act_func)

        # create fc layers according to the layers_dim
        self.fc_layers = nn.Sequential(
            collections.OrderedDict(
                [
                    (
                        "Layer {}".format(i),
                        nn.Sequential(
                            collections.OrderedDict(
                                [
                                    ("linear", nn.Linear(n_in, n_out) if use_bias else nn.Linear(n_in, n_out, bias = False),),
                                    ("batchnorm", nn.BatchNorm1d(n_out, momentum=0.01, eps=0.001) if use_batch_norm else None,),
                                    ("sigmoid", nn.Sigmoid(),),
                                    ("dropout", nn.Dropout(p=dropout_rate) if dropout_rate > 0 else None,),
                                ]
                            )
                        ),
                    )
                    for i, (n_in, n_out) in enumerate(zip(self.features[:-1], self.features[1:]))
                ]
            )
        )
    

# Encoder
class Encoder(nn.Module):
    def __init__(self, features = [1024, 256, 32, 8], dropout_rate = 0.1, negative_slope = 0.2):
        super(Encoder,self).__init__()
        
        self.features = features
        if len(features) > 2:
            self.fc = FC(
                features = features[:-1],
                dropout_rate = dropout_rate,
                negative_slope = negative_slope,
                use_bias = True
            )
        self.output = nn.Linear(features[-2], features[-1])

    def forward(self, x):
        if len(self.features) > 2:
            x = self.fc(x)
        x = self.output(x)
        return x


# Decoder
class Decoder(nn.Module):
    def __init__(self, features = [8, 32, 256, 1024], dropout_rate = 0.0, negative_slope = 0.2):
        super(Decoder, self).__init__()
        self.fc = FC(
            features = features,
            dropout_rate = dropout_rate,
            negative_slope = negative_slope,
            use_bias = True
        )



    def forward(self, z):
        # The decoder returns values for the parameters of the ZINB distribution
        x_mean = self.fc(z)
        return x_mean


class gene_act(nn.Module):
    def __init__(self, features = [1000, 500, 500], use_batch_norm = True, dropout_rate = 0.0, negative_slope = 0.0):
        super(gene_act, self).__init__()

        self.features = features
        self.fc_layers = []

        # create fc layers according to the layers_dim
        self.fc_layers = nn.Sequential(
            collections.OrderedDict(
                [
                    (
                        "Layer {}".format(i),
                        nn.Sequential(
                            collections.OrderedDict(
                                [
                                    ("linear", nn.Linear(n_in, n_out, bias = False),),
                                    ("batchnorm", nn.BatchNorm1d(n_out, momentum=0.01, eps=0.001) if use_batch_norm else None,),
                                    ("act", nn.ReLU() if negative_slope <= 0 else nn.LeakyReLU(negative_slope = negative_slope),),
                                    ("dropout", nn.Dropout(p=dropout_rate) if dropout_rate > 0 else None,),
                                ]
                            )
                        ),
                    )
                    for i, (n_in, n_out) in enumerate(zip(self.features[:-1], self.features[1:]))
                ]
            )
        )

    def forward(self, x):
        # loop through all layers
        for layers in self.fc_layers:
            # loop through linear, batchnorm, relu, dropout, etc
            for layer in layers:
                if layer is not None:
                    x = layer(x)
        
        return x

class OutputLayer(nn.Module):
    def __init__(self, outputSize, lastHidden) -> None:
        super().__init__()
        self.output_size = outputSize
        self.last_hidden = lastHidden
        self.mean_layer = FC(features=[self.last_hidden, self.output_size])
        self.pi_layer = FC_PI(features=[self.last_hidden, self.output_size])
        self.theta_layer = FC(features=[self.last_hidden, self.output_size])

    def forward(self, decodedData):
        Miu = self.mean_layer(decodedData)
        Pi = self.pi_layer(decodedData)
        Theta = self.theta_layer(decodedData)
        return Miu, Pi, Theta
