import numpy as np
import matplotlib.pyplot as plt

from skimage.segmentation import mark_boundaries
from sklearn.svm import LinearSVC

from sklearn.cross_validation import LeavePLabelOut
from sklearn.grid_search import GridSearchCV
from sklearn.utils import shuffle
from sklearn.metrics import recall_score, Scorer

from pascal_helpers import (load_pascal, load_image, cmap, eval_on_pixels,
                            load_kraehenbuehl, eval_on_sp, gt_in_sp,
                            get_ground_truth, load_pascal_pixelwise)

#from msrc_helpers import SimpleSplitCV

from IPython.core.debugger import Tracer
tracer = Tracer()
np.set_printoptions(precision=2)


def train_svm(C=0.1):
    data_train = load_pascal()
    svm = LinearSVC(C=C, dual=False, class_weight='auto')
    X, y = shuffle(data_train.X, data_train.Y)
    # prepare leave-one-label-out by assigning labels to images
    image_indicators = np.hstack([np.repeat(i, len(x)) for i, x in
                                  enumerate(X)])
    # go down to only 5 "folds"
    labels = image_indicators % 5
    X, y = np.vstack(X), np.hstack(y)
    #X_train, X_test, y_train, y_test = train_test_split(
        #data_train.X, data_train.Y, random_state=0)

    #X_train, y_train = np.vstack(X_train), np.hstack(y_train)
    #X_test, y_test = np.vstack(X_test), np.hstack(y_test)
    #n_test = len(X) // 5
    #n_train = len(X) - n_test
    #cv = SimpleSplitCV(n_train, n_test)
    cv = LeavePLabelOut(labels=labels, p=1)
    param_grid = {'C': 10. ** np.arange(-3, 3)}
    scorer = Scorer(recall_score, average="macro")
    grid_search = GridSearchCV(svm, param_grid=param_grid, cv=cv, verbose=10,
                               scoring=scorer, n_jobs=-1)
    grid_search.fit(X, y)

    tracer()

    #svm.fit(X, y)
    #print(svm.score(X, y))
    #eval_on_sp(data_train, [svm.predict(x) for x in data_train.X],
               #print_results=True)

    #data_val = load_pascal("val")
    #eval_on_sp(data_val, [svm.predict(x) for x in data_val.X],
               #print_results=True)
    tracer()


def visualize_pascal(plot_probabilities=False):
    data = load_pascal('val')
    for x, y, f, sps in zip(data.X, data.Y, data.file_names, data.superpixels):
        fig, ax = plt.subplots(2, 3)
        ax = ax.ravel()
        image = load_image(f)
        y_pixel = get_ground_truth(f)
        x_raw = load_kraehenbuehl(f)

        boundary_image = mark_boundaries(image, sps)

        ax[0].imshow(image)
        ax[1].imshow(y_pixel, cmap=cmap)
        ax[2].imshow(boundary_image)
        ax[3].imshow(np.argmax(x_raw, axis=-1), cmap=cmap, vmin=0, vmax=256)
        ax[4].imshow(y[sps], cmap=cmap, vmin=0, vmax=256)
        ax[5].imshow(np.argmax(x, axis=-1)[sps], cmap=cmap, vmin=0, vmax=256)
        for a in ax:
            a.set_xticks(())
            a.set_yticks(())
        plt.savefig("figures_pascal_val/%s.png" % f, bbox_inches='tight')
        plt.close()
        if plot_probabilities:
            fig, ax = plt.subplots(3, 7)
            for k in range(21):
                ax.ravel()[k].matshow(x[:, :, k], vmin=0, vmax=1)
            for a in ax.ravel():
                a.set_xticks(())
                a.set_yticks(())
            plt.savefig("figures_pascal_val/%s_prob.png" % f,
                        bbox_inches='tight')
            plt.close()
    tracer()


def eval_pixel_prediction():
    data = load_pascal_pixelwise('val')
    predictions = [np.argmax(x, axis=-1) for x in data.X]
    hamming, jaccard = eval_on_pixels(data.Y, predictions, print_results=True)
    tracer()


def eval_sp_prediction():
    data = load_pascal('val')
    predictions = [np.argmax(x, axis=-1) for x in data.X]
    hamming, jaccard = eval_on_sp(data, predictions, print_results=True)
    tracer()


def eval_pixel_best_possible():
    data = load_pascal('val')
    Y_on_sp = [gt_in_sp(f, sp) for f, sp in zip(data.file_names,
                                                data.superpixels)]
    hamming, jaccard = eval_on_sp(data, Y_on_sp, print_results=True)
    tracer()

if __name__ == "__main__":
    #visualize_pascal()
    #eval_pixel_best_possible()
    #eval_pixel_prediction()
    #eval_sp_prediction()
    train_svm(C=1)
