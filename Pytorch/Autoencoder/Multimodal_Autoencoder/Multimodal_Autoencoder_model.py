import torch
import torch.nn as nn



# 64x212
class encoder(nn.Module):
    def __init__(self, n_channel):
        super().__init__()
        self.n_channel = n_channel
        #512
        self.encoder = nn.Sequential(
            nn.Conv2d(n_channel, 64, (4, 8), 2, 1),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(64, 128, (4, 8), 2, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(128, 256, (4, 8), 2, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(256, 512, (4, 8), 2, 1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(512, 512, (4, 9), 1, 0),
            nn.LeakyReLU(0.2, True)
        )
        # init weights
        self.weight_init()

    def encode(self, x):
        return self.encoder(x)

    def forward(self, x):
        z = self.encode(x)
        return z

    def weight_init(self):
        self.encoder.apply(weight_init)


class decoder(nn.Module):
    def __init__(self, n_channel):
        super().__init__()
        self.n_channel = n_channel
        #2048
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(2048, 512, (4, 9), 1, 0),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(512, 256, (4, 9), 2, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(256, 128, (4, 8), 2, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(128, 64, (4, 8), 2, 1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(64, self.n_channel, (4, 8), 2, 1),
            nn.Tanh()
        )

        # init weights
        self.weight_init()

    def decode(self, z):
        return self.decoder(z)

    def forward(self, z):
        return self.decode(z)

    def weight_init(self):
        self.decoder.apply(weight_init)
# xavier_init
def weight_init(module):
    classname = module.__class__.__name__
    if classname.find('Conv') != -1:
        torch.nn.init.xavier_normal(module.weight.data)
        # module.weight.data.normal_(0.0, 0.01)
    elif classname.find('BatchNorm') != -1:
        module.weight.data.normal_(1.0, 0.02)
        module.bias.data.fill_(0)

'''
1242x375(is too large)
class encoder(nn.Module):
    def __init__(self):
        super().__init__()
        #512
        self.encoder = nn.Sequential(
            nn.Conv2d(1, 64, (4, 11), 2, 1),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(64, 128, (4, 11), 2, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(128, 256, (4, 11), 2, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(256, 512, (4, 11), 2, 1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(512, 512, (4, 11), 2, 1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.Conv2d(512, 512, (3, 12), 1, 0),
            nn.LeakyReLU(0.2, True)

        )
        # init weights
        self.weight_init()

    def encode(self, x):
        return self.encoder(x)

    def forward(self, x):
        z = self.encode(x)
        return z

    def weight_init(self):
        self.encoder.apply(weight_init)


class decoder(nn.Module):
    def __init__(self, data_type="rgb"):
        super().__init__()
        self.data_type = data_type
        #2048
        self.decoder_RGB = nn.Sequential(
            nn.ConvTranspose2d(2048, 512, (3, 12), 1, 0),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(512, 512, (4, 11), 2, 1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(512, 256, (4, 11), 2, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(256, 128, (4, 12), 2, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(128, 64, (4, 12), 2, 1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(64, 1, (4, 12), 2, 1),
            nn.Tanh()
        )
        self.decoder_d = nn.Sequential(
            nn.ConvTranspose2d(2048, 512, (3, 12), 1, 0),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(512, 512, (4, 11), 2, 1),
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(512, 256, (4, 11), 2, 1),
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(256, 128, (4, 12), 2, 1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(128, 64, (4, 12), 2, 1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, True),

            nn.ConvTranspose2d(64, 1, (4, 12), 2, 1),
            nn.Tanh()
        )

        # init weights
        self.weight_init()

    def decode(self, z):
        if self.data_type == "rgb":
            return self.decoder_RGB(z)
        elif self.data_type == "d":
            return self.decoder_d(z)

    def forward(self, z):
        return self.decode(z)

    def weight_init(self):
        if self.data_type == "rgb":
            self.decoder_RGB.apply(weight_init)
        elif self.data_type == "d":
            self.decoder_d.apply(weight_init)
'''
'''

class encoder(nn.Module):
    def __init__(self):
        super().__init__()
        #512
        self.encoder = nn.Sequential(
            nn.Linear(1080,1024),
            nn.LeakyReLU(0.2, True),

            nn.Linear(1024, 512),
            nn.LeakyReLU(0.2, True),

            nn.Linear(512, 24),
            nn.LeakyReLU(0.2, True)
        )
        # init weights
        self.weight_init()

    def encode(self, x):
        return self.encoder(x)

    def forward(self, x):
        z = self.encode(x)
        return z

    def weight_init(self):
        self.encoder.apply(weight_init)


class decoder(nn.Module):
    def __init__(self, data_type="rgb"):
        super().__init__()
        self.data_type = data_type
        #2048
        self.decoder_RGB = nn.Sequential(
            nn.Linear(96, 512),
            nn.ReLU(),

            nn.Linear(512, 1024),
            nn.ReLU(),

            nn.Linear(1024, 1080),
            nn.Tanh()
        )
        self.decoder_d = nn.Sequential(
            nn.Linear(96, 512),
            nn.ReLU(),

            nn.Linear(512, 1024),
            nn.ReLU(),

            nn.Linear(1024, 1080),
        )

        # init weights
        self.weight_init()

    def decode(self, z):
        if self.data_type == "rgb":
            return self.decoder_RGB(z)
        elif self.data_type == "d":
            return self.decoder_d(z)

    def forward(self, z):
        return self.decode(z)

    def weight_init(self):
        if self.data_type == "rgb":
            self.decoder_RGB.apply(weight_init)
        elif self.data_type == "d":
            self.decoder_d.apply(weight_init)
'''