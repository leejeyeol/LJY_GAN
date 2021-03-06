import argparse
import os
import random

import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
import torch.optim as optim
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
from torch.autograd import Variable
import numpy as np
from torchvision import models
import glob
from PIL import Image
# import custom package
import LJY_utils
import LJY_visualize_tools

win_dict = LJY_visualize_tools.win_dict()
line_win_dict = LJY_visualize_tools.win_dict()

#=======================================================================================================================
# Options
#=======================================================================================================================
parser = argparse.ArgumentParser()
# Options for path =====================================================================================================
parser.add_argument('--type', default='train', help='train, validation, test')

parser.add_argument('--dataset', default='MNIST', help='what is dataset?')
parser.add_argument('--dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/CelebA/Img/img_anlign_celeba_png.7z/img_align_celeba_png', help='path to dataset')
parser.add_argument('--netG', default='', help="path of Generator networks.(to continue training)")
parser.add_argument('--netD', default='', help="path of Discriminator networks.(to continue training)")
parser.add_argument('--outf', default='./pretrained_model', help="folder to output images and model checkpoints")
parser.add_argument('--net_vgg', default='', help="path of vgg classifier")


parser.add_argument('--cuda', action='store_true', help='enables cuda')
parser.add_argument('--display', default=False, help='display options. default:False. NOT IMPLEMENTED')
parser.add_argument('--ngpu', type=int, default=1, help='number of GPUs to use')
parser.add_argument('--workers', type=int, default=1, help='number of data loading workers')
parser.add_argument('--iteration', type=int, default=1000, help='number of epochs to train for')

parser.add_argument('--DC_G_dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/AI2018_results/DCGAN', help='generated by DCGAN_inference')
parser.add_argument('--W_G_dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/AI2018_results/WGAN', help='generated by WGAN_inference')
parser.add_argument('--LS_G_dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/AI2018_results/LSGAN', help='generated by LSGAN_inference')
parser.add_argument('--EB_G_dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/AI2018_results/EBGAN', help='generated by EBGAN_inference')
parser.add_argument('--eval_fake_dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/AI2018_results/Test_Fake', help='path to dataset')
parser.add_argument('--test_dataroot', default='/media/leejeyeol/74B8D3C8B8D38750/Data/AI2018_FACE_test', help='path to dataset')

# these options are saved for testing
parser.add_argument('--batchSize', type=int, default=20, help='input batch size')
parser.add_argument('--imageSize', type=int, default=224, help='the height / width of the input image to network')
parser.add_argument('--model', type=str, default='pretrained_model', help='Model name')
parser.add_argument('--lr', type=float, default=0.0002, help='learning rate')
parser.add_argument('--beta1', type=float, default=0.5, help='beta1 for Adam.')
parser.add_argument('--num_fake_data', type=int, default=50000, help='number of fake data')


parser.add_argument('--seed', type=int, help='manual seed')


options = parser.parse_args()
print(options)

if options.type == 'train':
    batch_size=options.batchSize
else:
    batch_size= 1

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





#=======================================================================================================================
# Data and Parameters
#=======================================================================================================================


class Dataloader(torch.utils.data.Dataset):
    def __init__(self, path_real, fake_root_list, transform_crop, transform):
        super().__init__()
        self.transform_crop = transform_crop
        self.transform = transform
        self.fake_root_list = fake_root_list
        for path in self.fake_root_list:
            assert os.path.exists(path)

        #[path_DC, path_W, path_LS, path_EB] = self.fake_root_list

        assert os.path.exists(path_real)
        self.base_path_real = path_real

        cur_file_paths = sorted(glob.glob(self.base_path_real + '/*.*'))
        # for random sample
        # random_files = random.sample(range(0, len(cur_file_paths)), options.num_fake_data * 4)
        # self.file_paths = [cur_file_paths[i] for i in random_files]
        self.file_paths = cur_file_paths[0:options.num_fake_data * 4]
        self.label = [0 for _ in range(len(self.file_paths))]

        for path in self.fake_root_list:
            cur_file_paths = sorted(glob.glob(path + '/*.*'))
            self.file_paths = self.file_paths + cur_file_paths
            self.label = self.label + [1 for _ in range(options.num_fake_data)]

    def pil_loader(self, path):
        # open path as file to avoid ResourceWarning (https://github.com/python-pillow/Pillow/issues/835)
        with open(path, 'rb') as f:
            with Image.open(f) as img:
                return img.convert('RGB')

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, item):
        path, label = self.file_paths[item], self.label[item]

        img = self.pil_loader(path)
        if label == 0 :
            img = self.transform_crop(img)
        else:
            #img= self.transform(img)
            img = self.transform(img)


        return img, label

transform_crop = transforms.Compose([
    transforms.CenterCrop(150),
    transforms.Scale(64),
    transforms.Scale(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])])
transform = transforms.Compose([
    transforms.Scale(150),
    transforms.Scale(64),
    transforms.Scale(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])])
makeimg = transforms.ToPILImage()
unorm = LJY_visualize_tools.UnNormalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])

dataloader = torch.utils.data.DataLoader(Dataloader(options.dataroot,[options.DC_G_dataroot,
                                                                      options.W_G_dataroot,
                                                                      options.LS_G_dataroot,
                                                                      options.EB_G_dataroot
                                                                      ], transform_crop,transform),
                                         batch_size=batch_size, shuffle=True, num_workers=options.workers,
                                         drop_last=False)
'''
dataloader = torch.utils.data.DataLoader(Dataloader(options.dataroot,[options.test_dataroot], transform_crop,transform),
                                         batch_size=batch_size, shuffle=True, num_workers=options.workers,
                                         drop_last=False)
'''
#=======================================================================================================================
# Models
#=======================================================================================================================



class VGG16(torch.nn.Module):
    def __init__(self):
        super(VGG16, self).__init__()
        vgg = models.vgg16(pretrained=True)
        vgg_pretrained_features = vgg.features
        vgg_classifier = vgg.classifier
        self.vgg_feature = torch.nn.Sequential()
        self.classifier = torch.nn.Sequential()

        for x in range(31):
            self.vgg_feature.add_module(str(x), vgg_pretrained_features[x])
        for x in range(6):
            self.classifier.add_module(str(x), vgg_classifier[x])
        self.classifier.add_module(str(6), nn.Linear(4096, 1, bias=True))
        self.classifier.add_module(str(7), nn.Sigmoid())

        self.classifier.apply(LJY_utils.weights_init)
    def forward(self, X):
        h = self.vgg_feature(X)
        h = h.view(h.size(0), -1)
        output = self.classifier(h)
        return output

vggnet = VGG16()
if options.net_vgg != '':
    vggnet.load_state_dict(torch.load(options.net_vgg))
print(vggnet)

#=======================================================================================================================
# Training
#=======================================================================================================================

# criterion set
BCE_loss = nn.BCELoss()
MSE_loss = nn.MSELoss()

# setup optimizer   ====================================================================================================
# todo add betas=(0.5, 0.999),
optimizer = optim.Adam(vggnet.parameters(), betas=(0.5, 0.999), lr=2e-5)



# container generate
input = torch.FloatTensor(options.batchSize, 3, options.imageSize, options.imageSize)



if options.cuda:
    vggnet.cuda()
    BCE_loss.cuda()
    MSE_loss.cuda()
    input = input.cuda()



# make to variables ====================================================================================================
input = Variable(input)


# training start
if options.type == 'train':
    print("Training Start!")
    for epoch in range(options.iteration):
        for i, (data, label) in enumerate(dataloader, 0):
            ############################
            # (1) Update D network
            ###########################
            # train with real data  ========================================================================================
            optimizer.zero_grad()


            real_cpu = data
            batch_size = real_cpu.size(0)
            input.data.resize_(real_cpu.size()).copy_(real_cpu)

            output = vggnet(input)
            label = label.float().view(label.shape[0], 1)
            label = Variable(label, volatile=True)
            if options.cuda:
                label = label.cuda()
            err = BCE_loss(output, label)
            err.backward()
            optimizer.step()
            print('\n')
            print('\n')
            print(list(np.asarray(label.data.view(-1),int)))
            print(list(np.asarray(output.data.round().view(-1),int)))
            print('\n')
            #visualize
            print('[%d/%d][%d/%d] Loss: %.6f label_mean : %.3f'
                  % (epoch, options.iteration, i, len(dataloader),
                     err.data.mean(),label.data.mean()))

            testImage = unorm(input.data[0].cpu().view(input.shape[1], input.shape[2], input.shape[3]))
            win_dict = LJY_visualize_tools.draw_images_to_windict(win_dict, [testImage], ["train"])
            line_win_dict = LJY_visualize_tools.draw_lines_to_windict(line_win_dict, [err.data.mean(),0], ['loss', 'zero'], epoch, i, len(dataloader))
            if i % 1000==0:
                torch.save(vggnet.state_dict(), '%s/vgg_%d.pth' % (options.outf, epoch))
        torch.save(vggnet.state_dict(), '%s/vgg_%d.pth' % (options.outf, epoch))
elif options.type == 'test':
    print("Testing Start!")
    TP = 0
    FP = 0
    FN = 0
    TN = 0
    for i, (data, label) in enumerate(dataloader, 0):
        ############################
        # (1) Update D network
        ###########################
        # train with real data  ========================================================================================
        print(i)
        optimizer.zero_grad()

        real_cpu = data
        batch_size = real_cpu.size(0)
        input.data.resize_(real_cpu.size()).copy_(real_cpu)

        output = vggnet(input)
        output = output.cpu().view(output.shape[0])
        label = label.float().view(label.shape[0])
        testImage=unorm(input.data.cpu().view(input.shape[1], input.shape[2], input.shape[3]))
        win_dict = LJY_visualize_tools.draw_images_to_windict(win_dict, [testImage], ["train"])

        if (label.cpu()[0] == 1):  # label is Positive
            if (output.data[0] >= 1 / 2):  # decision is Positive
                TP += 1
                makeimg(testImage).save(os.path.join(options.outf,'TP', '%05d.png' % (i)))
            else:  # decision is Negative
                FN += 1
                makeimg(testImage).save(os.path.join(options.outf,'FN', '%05d.png' % (i)))

        else:  # label is Negative
            if (output.data[0] <= 1 / 2):  # decision is Positive
                TN += 1
                makeimg(testImage).save(os.path.join(options.outf,'TN', '%05d.png' % (i)))

            else:  # decision is Negative
                FP += 1
                makeimg(testImage).save(os.path.join(options.outf,'FP', '%05d.png' % (i)))
    print("TP : %d\t FN : %d\t FP : %d\t TN : %d\t" % (TP, FN, FP, TN))
    print("Accuracy : %f \t Precision : %f \t Recall : %f" % (
        (TP + TN) / (TP + TN + FP + FN), TP / (TP + FP), TP / (FN + TP)))



# Je Yeol. Lee \[T]/
# Jolly Co-operation