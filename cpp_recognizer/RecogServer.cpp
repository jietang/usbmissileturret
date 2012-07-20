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

void run_server(vector<Ptr<FaceRecognizer> >& models) {
    char data[NUM_PIXELS];
    Mat image(RECOG_SIZE, RECOG_SIZE, CV_8UC1, data);
    int predictedLabel = 12345;
    double confidence = 0.12345;
    while (cin.read(data, NUM_PIXELS).gcount() == NUM_PIXELS) {
        cerr << "predicting..." << flush;
        foreach (Ptr<FaceRecognizer>& model, models) {
            model->predict(image, predictedLabel, confidence);
            cout << predictedLabel << endl << confidence << endl << flush;
        }
        cerr << "done" << endl;
    }
}

int main(int const argc, char const * const * const argv) {
    vector<Mat> images;
    vector<int> labels;

    {
        int i = 0;
        foreach (const char* dirname, make_pair(argv + 1, argv + argc)) {
            cerr << "Label " << i << ": " << dirname << " ..." << flush;
            int ct = 0;
            foreach (const directory_entry& entry, make_pair(directory_iterator(dirname), directory_iterator())) {
                const char* filename = entry.path().c_str();
                if (ends_with(filename, ".pgm")) {
                    images.push_back(rescale(imread(filename, CV_LOAD_IMAGE_GRAYSCALE)));
                    labels.push_back(i);
                    ct ++;
                }
            }
            cerr << ct << " images." << endl;
            ++ i;
        }
    }

    cerr << "training models..." << flush;
    vector<Ptr<FaceRecognizer> > models;
    models.push_back(createEigenFaceRecognizer());
    models.push_back(createFisherFaceRecognizer());
    models.push_back(createLBPHFaceRecognizer());
    foreach (Ptr<FaceRecognizer>& model, models)
        model->train(images, labels);
    cerr << "done." << endl; 

    cerr << "waiting for input..." << endl;
    run_server(models);
    cerr << "done." << endl;

    return 0;
}

