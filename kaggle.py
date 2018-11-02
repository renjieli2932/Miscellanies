#!/usr/bin/env python
# ECBM E4040 Fall 2018 Assignment 2
# This script is intended for task 5 Kaggle competition. Use it however you want.

import tensorflow as tf
import numpy as np
import time
import _pickle as pickle
import os
import zipfile # different from tar.gz in other tasks
import glob
from scipy.misc import imread
from scipy.misc import imresize
from sklearn.model_selection import train_test_split
#############################################
#############   LOAD  DATA       ############
#############################################
def load_data(mode='all'):
    """
    Unpack the CIFAR-10 dataset and load the datasets.
    :param mode: 'train', or 'test', or 'all'. Specify the training set or test set, or load all the data.
    :return: A tuple of data/labels, depending on the chosen mode. If 'train', return training data and labels;
    If 'test' ,return test data and labels; If 'all', return both training and test sets.
    """

    if not os.path.exists('./data/kaggle_train_128.zip'):
        print('Train Data Not Existed!')
        raise ValueError
    else:
        print('./data/kaggle_train_128.zip already exists. Begin extracting...')
    # Check if the package has been unpacked, otherwise unpack the package
    if not os.path.exists('./data/train_128/'):
        package = zipfile.ZipFile('./data/kaggle_train_128.zip')
        package.extractall('./data')
        package.close()

    if not os.path.exists('./data/kaggle_test_128.zip'):
        print('Test Data Not Existed!')
        raise ValueError
    else:
        print('./data/kaggle_test_128.zip already exists. Begin extracting...')
    # Check if the package has been unpacked, otherwise unpack the package
    if not os.path.exists('./data/test_128/'):
        package = zipfile.ZipFile('./data/kaggle_test_128.zip')
        package.extractall('./data')
        package.close()

    
    # Go to the location where the files are unpacked
    root_dir = os.getcwd()
    os.chdir(root_dir+'/data/train_128')
    train_data = []
    train_label = []
    val_data = []
    val_label = []
    test_data = []
    #test_label = [] # no label for test

    
    target_size =  64 #32
    for label in range(5):
        os.chdir(root_dir+'/data/train_128/'+str(label))
        data_train = glob.glob('*')
        try:
            for name in data_train:
                pic = imread(name)
                resize_pic = imresize(pic,(target_size,target_size))
                train_data.append(resize_pic)
                train_label.append(label)
        except BaseException:
            print('Something went wrong...')
            return None   

    os.chdir(root_dir+'/data/test_128')
    data_test = glob.glob('*')
    try:
        for name in data_test:
            pic = imread(name)
            resize_pic = imresize(pic,(target_size,target_size))
            test_data.append(resize_pic)
    except BaseException:
            print('Something went wrong...')
            return None    
    
    #train_data_re = crop_resize(train_data)
    #test_data_re = crop_resize(test_data)
    
    train_data = np.asarray(train_data)
    train_label = np.asarray(train_label)
    test_data = np.asarray(test_data)

    train_data,val_data,train_label,val_label = train_test_split(train_data, train_label, test_size = 0.25 , random_state = 42)
    os.chdir(root_dir)
    
    if mode == 'all':
        return train_data, train_label, val_data, val_label, test_data
    else:
        raise ValueError('Mode should be \'train\' or \'test\' or \'all\'')

        
        
#############################################
#############################################
#############   Crop & Resize ###############
#############################################  
'''
    One problem here is that the images are too large, which may lead to OOM issue.
    Since most of the bottles are located in the middle part of the images, I want to preprocess the images by:
    1. Crop the image to 64x64, only leave the middle part of the image
    2. Resize the 64x64 image to 32x32
'''
def crop_resize(X):
    # at first I will try to only resize the images
    # X is list now... 
    target_size = 32
    output = []
    for i in range(len(X)):
        output.append(imresize(imread(X[i]),size=(target_size,target_size)))
    return output





#############################################
#############   MODEL Processing ############
#############################################

class conv_layer(object):
    def __init__(self, input_x, in_channel, out_channel, kernel_shape, rand_seed, index=0):
        """
        :param input_x: The input of the conv layer. Should be a 4D array like (batch_num, img_len, img_len, channel_num)
        :param in_channel: The 4-th demension (channel number) of input matrix. For example, in_channel=3 means the input contains 3 channels.
        :param out_channel: The 4-th demension (channel number) of output matrix. For example, out_channel=5 means the output contains 5 channels (feature maps).
        :param kernel_shape: the shape of the kernel. For example, kernal_shape = 3 means you have a 3*3 kernel.
        :param rand_seed: An integer that presents the random seed used to generate the initial parameter value.
        :param index: The index of the layer. It is used for naming only.
        """
        assert len(input_x.shape) == 4 and input_x.shape[1] == input_x.shape[2] and input_x.shape[3] == in_channel

        with tf.variable_scope('conv_layer_%d' % index):
            with tf.name_scope('conv_kernel'):
                w_shape = [kernel_shape, kernel_shape, in_channel, out_channel]
                weight = tf.get_variable(name='conv_kernel_%d' % index, shape=w_shape,
                                         initializer=tf.glorot_uniform_initializer(seed=rand_seed))
                self.weight = weight

            with tf.variable_scope('conv_bias'):
                b_shape = [out_channel]
                bias = tf.get_variable(name='conv_bias_%d' % index, shape=b_shape,
                                       initializer=tf.glorot_uniform_initializer(seed=rand_seed))
                self.bias = bias

            # strides [1, x_movement, y_movement, 1]
            conv_out = tf.nn.conv2d(input_x, weight, strides=[1, 1, 1, 1], padding="SAME")
            cell_out = tf.nn.relu(conv_out + bias)

            self.cell_out = cell_out

            tf.summary.histogram('conv_layer/{}/kernel'.format(index), weight)
            tf.summary.histogram('conv_layer/{}/bias'.format(index), bias)

    def output(self):
        return self.cell_out


class max_pooling_layer(object):
    def __init__(self, input_x, k_size, padding="SAME"):
        """
        :param input_x: The input of the pooling layer.
        :param k_size: The kernel size you want to behave pooling action.
        :param padding: The padding setting. Read documents of tf.nn.max_pool for more information.
        """
        with tf.variable_scope('max_pooling'):
            # strides [1, k_size, k_size, 1]
            pooling_shape = [1, k_size, k_size, 1]
            cell_out = tf.nn.max_pool(input_x, strides=pooling_shape,
                                      ksize=pooling_shape, padding=padding)
            self.cell_out = cell_out

    def output(self):
        return self.cell_out


class norm_layer(object):
    def __init__(self, input_x,is_training):
        """
        :param input_x: The input that needed for normalization.
        :param is_training: To control the training or inference phase
        """
        with tf.variable_scope('batch_norm'):
            batch_mean, batch_variance = tf.nn.moments(input_x, axes=[0], keep_dims=True)
            ema = tf.train.ExponentialMovingAverage(decay=0.99)

            def True_fn():
                ema_op = ema.apply([batch_mean, batch_variance])
                with tf.control_dependencies([ema_op]):
                    return tf.identity(batch_mean), tf.identity(batch_variance)

            def False_fn():
                return ema.average(batch_mean), ema.average(batch_variance)

            mean, variance = tf.cond(is_training, True_fn, False_fn)

            cell_out = tf.nn.batch_normalization(input_x,
                                                 mean,
                                                 variance,
                                                 offset=None,
                                                 scale=None,
                                                 variance_epsilon=1e-6,
                                                 name=None)
            self.cell_out = cell_out

    def output(self):
        return self.cell_out


class fc_layer(object):
    def __init__(self, input_x, in_size, out_size, rand_seed, activation_function=None, index=0):
        """
        :param input_x: The input of the FC layer. It should be a flatten vector.
        :param in_size: The length of input vector.
        :param out_size: The length of output vector.
        :param rand_seed: An integer that presents the random seed used to generate the initial parameter value.
        :param keep_prob: The probability of dropout. Default set by 1.0 (no drop-out applied)
        :param activation_function: The activation function for the output. Default set to None.
        :param index: The index of the layer. It is used for naming only.

        """
        with tf.variable_scope('fc_layer_%d' % index):
            with tf.name_scope('fc_kernel'):
                w_shape = [in_size, out_size]
                weight = tf.get_variable(name='fc_kernel_%d' % index, shape=w_shape,
                                         initializer=tf.glorot_uniform_initializer(seed=rand_seed))
                self.weight = weight

            with tf.variable_scope('fc_kernel'):
                b_shape = [out_size]
                bias = tf.get_variable(name='fc_bias_%d' % index, shape=b_shape,
                                       initializer=tf.glorot_uniform_initializer(seed=rand_seed))
                self.bias = bias

            cell_out = tf.add(tf.matmul(input_x, weight), bias)
            if activation_function is not None:
                cell_out = activation_function(cell_out)

            self.cell_out = cell_out

            tf.summary.histogram('fc_layer/{}/kernel'.format(index), weight)
            tf.summary.histogram('fc_layer/{}/bias'.format(index), bias)

    def output(self):
        return self.cell_out


def LeNet(input_x, input_y, is_training,
          img_len=64, channel_num=3, output_size=5,
          conv_featmap=[6, 16], fc_units=[84],
          conv_kernel_size=[5, 5], pooling_size=[2, 2],
          l2_norm=0.01, seed=235):
    """
        LeNet is an early and famous CNN architecture for image classfication task.
        It is proposed by Yann LeCun. Here we use its architecture as the startpoint
        for your CNN practice. Its architecture is as follow.

        input >> Conv2DLayer >> Conv2DLayer >> flatten >>
        DenseLayer >> AffineLayer >> softmax loss >> output

        Or

        input >> [conv2d-maxpooling] >> [conv2d-maxpooling] >> flatten >>
        DenseLayer >> AffineLayer >> softmax loss >> output

        http://deeplearning.net/tutorial/lenet.html

    """

    assert len(conv_featmap) == len(conv_kernel_size) and len(conv_featmap) == len(pooling_size)

    # conv layer 0
    conv_layer_0 = conv_layer(input_x=input_x,
                              in_channel=channel_num,
                              out_channel=conv_featmap[0],
                              kernel_shape=conv_kernel_size[0],
                              rand_seed=seed, index = 0)
    # Add batch normalization, I dont understand why in sample code there is a Norm_layer class, but the code never calls it 
    norm_layer_0 = norm_layer(conv_layer_0.output(),is_training)
    #Sub-sampling
    pooling_layer_0 = max_pooling_layer(input_x=norm_layer_0.output(),
                                        k_size=pooling_size[0],
                                        padding="VALID")

    # conv layer 1 , the same, there should be two conv layers in LENET, but in sample code there is only one...
    conv_layer_1 = conv_layer(input_x=pooling_layer_0.output(),
                              in_channel=pooling_layer_0.output().shape[3],
                              out_channel=conv_featmap[1],
                              kernel_shape=conv_kernel_size[1],
                              rand_seed=seed, index = 1)
    # batch normalization
    norm_layer_1 = norm_layer(conv_layer_1.output(),is_training)
    pooling_layer_1 = max_pooling_layer(input_x=norm_layer_1.output(),
                                        k_size=pooling_size[1],
                                        padding="VALID")
    # flatten
    pool_shape = pooling_layer_1.output().get_shape()
    img_vector_length = pool_shape[1].value * pool_shape[2].value * pool_shape[3].value
    flatten = tf.reshape(pooling_layer_1.output(), shape=[-1, img_vector_length])

    # fc layer
    fc_layer_0 = fc_layer(input_x=flatten,
                          in_size=img_vector_length,
                          out_size=fc_units[0],
                          rand_seed=seed,
                          activation_function=tf.nn.relu,
                          index=0)
    # Batch normalization
    norm_layer_2 = norm_layer(fc_layer_0.output(),is_training)
    
    fc_layer_1 = fc_layer(input_x=norm_layer_2.output(),
                          in_size=fc_units[0],
                          out_size=output_size,
                          rand_seed=seed,
                          activation_function=None,
                          index=1)

    # saving the parameters for l2_norm loss
    conv_w = [conv_layer_0.weight,conv_layer_1.weight]
    fc_w = [fc_layer_0.weight, fc_layer_1.weight]

    # loss
    with tf.name_scope("loss"):
        l2_loss = tf.reduce_sum([tf.norm(w) for w in fc_w])
        l2_loss += tf.reduce_sum([tf.reduce_sum(tf.norm(w, axis=[-2, -1])) for w in conv_w])

        label = tf.one_hot(input_y, 5)
        cross_entropy_loss = tf.reduce_mean(
            tf.nn.softmax_cross_entropy_with_logits(labels=label, logits=fc_layer_1.output()),
            name='cross_entropy')
        loss = tf.add(cross_entropy_loss, l2_norm * l2_loss, name='loss')

        tf.summary.scalar('LeNet_loss', loss)

    return fc_layer_1.output(), loss


def cross_entropy(output, input_y):
    with tf.name_scope('cross_entropy'):
        label = tf.one_hot(input_y, 5)
        ce = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=label, logits=output))

    return ce


def train_step(loss, learning_rate=1e-3):
    with tf.name_scope('train_step'):
        #step = tf.train.GradientDescentOptimizer(learning_rate).minimize(loss)
        step = tf.train.AdamOptimizer(learning_rate).minimize(loss)
        #step = tf.train.RMSPropOptimizer(learning_rate).minimize(loss)
        #I cannot find NADAM in tf.train...
    return step


def evaluate(output, input_y):
    with tf.name_scope('evaluate'):
        pred = tf.argmax(output, axis=1)
        error_num = tf.count_nonzero(pred - input_y, name='error_num')
        tf.summary.scalar('LeNet_error_num', error_num)
    return error_num


def prediction(output):
    with tf.name_scope('prediction'):
        pred = tf.argmax(output, axis = 1)
        print(output.shape)
    return pred


def my_training(X_train, y_train, X_val, y_val,X_test,y_test,
             conv_featmap=[6],
             fc_units=[84],
             conv_kernel_size=[5],
             pooling_size=[2],
             l2_norm=0.01,
             seed=235,
             learning_rate=1e-2,
             epoch=20,
             batch_size=245,
             verbose=False,
             pre_trained_model=None):
    print("Building my LeNet. Parameters: ")
    print("conv_featmap={}".format(conv_featmap))
    print("fc_units={}".format(fc_units))
    print("conv_kernel_size={}".format(conv_kernel_size))
    print("pooling_size={}".format(pooling_size))
    print("l2_norm={}".format(l2_norm))
    print("seed={}".format(seed))
    print("learning_rate={}".format(learning_rate))

    # define the variables and parameter needed during training
    with tf.name_scope('inputs'):
        xs = tf.placeholder(shape=[None, 64, 64, 3], dtype=tf.float32)
        ys = tf.placeholder(shape=[None, ], dtype=tf.int64)
        is_training = tf.placeholder(tf.bool, name='is_training')

    output, loss = LeNet(xs, ys, is_training,
                         img_len=64,
                         channel_num=3,
                         output_size=5,
                         conv_featmap=conv_featmap,
                         fc_units=fc_units,
                         conv_kernel_size=conv_kernel_size,
                         pooling_size=pooling_size,
                         l2_norm=l2_norm,
                         seed=seed)

    iters = int(X_train.shape[0] / batch_size)
    print('number of batches for training: {}'.format(iters))

    step = train_step(loss,learning_rate) 
    # One funny thing is in sample code (step = train_step(loss))
    #it did not pass the learning rate to train_step fcn
    #which means no matter how we tune the lr , the code itself wont have any change lol
    eve = evaluate(output, ys)
    
    pred = prediction(output)
    
    iter_total = 0
    best_acc = 0
    cur_model_name = 'lenet_{}'.format(int(time.time()))

    with tf.Session() as sess:
        merge = tf.summary.merge_all()

        writer = tf.summary.FileWriter("log/{}".format(cur_model_name), sess.graph)
        saver = tf.train.Saver()
        sess.run(tf.global_variables_initializer())

        # try to restore the pre_trained
        if pre_trained_model is not None:
            try:
                print("Load the model from: {}".format(pre_trained_model))
                saver.restore(sess, 'model/{}'.format(pre_trained_model))
            except Exception:
                raise ValueError("Load model Failed!")

        for epc in range(epoch):
            print("epoch {} ".format(epc + 1))

            for itr in range(iters):
                iter_total += 1

                training_batch_x = X_train[itr * batch_size: (1 + itr) * batch_size]
                training_batch_y = y_train[itr * batch_size: (1 + itr) * batch_size]

                _, cur_loss = sess.run([step, loss], feed_dict={xs: training_batch_x,
                                                                ys: training_batch_y,
                                                                is_training: True})

                if iter_total % 100 == 0:
                    # do validation
                    valid_eve, merge_result = sess.run([eve, merge], feed_dict={xs: X_val,
                                                                                ys: y_val,
                                                                                is_training: False})
                    valid_acc = 100 - valid_eve * 100 / y_val.shape[0]
                    if verbose:
                        print('{}/{} loss: {} validation accuracy : {}%'.format(
                            batch_size * (itr + 1),
                            X_train.shape[0],
                            cur_loss,
                            valid_acc))

                    # save the merge result summary
                    writer.add_summary(merge_result, iter_total)

                    # when achieve the best validation accuracy, we store the model paramters
                    if valid_acc > best_acc:
                        print('Best validation accuracy! iteration:{} accuracy: {}%'.format(iter_total, valid_acc))
                        best_acc = valid_acc
                        saver.save(sess, 'model/{}'.format(cur_model_name))
                        y_test = sess.run(pred, feed_dict={xs: X_test,ys: y_test,is_training:False})
    print("Traning ends. The best valid accuracy is {}. Model named {}.".format(best_acc, cur_model_name))
    return y_test
