import tensorflow as tf
import numpy as np
import time
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical

# Use TF 1.x compatibility
tf.compat.v1.disable_eager_execution()

# Load MNIST dataset
(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train = x_train.reshape(-1, 28, 28, 1).astype('float32') / 255.0
x_test  = x_test.reshape(-1, 28, 28, 1).astype('float32') / 255.0
y_train = to_categorical(y_train, 10)
y_test  = to_categorical(y_test, 10)

# Build model
input_tensor = tf.compat.v1.placeholder(tf.float32, shape=[None, 28, 28, 1], name='input')
labels = tf.compat.v1.placeholder(tf.float32, shape=[None, 10], name='labels')

net = tf.compat.v1.layers.conv2d(input_tensor, 32, (3, 3), activation=tf.nn.relu)
net = tf.compat.v1.layers.max_pooling2d(net, (2, 2), (2, 2))
net = tf.compat.v1.layers.conv2d(net, 64, (3, 3), activation=tf.nn.relu)
net = tf.compat.v1.layers.max_pooling2d(net, (2, 2), (2, 2))
net = tf.compat.v1.layers.flatten(net)
net = tf.compat.v1.layers.dense(net, 128, activation=tf.nn.relu)
logits = tf.compat.v1.layers.dense(net, 10, activation=None)
logits = tf.identity(logits, name='logits')

loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=labels, logits=logits))
train_op = tf.compat.v1.train.AdamOptimizer().minimize(loss)
correct = tf.equal(tf.argmax(logits, 1), tf.argmax(labels, 1))
accuracy = tf.reduce_mean(tf.cast(correct, tf.float32))

# Training and timing
with tf.compat.v1.Session() as sess:
    sess.run(tf.compat.v1.global_variables_initializer())
    print("\nTraining model...")
    for epoch in range(5):
        for i in range(0, len(x_train), 64):
            x_batch = x_train[i:i+64]
            y_batch = y_train[i:i+64]
            sess.run(train_op, feed_dict={input_tensor: x_batch, labels: y_batch})
        acc = sess.run(accuracy, feed_dict={input_tensor: x_test, labels: y_test})
        print(f"Epoch {epoch+1}, Accuracy: {acc:.4f}")

    # Freeze graph
    output_graph_def = tf.compat.v1.graph_util.convert_variables_to_constants(
        sess,
        sess.graph_def,
        output_node_names=['logits']
    )
    with tf.io.gfile.GFile('model_DigitRecognition.pb', 'wb') as f:
        f.write(output_graph_def.SerializeToString())
    print("\nSaved frozen model as model_DigitRecognition.pb")

    # CPU inference timing
    print("\nRunning inference on CPU...")
    num_images = 1000
    start = time.perf_counter()
    for i in range(num_images):
        _ = sess.run(logits, feed_dict={input_tensor: x_test[i:i+1]})
    end = time.perf_counter()

    total_time = (end - start) * 1000  # ms
    avg_time = total_time / num_images
    fps = 1000 / avg_time

    print("\n--- CPU Performance ---")
    print(f"Total time: {total_time:.2f} ms")
    print(f"Avg inference time: {avg_time:.3f} ms")
    print(f"Throughput: {fps:.2f} FPS")
