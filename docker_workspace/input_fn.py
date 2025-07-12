import tensorflow as tf
import os

# Enable TensorFlow 1.x compatibility mode
tf.compat.v1.disable_eager_execution()

_R_MEAN = 123.68
_G_MEAN = 116.78
_B_MEAN = 103.94

class Data_loader(object):
  def __init__(self, out_height, out_width, smallest_side=256):
    self._sess = tf.compat.v1.Session()
    self._out_height = out_height
    self._out_width = out_width
    self._smallest_side = smallest_side

    self._decode_jpeg_data = tf.compat.v1.placeholder(dtype=tf.string)
    self._decode_jpeg = tf.image.decode_png(self._decode_jpeg_data, channels=1)

    self._image_pl = tf.compat.v1.placeholder(tf.float32, shape=(None, None, 1))
    self._resized_image = self._aspect_preserving_resize(self._image_pl, self._smallest_side)

  def _center_crop(self, image):
    image_height, image_width = image.shape[:2]
    offset_height = (image_height - self._out_height) // 2
    offset_width = (image_width - self._out_width) // 2
    image = image[offset_height:offset_height + self._out_height,
                  offset_width:offset_width + self._out_width, :]
    return image

  def _smallest_size_at_least(self, height, width, smallest_side):
    smallest_side = tf.convert_to_tensor(smallest_side, dtype=tf.int32)

    height = tf.cast(height, tf.float32)
    width = tf.cast(width, tf.float32)
    smallest_side = tf.cast(smallest_side, tf.float32)

    scale = tf.cond(tf.greater(height, width),
                    lambda: smallest_side / width,
                    lambda: smallest_side / height)
    new_height = tf.cast(tf.math.rint(height * scale), tf.int32)
    new_width = tf.cast(tf.math.rint(width * scale), tf.int32)
    return new_height, new_width

  def _aspect_preserving_resize(self, image, smallest_side):
    smallest_side = tf.convert_to_tensor(smallest_side, dtype=tf.int32)
    shape = tf.shape(image)
    height = shape[0]
    width = shape[1]
    new_height, new_width = self._smallest_size_at_least(height, width, smallest_side)
    image = tf.expand_dims(image, 0)
    resized_image = tf.image.resize(image, [new_height, new_width], method='bilinear')
    resized_image = tf.squeeze(resized_image)
    return resized_image

  def preprocess(self, image):
    assert image is not None, "image cannot be None"
    resized_image = self._sess.run(self._resized_image, feed_dict={self._image_pl: image})
    image_crop = self._center_crop(resized_image)
    image = image_crop - [_R_MEAN, _G_MEAN, _B_MEAN]
    return image

  def load_image(self, img_path):
    assert os.path.exists(img_path), img_path + ' does not exist!'
    image_data = tf.io.gfile.GFile(img_path, 'rb').read()
    image = self._sess.run(self._decode_jpeg, feed_dict={self._decode_jpeg_data: image_data})
    assert len(image.shape) == 3
    assert image.shape[-1] == 1
    return image

calib_image_dir = "./calib_images/"
calib_image_list = "./labels.txt"
calib_batch_size = 50
input_height = 28
input_width = 28

def calib_input(iter):
  images = []
  data_loader = Data_loader(input_height, input_width)
  line = open(calib_image_list).readlines()
  for index in range(0, calib_batch_size):
    curline = line[iter * calib_batch_size + index]
    calib_image_name = curline.strip()
    filename = os.path.join(calib_image_dir, calib_image_name)
    image = data_loader.load_image(filename)
    #image = data_loader.preprocess(image)
    images.append(image.tolist())
  return {"x": images}

if __name__ == "__main__":
    result = calib_input(0)
    print("Batch shape:", len(result["input"]))
    print("First image shape:", len(result["input"][0]), "x", len(result["input"][0][0]))
