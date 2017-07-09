from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import pandas as pd
import numpy as np
from tensorflow.contrib.learn.python.learn.datasets import base
from tensorflow.contrib.learn.python.learn.datasets.mnist import DataSet
import tensorflow as tf
import kaggle_mnist as km

mnist = km.custom_kaggle_mnist()


# five layers and their number of neurons (tha last layer has 10 softmax neurons)
L = 200
M = 10
N = 60
O = 30

# input X: 28x28 grayscale images, the first dimension (None) will index the images in the mini-batch
X = tf.placeholder(tf.float32, [None, 28, 28, 1])
# correct answers will go here
Y_ = tf.placeholder(tf.float32, [None, 10])
# weights W[784, 10]   784=28*28
W = tf.Variable(tf.zeros([784, 10]))
# biases b[10]
b = tf.Variable(tf.zeros([10]))


# Weights initialised with small random values between -0.2 and +0.2
# When using RELUs, make sure biases are initialised with small *positive* values for example 0.1 = tf.ones([K])/10
W1 = tf.Variable(tf.truncated_normal([784, L], stddev=0.1))  # 784 = 28 * 28
B1 = tf.Variable(tf.zeros([L]))
W2 = tf.Variable(tf.truncated_normal([L, 10], stddev=0.1))
B2 = tf.Variable(tf.zeros([M]))

# flatten the images into a single line of pixels
# -1 in the shape definition means "the only possible dimension that will preserve the number of elements"
XX = tf.reshape(X, [-1, 784])
Y1 = tf.nn.sigmoid(tf.matmul(XX, W1) + B1)
Ylogits = tf.matmul(Y1, W2) + B2
Y = tf.nn.softmax(Ylogits)

# cross-entropy
# log takes the log of each element, * multiplies the tensors element by element
# reduce_mean will add all the components in the tensor
# so here we end up with the total cross-entropy for all images in the batch
# cross_entropy = -tf.reduce_mean(Y_ * tf.log(Y)) * 1000.0  # normalized for batches of 100 images,
# *10 because  "mean" included an unwanted division by 10


cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=Ylogits, labels=Y_)
cross_entropy = tf.reduce_mean(cross_entropy)*100

# accuracy of the trained model, between 0 (worst) and 1 (best)
correct_prediction = tf.equal(tf.argmax(Y, 1), tf.argmax(Y_, 1))
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

# training, learning rate = 0.005
train_step = tf.train.GradientDescentOptimizer(0.005).minimize(cross_entropy)


sess = tf.InteractiveSession()

tf.global_variables_initializer().run()

# Train (10, 100, 1000)
BATCH_SIZE = 100
EPOCH_NUMBER = 10
RANGE_SIZE = int(EPOCH_NUMBER * km.TRAIN_SIZE/BATCH_SIZE)
for index in range(RANGE_SIZE):
    batch_xs, batch_ys = mnist.train.next_batch(BATCH_SIZE)
    _accuracy, _train_step = sess.run([accuracy, train_step], feed_dict={X: batch_xs, Y_: batch_ys})

    if index%(km.TRAIN_SIZE/BATCH_SIZE) == 0:
        print("Epoch {}, training accuracy: {}".format(int(1+index/(km.TRAIN_SIZE/BATCH_SIZE)), _accuracy))

print("Validation accuracy: {}".format(sess.run(accuracy, feed_dict={X: mnist.validation.images,
                                    Y_: mnist.validation.labels})))
# Test trained model before submission
print("Validation accuracy: {}".format(sess.run(accuracy, feed_dict={X: mnist.test.images,
                                    Y_: mnist.test.labels})))

# kaggle test data
if km.DOWNLOAD_DATASETS:
    base.maybe_download(km.KAGGLE_TEST_CSV, km.DATA_DIR, km.SOURCE_URL + km.KAGGLE_TEST_CSV)
kaggle_test_images = pd.read_csv(km.DATA_DIR + km.KAGGLE_TEST_CSV).values.astype('float32')
kaggle_test_images = np.reshape(kaggle_test_images, (kaggle_test_images.shape[0], 28, 28, 1))

# convert from [0:255] => [0.0:1.0]
kaggle_test_images = np.multiply(kaggle_test_images, 1.0 / 255.0)

predictions_kaggle = sess.run(tf.argmax(tf.nn.softmax(Y), 1), feed_dict={X: kaggle_test_images})

with open(km.SUBMISSION_FILE, 'w') as submission:
    submission.write('ImageId,Label\n')
    for index, prediction in enumerate(predictions_kaggle):
        submission.write('{0},{1}\n'.format(index + 1, prediction))
    print("prediction submission written to {0}".format(km.SUBMISSION_FILE))
