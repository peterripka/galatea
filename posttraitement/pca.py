import numpy
from scipy import linalg

def pca(X, num_components = numpy.inf, min_variance = .0):
    """
    Dimensionality reduction via Principal Component Analysis.
    """
    assert X.shape[1] <= X.shape[0]

    X -= numpy.mean (X, axis = 0)
    (U, s, Vh) = linalg.svd(X, full_matrices = False)
    vars = s ** 2
    var_filter = (vars / sum(vars)) >= min_variance
    num_components = min(num_components, X.shape[1], sum(var_filter))
    S = linalg.diagsvd(s[var_filter][:num_components], U.shape[1], num_components)

    return numpy.dot(U, S)

if __name__ == "__main__":
    import argparse
    from dense.dA import dA
    from dense.logistic_sgd import load_data, get_constant
    import theano

    parser = argparse.ArgumentParser(
        description="Transform the output of a model by Principal Component Analysis"
    )
    parser.add_argument('dataset', action = 'store',
                        type = str,
                        choices = ['avicenna', 'harry', 'rita', 'sylvester',
                                 'ule'],
                        help = 'Dataset on which to run the PCA')
    parser.add_argument('-d', '--load-dir', action = 'store',
                        type = str,
                        default = ".",
                        required = False,
                        help = "Directory from which to load model.pkl")
    parser.add_argument('-n', '--num-components', action = 'store',
                        type = int,
                        default = numpy.inf,
                        required = False,
                        help = "Only the 'n' most important components will be preserved")
    parser.add_argument('-v', '--min-variance', action = 'store',
                        type = float,
                        default = .0,
                        required = False,
                        help = "Components with variance below this threshold will be discarded")
    args = parser.parse_args()

    # Load model
    da = dA()
    da.load(args.load_dir)

    # Load dataset
    data = load_data(args.dataset)
    print >> sys.stderr, "Dataset shapes:", map(lambda(x): get_constant(x.shape), data)

    def get_subset_rep (index):
        d = theano.tensor.matrix('input')
        return theano.function([], da.get_hidden_values(d), givens = {d:data[index]})()
    reps = map(get_subset_rep, range(3))

    print "Computing PCA..."
    [train_pca, valid_pca, test_pca] = [pca(subset, args.num_components, args.min_variance) for subset in reps]
    
    print "Some stats:"
    print "\t", map(numpy.shape, [train_pca, valid_pca, test_pca])
    map(lambda((f, d)): numpy.savetxt(f, d), zip(map (lambda(s): s + "_pca.csv", ["train", "valid", "test"]), [train_pca, valid_pca, test_pca]))
