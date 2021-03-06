from pylearn2.utils import serial
from pylearn2.config import yaml_parse
import sys

model_paths = sys.argv[1:]

class Committee(object):

    def set_batch_size(self, batch_size):
        for member in self.members:
            member.set_batch_size(batch_size)

    def get_input_space(self):
        return self.members[0].get_input_space()

    def get_output_space(self):
        return self.members[0].get_output_space()

    def __init__(self):
        self.members = []

    def fprop(self, state_below):
        states = [member.fprop(state_below) for member in self.members]
        state = sum(states)
        return state

model = Committee()

for model_path in model_paths:
    submodel = serial.load(model_path)
    model.members.append(submodel)

src = model.members[0].dataset_yaml_src
batch_size = 100
model.set_batch_size(batch_size)


assert src.find('train') != -1
test = yaml_parse.load(src)
x = raw_input("use test set? ")
if x == 'y':
    test = test.get_test_set()
    assert test.X.shape[0] == 10000
else:
    assert x == 'n'

if x == 'y':
    if not (test.X.shape[0] == 10000):
        print test.X.shape[0]
        assert False
else:
    # compute the train accuracy on what the model
    # was trained on, not the entire train set
    assert test.X.shape[0] in [40000,50000,60000]

test.X = test.X.astype('float32')
test.y = test.y.astype('float32')

import theano.tensor as T

Xb = model.get_input_space().make_batch_theano()
Xb.name = 'Xb'
yb = model.get_output_space().make_batch_theano()
yb.name = 'yb'

ymf = model.fprop(Xb)
ymf.name = 'ymf'

from theano import function

yl = T.argmax(yb,axis=1)

mf1acc = 1.-T.neq(yl , T.argmax(ymf,axis=1)).mean()

batch_acc = function([Xb,yb],[mf1acc])

# The averaging math assumes batches are all same size
assert test.X.shape[0] % batch_size == 0

def accs():
    mf1_accs = []
    assert isinstance(test.X.shape[0], int)
    assert isinstance(batch_size, int)
    for i in xrange(test.X.shape[0]/batch_size):
        print i
        x_arg = test.X[i*batch_size:(i+1)*batch_size,:]
        if Xb.ndim > 2:
            x_arg = test.get_topological_view(x_arg)
        mf1_accs.append( batch_acc(x_arg,
            test.y[i*batch_size:(i+1)*batch_size,:])[0])
    return sum(mf1_accs) / float(len(mf1_accs))


result = accs()


print 1. - result
