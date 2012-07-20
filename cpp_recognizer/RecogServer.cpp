#include <iostream>
#include <vector>
#include <string>

#include <boost/algorithm/string/predicate.hpp>
#include <boost/filesystem.hpp>
#include <boost/foreach.hpp>

#include "opencv2/core/core.hpp"
#include "opencv2/contrib/contrib.hpp"
#include "opencv2/highgui/highgui.hpp"

using namespace std;
using namespace cv;
using namespace boost::algorithm;
using namespace boost::filesystem;

#define foreach BOOST_FOREACH


const int RECOG_SIZE = 32;
const int NUM_PIXELS = RECOG_SIZE * RECOG_SIZE;

Mat rescale(const Mat& m) {
    Mat scaled(RECOG_SIZE, RECOG_SIZE, CV_8UC1);
    resize(m, scaled, Size(RECOG_SIZE, RECOG_SIZE), 0, 0, INTER_LINEAR);
    return scaled;
}

Mat read_mat() {
    return Mat();
}

void run_server(FaceRecognizer& model) {
    char data[NUM_PIXELS];
    Mat image(RECOG_SIZE, RECOG_SIZE, CV_8UC1, data);
    int predictedLabel = 12345;
    double confidence = 0.12345;
    while (cin.read(data, NUM_PIXELS).gcount() == NUM_PIXELS) {
        cerr << "predicting... " << flush;
        model.predict(image, predictedLabel, confidence);
        cout << predictedLabel << endl << confidence << endl << flush;
        cerr << "label: " << predictedLabel << ", confidence: " << confidence << endl;
    }
}

int main(int const argc, char const * const * const argv) {
    vector<Mat> images, test_images;
    vector<int> labels, test_labels;

    {
        int i = 0;
        foreach (const char* dirname, make_pair(argv + 1, argv + argc)) {
            cerr << "Label " << i << ": " << dirname << " ..." << flush;
            int ct = 0;
            foreach (const directory_entry& entry, make_pair(directory_iterator(dirname), directory_iterator())) {
                const char* filename = entry.path().c_str();
                if (ends_with(filename, "1.pgm")) {
                    (ct % 10 ? images : test_images).push_back(rescale(imread(filename, CV_LOAD_IMAGE_GRAYSCALE)));
                    (ct % 10 ? labels : test_labels).push_back(i);
                    ct ++;
                }
            }
            cerr << ct << " images." << endl;
            ++ i;
        }
    }

    /*
    namedWindow("yay", CV_WINDOW_AUTOSIZE);
    foreach (const Mat& im, images) {
        imshow("yay", im);
        waitKey(0);
    }
    */

    cerr << "training model..." << flush;
    Ptr<FaceRecognizer> model = createLBPHFaceRecognizer();
    model->train(images, labels);
    cerr << "done." << endl; 

    cerr << "testing model:" << endl;
    int predictedLabel = 12345;
    double confidence = 0.12345;
    for (int i = 0; i < test_images.size(); i ++) {
        cerr << i << ": " << test_labels[i] << "->";
        model->predict(test_images[i], predictedLabel, confidence);
        cerr << predictedLabel << " " << confidence << endl;
    }

    cerr << "waiting for input..." << endl;
    run_server(*model);
    cerr << "done." << endl;

    return 0;
}

