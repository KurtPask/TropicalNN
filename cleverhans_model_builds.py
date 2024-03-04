import math
import time
import sys
import numpy as np
import tensorflow as tf

from absl import app, flags

from functions.models import CH_ReluConv3Layer, CH_ReLU_ResNet50, CH_Trop_ResNet50, CH_TropConv3LayerLogits, CH_MaxoutConv3Layer, CH_MaxOut_ResNet50
from functions.load_data import ld_mnist, ld_svhn, ld_cifar10  

from cleverhans.tf2.attacks.projected_gradient_descent import projected_gradient_descent
from cleverhans.tf2.attacks.fast_gradient_method import fast_gradient_method

FLAGS = flags.FLAGS

def main(_):
    if len(sys.argv) > 1:
        adv_train = sys.argv[1]
        arg_dataset = sys.argv[2]
        batch_size = int(sys.argv[3])
        print('argument dataset', arg_dataset, arg_dataset == FLAGS.dataset)
    else:
        adv_train = 'yes'
        arg_dataset = 'mnist'
        batch_size = 128
    
    if adv_train == 'yes':
        FLAGS.adv_train = True
    else:
        FLAGS.adv_train = False
    
    # Load training and test data
    if arg_dataset == "mnist":
        FLAGS.dataset = "mnist"
        FLAGS.eps = 0.2
        data, info = ld_mnist(batch_size=batch_size)
        models = {'CH_ReluConv3Layer': CH_ReluConv3Layer(num_classes=10),
                  'CH_TropConv3Layer': CH_TropConv3LayerLogits(num_classes=10),
                  'CH_MaxoutConv3Layer': CH_MaxoutConv3Layer(num_classes=10)
                  }
    elif arg_dataset == "svhn":
        FLAGS.dataset = "svhn"
        FLAGS.eps = 8/255
        data, info = ld_svhn(batch_size=batch_size)
        models = {
                  'CH_TropConv3Layer': CH_TropConv3LayerLogits(num_classes=10),
                  'CH_ReluConv3Layer': CH_ReluConv3Layer(num_classes=10),
                  'CH_MaxoutConv3Layer': CH_MaxoutConv3Layer(num_classes=10)}
    else:
        FLAGS.dataset = "cifar"
        FLAGS.eps = 8/255
        data, info = ld_cifar10(batch_size=batch_size)
        models = {'CH_ReLU_ResNet50': CH_ReLU_ResNet50(num_classes=10),
                  #'CH_Trop_ResNet50': CH_Trop_ResNet50(num_classes=10),
                  #'CH_MaxOut_ResNet50': CH_MaxOut_ResNet50(num_classes=10)
                  }

    for name, model in models.items():
        if 'Trop' in name:
            boo_tropical = True
        
        loss_object = tf.losses.SparseCategoricalCrossentropy(from_logits=True)
        optimizer = tf.optimizers.Adam(learning_rate=0.001)

        # Metrics to track the different accuracies.
        train_loss = tf.metrics.Mean(name="train_loss")
        train_acc = tf.metrics.SparseCategoricalAccuracy()

        @tf.function
        def train_step(x, y):
            with tf.GradientTape() as tape:
                predictions = model(x)
                loss = loss_object(y, predictions)
            gradients = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(gradients, model.trainable_variables))
            train_loss(loss)
            train_acc(y, predictions)

        start = time.time()
        # Train model with adversarial training
        for epoch in range(FLAGS.nb_epochs):
            # keras like display of progress
            progress_bar_train = tf.keras.utils.Progbar(info.splits['train'].num_examples)
            print(f"--epoch {epoch}--")
            for (x, y) in data.train:
                if FLAGS.adv_train:
                    # Replace clean example with adversarial example for adversarial training
                    x = projected_gradient_descent(model_fn = model,
                                                    x = x,
                                                    eps = FLAGS.eps,
                                                    eps_iter = 0.01,
                                                    nb_iter = 40,
                                                    norm = np.inf,
                                                    loss_fn = None,
                                                    clip_min = -1.0,
                                                    clip_max = 1.0,
                                                    y = None,
                                                    targeted = False,
                                                    rand_init = True,
                                                    rand_minmax = FLAGS.eps,
                                                    sanity_checks=False)
                train_step(x, y)
                progress_bar_train.add(x.shape[0], values=[("loss", train_loss.result()), ("acc", train_acc.result())])
        elapsed = time.time() - start
        print(f'##### training time = {elapsed} seconds | {elapsed/60} minutes')
        model.summary()
        #model.save(f'saved_models/{name}_{FLAGS.dataset}_{FLAGS.eps}_{FLAGS.nb_epochs}_{FLAGS.adv_train}', save_format='tf')

if __name__ == "__main__":
    print("##########      Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))
    flags.DEFINE_integer("nb_epochs", 100, "Number of epochs.")
    flags.DEFINE_float("eps", 0.1, "Total epsilon for FGM and PGD attacks.")
    flags.DEFINE_bool("adv_train", False, "Use adversarial training (on PGD adversarial examples).")
    flags.DEFINE_string("dataset", "mnist", "Specifies dataset used to train the model.")
    app.run(main)