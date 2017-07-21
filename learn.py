import tflearn
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.estimator import regression
from tflearn.layers.normalization import local_response_normalization
import numpy as np
import cv2
import os

PHONE_IMAGES = ['.images/ios_ready', '.images/android_ready']
NON_PHONE_IMAGES = ['.images/non_ready']

def load_images(img_dirs):
    images = list()
    for directory in img_dirs:
        for img_file in os.listdir(directory):
            img = cv2.imread(os.path.join(directory, img_file), cv2.IMREAD_GRAYSCALE)
            images.append(img)
    return images

def main():
    all_phone_images = load_images(PHONE_IMAGES)
    all_non_images = load_images(NON_PHONE_IMAGES)

    X = [x.reshape([128, 128, 1]) for x in all_phone_images + all_non_images]
    #X = np.array(all_phone_images + all_non_images)
    Y = [[1, 0] for _ in all_phone_images] + [[0, 1] for _ in all_non_images]

    data = list(zip(X, Y))
    data = tflearn.data_utils.shuffle(data)
    
    print(len(all_phone_images))
    print(len(all_non_images))

    # heavily inspired by the examples
    # https://github.com/tflearn/tflearn/blob/master/examples/images/convnet_mnist.py
    network = input_data(shape=[None, 128, 128, 1], name='input')
    network = conv_2d(network, 4, 6, activation='relu', regularizer="L2")
    network = max_pool_2d(network, 6)
    network = local_response_normalization(network)
    network = conv_2d(network, 8, 6, activation='relu', regularizer="L2")
    network = max_pool_2d(network, 6)
    network = local_response_normalization(network)
    network = fully_connected(network, 1024, activation='relu')
    network = dropout(network, 0.8)
    network = fully_connected(network, 1024, activation='relu')
    network = dropout(network, 0.8)
    network = fully_connected(network, 2, activation='softmax')
    network = regression(network, name='target')

    model = tflearn.DNN(network, tensorboard_verbose=0)
    model.fit(X, Y, n_epoch=20,
              validation_set=0.1, shuffle=True, snapshot_step=100,
              show_metric=True, run_id='phone_images')

    
if __name__ == "__main__":
    main()
