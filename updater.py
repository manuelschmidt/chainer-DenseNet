#!/usr/bin/env python
# -*- coding: utf-8 -*-

from chainer import optimizer as optimizer_module
from chainer import training
from chainer import variable
from chainer.dataset import iterator as iterator_module
from chainer.dataset import convert

import six


class StandardUpdater(training.StandardUpdater):

    def __init__(self, iterator, optimizer, batch_split=(1, 'mean'),
                 converter=convert.concat_examples,
                 device=None, loss_func=None):
        if isinstance(iterator, iterator_module.Iterator):
            iterator = {'main': iterator}
        self._iterators = iterator

        if isinstance(optimizer, optimizer_module.Optimizer):
            optimizer = {'main': optimizer}
        self._optimizers = optimizer

        self._split_size = batch_split[0]
        if batch_split[1] == 'mean':
            self._grad_divisor = self._split_size
        elif batch_split[1] == 'sum':
            self._grad_divisor = 1
        else:
            raise Exception('batch_split option is \'mean\' or \'sum\'')

        self.converter = converter
        self.loss_func = loss_func
        self.device = device
        self.iteration = 0

    def update_core(self):
        optimizer = self._optimizers['main']
        model = optimizer.target
        model.cleargrads()
        is_new_epoch = False

        for _ in six.moves.range(self._split_size):
            batch = self._iterators['main'].next()
            in_arrays = self.converter(batch, self.device)

            if self._iterators['main'].is_new_epoch:
                is_new_epoch = True
            self._iterators['main'].is_new_epoch = is_new_epoch

            in_vars = tuple(variable.Variable(x) for x in in_arrays)
            loss = model(*in_vars) / self._grad_divisor
            loss.backward()

        optimizer.update()
