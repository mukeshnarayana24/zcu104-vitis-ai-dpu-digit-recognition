#include <iostream>
#include <memory>
#include <opencv2/opencv.hpp>
#include <xir/graph/graph.hpp>
#include <vart/runner.hpp>
#include <vart/tensor_buffer.hpp>
#include <glog/logging.h>
#include <cmath>
#include <cstring>
#include <chrono>


class SimpleTensorBuffer : public vart::TensorBuffer {
public:
    SimpleTensorBuffer(const xir::Tensor* tensor)
        : vart::TensorBuffer(tensor), data_(new int8_t[tensor->get_element_num()]) {}

    std::pair<uint64_t, size_t> data(std::vector<int> = {}) override {
        return {
            reinterpret_cast<uint64_t>(data_.get()),
            tensor_->get_data_type().bit_width / 8 * tensor_->get_element_num()
        };
    }

private:
    std::unique_ptr<int8_t[]> data_;
};

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: ./mnist_dpu <model.xmodel> <image.png>" << std::endl;
        return -1;
    }

    std::string model_path = argv[1];
    std::string image_path = argv[2];

    auto graph = xir::Graph::deserialize(model_path);
    auto root = graph->get_root_subgraph();
    xir::Subgraph* dpu_subgraph = nullptr;
    for (auto c : root->get_children()) {
        if (c->has_attr("device") && c->get_attr<std::string>("device") == "DPU") {
            dpu_subgraph = c;
            break;
        }
    }

    CHECK(dpu_subgraph != nullptr) << "No DPU subgraph found.";

    auto runner = vart::Runner::create_runner(dpu_subgraph, "run");

    auto input_tensor = runner->get_input_tensors()[0];
    auto output_tensor = runner->get_output_tensors()[0];

    int height = input_tensor->get_shape()[1];
    int width = input_tensor->get_shape()[2];

    cv::Mat img = cv::imread(image_path, cv::IMREAD_GRAYSCALE);
    if (img.empty()) {
        std::cerr << "Failed to load image: " << image_path << std::endl;
        return -1;
    }

    cv::resize(img, img, cv::Size(width, height));
    img.convertTo(img, CV_8SC1);

    auto input_buffer = std::make_unique<SimpleTensorBuffer>(input_tensor);
    auto output_buffer = std::make_unique<SimpleTensorBuffer>(output_tensor);

    int8_t* input_data = reinterpret_cast<int8_t*>(input_buffer->data().first);
    std::memcpy(input_data, img.data, width * height);

    std::vector<vart::TensorBuffer*> inputs = {input_buffer.get()};
    std::vector<vart::TensorBuffer*> outputs = {output_buffer.get()};

    // Measure inference time
    auto start_time = std::chrono::high_resolution_clock::now();

    auto job_id = runner->execute_async(inputs, outputs);
    runner->wait(job_id.first, -1);

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration_us = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time).count();
    double duration_ms = duration_us / 1000.0;
    double fps = 1000.0 / duration_ms;

    int8_t* output_data = reinterpret_cast<int8_t*>(output_buffer->data().first);

    // Numerically stable softmax
    int8_t max_logit = output_data[0];
    for (int i = 1; i < 10; ++i) {
        if (output_data[i] > max_logit) {
            max_logit = output_data[i];
        }
    }

    float exp_sum = 0.0f;
    float probs[10];
    for (int i = 0; i < 10; ++i) {
        probs[i] = std::exp(static_cast<float>(output_data[i] - max_logit));
        exp_sum += probs[i];
    }

    int pred = 0;
    float max_prob = 0.0f;
    for (int i = 0; i < 10; ++i) {
        probs[i] /= exp_sum;
        if (probs[i] > max_prob) {
            max_prob = probs[i];
            pred = i;
        }
    }

    std::cout << "Predicted Digit: " << pred << std::endl;
    for (int i = 0; i < 10; ++i) {
        std::cout << "Class " << i << ": " << probs[i] << std::endl;
    }

    //performance metrics
    std::cout << "\n--- Performance Metrics ---" << std::endl;
    std::cout << "Inference Time: " << duration_ms << " ms" << std::endl;
    std::cout << "Throughput (FPS): " << fps << " frames/sec" << std::endl;

    return 0;
}

