import matplotlib.pyplot as plt
import tensorflow as tf
import os
from functions.models import ResNet50Model, ModifiedLeNet5, LeNet5, VGG16Model, MobileNetModel, EfficientNetB4Model, AlexNetModel, MMRModel
from tensorflow import cast, float32, reduce_any
import tensorflow_datasets as tfds
from easydict import EasyDict

def convert_types(image, label):
    """Convert image types and normalize to [-1, 1]."""
    image = cast(image, float32)
    image /= 127.5
    image -= 1.0
    return image, label

def filter_classes(dataset, classes):
    """Filter the dataset to include only specified classes."""
    return dataset.filter(lambda image, label: reduce_any([label == cls for cls in classes]))

def ld_mnist(batch_size=128, classes=None):
    """Load MNIST training and test data and filter by specified classes."""
    dataset, info = tfds.load("mnist", with_info=True, as_supervised=True)

    mnist_train, mnist_test = dataset["train"], dataset["test"]
    
    # Apply class filtering if classes are specified
    if classes is not None:
        mnist_train = filter_classes(mnist_train, classes)
        mnist_test = filter_classes(mnist_test, classes)
    
    mnist_train = mnist_train.map(convert_types).shuffle(10000).batch(batch_size)
    mnist_test = mnist_test.map(convert_types).batch(batch_size)

    return EasyDict(train=mnist_train, test=mnist_test), info

def ld_svhn(batch_size = 128):
    """Load SVHN training and test data."""
    dataset, info = tfds.load("svhn_cropped", with_info=True, as_supervised=True)

    svhn_train, svhn_test = dataset["train"], dataset["test"]
    svhn_train = svhn_train.map(convert_types).shuffle(10000).batch(batch_size)
    svhn_test = svhn_test.map(convert_types).batch(batch_size)

    return EasyDict(train=svhn_train, test=svhn_test), info

def ld_cifar10(batch_size = 128):
    """Load CIFAR-10 training and test data."""
    dataset, info = tfds.load("cifar10", with_info=True, as_supervised=True)

    cifar10_train, cifar10_test = dataset["train"], dataset["test"]
    cifar10_train = cifar10_train.map(convert_types).shuffle(10000).batch(batch_size)
    cifar10_test = cifar10_test.map(convert_types).batch(batch_size)

    return EasyDict(train=cifar10_train, test=cifar10_test), info

def ld_cifar100(batch_size = 128):
    """Load CIFAR-10 training and test data."""
    dataset, info = tfds.load("cifar100", with_info=True, as_supervised=True)

    cifar100_train, cifar100_test = dataset["train"], dataset["test"]
    cifar100_train = cifar100_train.map(convert_types).shuffle(10000).batch(batch_size)
    cifar100_test = cifar100_test.map(convert_types).batch(batch_size)

    return EasyDict(train=cifar100_train, test=cifar100_test), info

def l2(x, y):
    return tf.sqrt(tf.reduce_sum(tf.square(x - y), list(range(1, len(x.shape)))))

def l1(x, y):
    return tf.reduce_sum(tf.abs(x - y), list(range(1, len(x.shape))))

def plot_images_in_grid(list_of_xs, row_labels, col_labels, save_path, input_elements):
    num_rows = len(row_labels)
    num_cols = len(col_labels)
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(num_cols * 2, num_rows * 2))
    if input_elements == 784:
        cmap = 'gray'
    else:
        cmap = None
    for i in range(num_rows):
        for j in range(num_cols):
            ax = axes[i, j]
            ax.imshow(list_of_xs[j][i,:,:,:], cmap=cmap)
            ax.axis('off')
            if i == 0:
                ax.set_title(col_labels[j], size='large')
    
    #plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()


def load_data(dataset_name, batch_size, classes = None):
    # -- load data and set epsilon --
    if dataset_name == "mnist":
        dataset_category = 0
        eps = 0.2
        input_elements = 28*28*1
        data, info = ld_mnist(batch_size=batch_size, classes=classes)
        num_classes = 10
        input_shape = (28,28,1)
    elif dataset_name == "svhn":
        dataset_category = 0
        eps = 8/255
        input_elements = 32*32*3
        data, info = ld_svhn(batch_size=batch_size)
        num_classes = 10
        input_shape = (32,32,3)
    elif dataset_name == "cifar10":
        dataset_category = 1
        eps = 8/255
        input_elements = 32*32*3
        data, info = ld_cifar10(batch_size=batch_size)
        num_classes = 10
        input_shape = (32,32,3)
    elif dataset_name == "cifar100":
        dataset_category = 1
        eps = 8/255
        input_elements = 32*32*3
        data, info = ld_cifar100(batch_size=batch_size)
        num_classes = 100
        input_shape = (32,32,3)
    else:
        raise ValueError("Invalid dataset name provided. Should be either mnist, svhn, cifar10, cifar100, or imagenet")
    return dataset_category, eps, input_elements, data, info, input_shape, num_classes


def find_model(dataset_name, base_model, top_layer, root_dir = "new_master_models"):
    valid_datasets = ["mnist", "svhn", "cifar10", "cifar100"]
    valid_base_models = ["LeNet5", "ModifiedLeNet5", "MobileNet", "ResNet50", "VGG16", "EfficientNetB4"]
    valid_top_layers = ["maxout", "relu", "trop"]
    for dir_path, _dirnames_, filenames in os.walk(root_dir):
        for filename in filenames:
            if not ".keras" in filename:
                continue
            list_dirname = filename.split('_')
            if (list_dirname[0] == dataset_name) and (list_dirname[1] == base_model) and (list_dirname[2] == top_layer) and (list_dirname[3] == "no"):
                return os.path.join(dir_path, filename)  


def model_choice(dataset_name, base_model, top, adv_train):
    if dataset_name == "cifar100":
        num_classes = 100
    else:
        num_classes = 10

    if base_model == "LeNet5":
        model = LeNet5(num_classes=num_classes, top=top)
    elif base_model == "ModifiedLeNet5":
        model =  ModifiedLeNet5(num_classes=num_classes, top=top)
    elif base_model == "MobileNet":
        model =  MobileNetModel(num_classes=num_classes, top=top)
    elif base_model == "ResNet50":
        model =  ResNet50Model(num_classes=num_classes, top=top)
    elif base_model == "VGG16":
        model =  VGG16Model(num_classes=num_classes, top=top)
    elif base_model == "EfficientNetB4":
        model =  EfficientNetB4Model(num_classes=num_classes, top=top)
    elif base_model == "AlexNet":
        model =  AlexNetModel(num_classes=num_classes, top=top)
    elif base_model == "MMR":
        model = MMRModel(num_classes=num_classes)

    if adv_train == "yes":
        starting_model_path = find_model(dataset_name, base_model, top)
        starting_model = tf.keras.models.load_model(starting_model_path)
        new_model = tf.keras.models.clone_model(starting_model)
        starting_model_weights = starting_model.get_weights()
        new_model.set_weights(starting_model_weights)
        return new_model
    else:
        return model

def load_models(config):
    models = {}
    for dataset_name, config1 in config.items():
        for base_model, config2 in config1.items():
            for top_layer, config3 in config2.items():
                for adv_train, answer in config3.items():
                    if answer == 1:
                        models[f"{dataset_name}_{base_model}_{top_layer}_{adv_train}"] = model_choice(dataset_name, base_model, top_layer, adv_train)
    return models
                                                                                    
def find_directories_with_keyphrase(root_dir, dataset_name):
    valid_datasets = ["mnist", "svhn", "cifar10", "cifar100"]
    valid_base_models = ["LeNet5", "ModifiedLeNet5", "MobileNet", "ResNet50", "VGG16", "EfficientNetB4"]
    valid_top_layers = ["maxout", "relu", "trop", "MMRModel"]
    models_to_attack = {
                        "mnist" : {"LeNet5" :           {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}},
                                    "ModifiedLeNet5" :  {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0},
                                                        "MMRModel" :{"yes" : 0, "no" : 1}}},
                                                
                        "svhn" :  {"LeNet5" :           {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}},
                                    "ModifiedLeNet5" :  {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0},
                                                        "MMRModel" :{"yes" : 0, "no" : 1}},
                                    "MobileNet" :       {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}}},
                                                        
                        "cifar10" : {"ResNet50" :       {"trop" :   {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "maxout" :  {"yes" : 0, "no" : 0}},
                                    "VGG16" :           {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}},
                                    "EfficientNetB4" :  {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}}},
                                                        
                        "cifar100" : {"ResNet50" :      {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}},
                                    "VGG16" :           {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}},
                                    "EfficientNetB4" :  {"maxout" : {"yes" : 0, "no" : 0},
                                                        "relu" :    {"yes" : 0, "no" : 0},
                                                        "trop" :    {"yes" : 0, "no" : 0}}},
                    }
    #{dataset_name}_{base_model}_{top_layer}_{adv_train}
    result = {}
    for dir_path, dirnames, filenames in os.walk(root_dir):
        for dirname in dirnames:
            list_dirname = dirname.split('_')
            if (not list_dirname[0] in valid_datasets) or (not list_dirname[1] in valid_base_models) or (not list_dirname[2] in valid_top_layers):
                continue
            #print(list_dirname)
            if (dataset_name in dirname) and (models_to_attack[list_dirname[0]][list_dirname[1]][list_dirname[2]][list_dirname[3]] == 1):
                result[dirname] = os.path.join(dir_path, dirname)
        for filename in filenames:
            if not ".keras" in filename:
                continue
            list_dirname = filename.split('_')
            if (not list_dirname[0] in valid_datasets) or (not list_dirname[1] in valid_base_models) or (not list_dirname[2] in valid_top_layers):
                continue
            #print(list_dirname)
            if (dataset_name in filename) and (models_to_attack[list_dirname[0]][list_dirname[1]][list_dirname[2]][list_dirname[3]] == 1):
                result[filename] = os.path.join(dir_path, filename)
    return result


def load_attack_settings(dataset_name, batch_size, root_dir):
    _, eps, _, data, info, _, _ = load_data(dataset_name, batch_size)
    model_paths = find_directories_with_keyphrase(root_dir, dataset_name)
    return eps, data, info, model_paths


def save_location_attack_results(arg_dataset, name, batch_chunk, total_batch_chunks,attack_type):
    list_dirname = name.split('_')
    base_model = list_dirname[1]
    top_layer = list_dirname[2]
    adv_train = list_dirname[3]
    if not os.path.exists('new_attack_results'):  # Check if directory doesn't exist
        os.makedirs('new_attack_results')
    if not os.path.exists(f'new_attack_results/{arg_dataset}'):  # Check if directory doesn't exist
        os.makedirs(f'new_attack_results/{arg_dataset}')
    if not os.path.exists(f'new_attack_results/{arg_dataset}/{base_model}'):  # Check if directory doesn't exist
        os.makedirs(f'new_attack_results/{arg_dataset}/{base_model}')
    if not os.path.exists(f'new_attack_results/{arg_dataset}/{base_model}/{top_layer}'):  # Check if directory doesn't exist
        os.makedirs(f'new_attack_results/{arg_dataset}/{base_model}/{top_layer}')
    if not os.path.exists(f'new_attack_results/{arg_dataset}/{base_model}/{top_layer}/{adv_train}'):  # Check if directory doesn't exist
        os.makedirs(f'new_attack_results/{arg_dataset}/{base_model}/{top_layer}/{adv_train}')
    new_name = name.replace('.keras', '')
    return f'new_attack_results/{arg_dataset}/{base_model}/{top_layer}/{adv_train}/{new_name}_{batch_chunk}_of_{total_batch_chunks}_{attack_type}.csv'