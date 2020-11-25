import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class Network1(nn.Module):
    def __init__(self, dataset, out_features):
        super(Network1, self).__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, out_features)

    def forward(self, x):
        x = x.view(-1, 784)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)
        x = self.fc3(x)
        x = F.relu(x)
        return x


class Network2(nn.Module):
    def __init__(self, dataset, out_features):
        super(Network2, self).__init__()
        self.conv1 = nn.Conv2d(1, 16, kernel_size=5, padding=0, stride=1)
        self.conv2 = nn.Conv2d(16, 16, kernel_size=5, padding=0, stride=1)
        self.fc1 = nn.Linear(256, 100)
        self.fc2 = nn.Linear(100, out_features)

    def forward(self, x):
        x = self.conv1(x)
        x = F.max_pool2d(x, kernel_size=2, stride=2)
        x = F.relu(x)  ## inverted!
        x = self.conv2(x)
        x = F.max_pool2d(x, kernel_size=2, stride=2)
        x = F.relu(x)  ## inverted!
        x = x.view(-1, 256)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        x = F.relu(x)
        return x


class AlexNet_CIFAR10(nn.Module):
    def __init__(self, out_features=10):
        super(AlexNet_CIFAR10, self).__init__()
        self.conv_base = nn.Sequential(
            nn.Conv2d(3, 96, kernel_size=11, stride=4, padding=10),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.ReLU(inplace=True),  ## inverted!
            nn.BatchNorm2d(96),
            nn.Conv2d(96, 256, kernel_size=5, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.ReLU(inplace=True),  ## inverted!
            nn.BatchNorm2d(256),
            nn.Conv2d(256, 384, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(384, 384, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(384, 256, kernel_size=3, stride=1, padding=1),
            nn.ReLU(inplace=True),
        )
        self.fc_base = nn.Sequential(
            nn.Linear(256, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, out_features),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        x = self.conv_base(x)
        x = torch.flatten(x, 1)
        x = self.fc_base(x)
        return x


class AlexNet_FALCON(nn.Module):
    """
    This is the AlexNet version used in FALCON, which is not the standard
    of PyTorch
    """
    def __init__(self, out_features=10):
        super(AlexNet_FALCON, self).__init__()
        self.conv_base = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=1, padding=3),
            nn.Conv2d(64, 64, kernel_size=5, stride=1, padding=2),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.ReLU(inplace=True),  ## inverted!
            nn.BatchNorm2d(64),
            nn.Conv2d(64, 128, kernel_size=5, stride=1, padding=2),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.ReLU(inplace=True),  ## inverted!
            nn.BatchNorm2d(128),
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.ReLU(inplace=True),
        )
        self.fc_base = nn.Sequential(
            nn.Linear(16384, 1024),  # 7*7*256
            nn.ReLU(inplace=True),
            nn.Linear(1024, 1024),
            nn.ReLU(inplace=True),
            nn.Linear(1024, 200),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        x = self.conv_base(x)
        x = torch.flatten(x, 1)
        x = self.fc_base(x)
        return x


def alexnet(dataset, out_features):
    if dataset == "cifar10":
        model = AlexNet_CIFAR10(out_features)
        return model
    elif dataset == "tiny-imagenet":
        model = models.alexnet(pretrained=True)

        class Empty(nn.Module):
            def __init__(self):
                super().__init__()

            def forward(self, x):
                return x

        model.avgpool = Empty()

        model.classifier = nn.Sequential(
            # nn.Dropout(),
            nn.Linear(256, 1024),
            nn.ReLU(True),
            # nn.Dropout(),
            nn.Linear(1024, 1024),
            nn.ReLU(True),
            nn.Linear(1024, out_features),
        )

        # Invert ReLU and MaxPool2d
        for i, module in enumerate(model.features[:-1]):
            next_module = model.features[i + 1]
            if isinstance(module, nn.ReLU) and isinstance(next_module, nn.MaxPool2d):
                model.features[i + 1] = module
                model.features[i] = next_module

        return model
    else:
        raise ValueError("VGG16 can't be built for this dataset, maybe modify it?")


def vgg16(dataset, out_features):
    model = models.vgg16()

    # Invert ReLU <-> Maxpool
    for i, module in enumerate(model.features[:-1]):
        next_module = model.features[i + 1]
        if isinstance(module, nn.ReLU) and isinstance(next_module, nn.MaxPool2d):
            model.features[i + 1] = module
            model.features[i] = next_module

    class Empty(nn.Module):
        def __init__(self):
            super().__init__()

        def forward(self, x):
            return x

    model.avgpool = Empty()

    if dataset == "cifar10":
        first_linear = nn.Linear(512, 4096)
    elif dataset == "tiny-imagenet":
        first_linear = nn.Linear(512 * 2 * 2, 4096)
    else:
        raise ValueError("VGG16 can't be built for this dataset, maybe modify it?")

    model.classifier = nn.Sequential(
        first_linear,
        nn.ReLU(True),
        # nn.Dropout(),
        nn.Linear(4096, 4096),
        nn.ReLU(True),
        # nn.Dropout(),
        nn.Linear(4096, out_features),
    )

    return model


def resnet18(dataset, out_features):
    model = models.resnet18()
    model.maxpool, model.relu = model.relu, model.maxpool
    model.fc = nn.Linear(in_features=512, out_features=out_features)
    return model


model_zoo = {
    "network1": Network1,
    "network2": Network2,
    "resnet18": resnet18,
    "vgg16": vgg16,
    "alexnet": alexnet,
}


def get_model(model_name, dataset, out_features):
    return model_zoo[model_name](dataset, out_features)
