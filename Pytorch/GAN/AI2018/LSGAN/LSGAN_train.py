import argparse
import os
import random

import torch.backends.cudnn as cudnn
import torch.optim as optim
import torch.utils.data
import torchvision.transforms as transforms
from torch.autograd import Variable

import GAN.AI2018.LSGAN.LSGAN_model as model
import GAN.AI2018.LSGAN.LSGAN_dataloader as dset
# import custom package
import LJY_utils
import LJY_visualize_tools

#=======================================================================================================================
# Options
#=======================================================================================================================
parser = argparse.ArgumentParser()
# Options for path =====================================================================================================
parser.add_argument('--dataset', default='CelebA', help='what is dataset?')
parser.add_argument('--dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/CelebA/Img/img_anlign_celeba_png.7z/img_align_celeba_png', help='path to dataset')
parser.add_argument('--fold', type=int,default=None, help = 'fold number')
parser.add_argument('--fold_dataroot', default='',help='Proprocessing/fold_divider.py')

parser.add_argument('--netG', default='', help="path of Generator networks.(to continue training)")
parser.add_argument('--netD', default='', help="path of Discriminator networks.(to continue training)")
parser.add_argument('--outf', default='./output', help="folder to output images and model checkpoints")

parser.add_argument('--cuda', action='store_true', help='enables cuda')
parser.add_argument('--display', default=True, help='display options. default:False.')
parser.add_argument('--ngpu', type=int, default=1, help='number of GPUs to use')
parser.add_argument('--workers', type=int, default=1, help='number of data loading workers')
parser.add_argument('--iteration', type=int, default=1000, help='number of epochs to train for')

# these options are saved for testing
parser.add_argument('--batchSize', type=int, default=80, help='input batch size')
parser.add_argument('--imageSize', type=int, default=64, help='the height / width of the input image to network')
parser.add_argument('--model', type=str, default='pretrained_model', help='Model name')
parser.add_argument('--nc', type=int, default=3, help='number of input channel.')
parser.add_argument('--nz', type=int, default=100, help='dimension of noise.')
parser.add_argument('--ngf', type=int, default=64, help='number of generator filters.')
parser.add_argument('--ndf', type=int, default=64, help='number of discriminator filters.')

parser.add_argument('--seed', type=int, help='manual seed')

options = parser.parse_args()
print(options)



# save directory make   ================================================================================================
try:
    os.makedirs(options.outf)
except OSError:
    pass

# seed set  ============================================================================================================
if options.seed is None:
    options.seed = random.randint(1, 10000)
print("Random Seed: ", options.seed)
random.seed(options.seed)
torch.manual_seed(options.seed)

# cuda set  ============================================================================================================
if options.cuda:
    torch.cuda.manual_seed(options.seed)

torch.backends.cudnn.benchmark = True
cudnn.benchmark = True
if torch.cuda.is_available() and not options.cuda:
    print("WARNING: You have a CUDA device, so you should probably run with --cuda")


# ======================================================================================================================
# Data and Parameters
# ======================================================================================================================
display = options.display
dataset= options.dataset
batch_size = options.batchSize
ngpu = int(options.ngpu)
nz = int(options.nz)
ngf = int(options.ngf)
ndf = int(options.ndf)
nc = int(options.nc)
# CelebA call and load   ===============================================================================================


transform = transforms.Compose([
    transforms.CenterCrop(150),
    #transforms.Scale(64),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))
])

if options.fold is None:
    dataloader = torch.utils.data.DataLoader(dset.Dataloader(options.dataroot, transform),
                                             batch_size=options.batchSize, shuffle=True, num_workers=options.workers,drop_last=False)
else:
    dataloader = torch.utils.data.DataLoader(dset.fold_Dataloader(options.fold, options.fold_dataroot, transform, type='train'),
                                             batch_size=options.batchSize, shuffle=True, num_workers=options.workers,drop_last=False)
unorm = LJY_visualize_tools.UnNormalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5))

# ======================================================================================================================
# Models
# ======================================================================================================================

# Generator ============================================================================================================
netG = model.Generator(ngpu, nz, ngf, nc)
netG.apply(LJY_utils.weights_init)
if options.netG != '':
    netG.load_state_dict(torch.load(options.netG))
print(netG)

# Discriminator ========================================================================================================
netD = model.Discriminator(ngpu, ndf, nc)
netD.apply(LJY_utils.weights_init)
if options.netD != '':
    netD.load_state_dict(torch.load(options.netD))
print(netD)

# ======================================================================================================================
# Training
# ======================================================================================================================


# setup optimizer   ====================================================================================================
# todo add betas=(0.5, 0.999),
optimizerD = optim.Adam(netD.parameters(), betas=(0.5, 0.999), lr=2e-4)
optimizerG = optim.Adam(netG.parameters(), betas=(0.5, 0.999), lr=1e-3)



# container generate
noise = torch.FloatTensor(batch_size, nz, 1, 1)

label = torch.FloatTensor(batch_size)
real_label = 1
fake_label = 0

if options.cuda:
    netD.cuda()
    netG.cuda()

    label = label.cuda()
    noise = noise.cuda()


# make to variables ====================================================================================================

label = Variable(label)
noise = Variable(noise)

# for visualize
win_dict = LJY_visualize_tools.win_dict()
line_win_dict = LJY_visualize_tools.win_dict()

# training start
print("Training Start!")
for epoch in range(options.iteration):
    for i, (data) in enumerate(dataloader, 0):
        ############################
        # (1) Update D network
        ###########################
        # train with real data  ========================================================================================
        optimizerD.zero_grad()

        input = Variable(data, requires_grad=True)
        if options.cuda:
           input = input.cuda()


        outputD_real = netD(input)
        visual_D_real = outputD_real.data.mean()   # for visualize

        # generate noise    ============================================================================================
        noise.data.resize_(input.size(0), nz, 1, 1)
        noise.data.normal_(0, 1)

        # train with fake data   =======================================================================================
        fake = netG(noise)


        outputD_fake = netD(fake.detach())
        visual_D_fake = outputD_fake.data.mean()

        errD = 0.5 * (torch.mean((outputD_real-real_label)**2) + torch.mean((outputD_fake-fake_label)**2))
        errD.backward()
        optimizerD.step()

        ############################
        # (2) Update G network and Q network
        ###########################
        optimizerG.zero_grad()
        label.data.fill_(real_label)  # fake labels are real for generator cost

        outputD = netD(fake)
        errG = 0.5 * torch.mean((outputD-real_label)**2)
        errG.backward()
        visual_D_fake_2 = outputD.data.mean()

        optimizerG.step()

        #visualize
        print('[%d/%d][%d/%d] Loss_D: %.4f Loss_G: %.4f     D(x): %.4f D(G(z)): %.4f | %.4f'
              % (epoch, options.iteration, i, len(dataloader),
                 errD.data[0], errG.data[0],  visual_D_real, visual_D_fake, visual_D_fake_2))

        if display:
            testImage = torch.cat((unorm(input.data[0]), unorm(fake.data[0])), 2)
            win_dict = LJY_visualize_tools.draw_images_to_windict(win_dict, [testImage], ["LSGAN_%s" % dataset])
            line_win_dict = LJY_visualize_tools.draw_lines_to_windict(line_win_dict,
                                                                      [errD.data.mean(), errG.data.mean(), visual_D_real,
                                                                       visual_D_fake],
                                                                      ['lossD', 'lossG', 'real is?', 'fake is?'], epoch,i,
                                                                      len(dataloader))

    # do checkpointing
    if epoch % 10 == 0:
        torch.save(netG.state_dict(), '%s/%d_fold_netG_epoch_%d.pth' % (options.outf, options.fold, epoch))
        torch.save(netD.state_dict(), '%s/%d_fold_netD_epoch_%d.pth' % (options.outf, options.fold, epoch))

# Je Yeol. Lee \[T]/