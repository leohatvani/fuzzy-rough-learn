from functools import partial

import numpy as np

from ..utils import limit_and_sort

class OWAOperator():

    """
    Ordered Weighted Averaging (OWA) operator, which can be applied to an
    array to obtain its ordered weighted average. Intended specifically for
    dual pairs of OWA operators that approximate maxima and minima, which are
    encoded together in one object.

    Parameters
    ----------
    w : array shape=(n_weights, )
        Weights which define the OWA operator. The values should be in [0, 1]
        and sum to 1.

    max_like : bool
        Whether the weights in the order in which they are provided are to be
        used to approximate a maximum (True) or a minimum (False). The dual
        operator will then automatically be added by inversing the weight
        vector.

    name : str, default=None
        Name of the OWA operator to be displayed as its string representation.
        If None, the weight array will be displayed instead.
    """

    def __init__(self, w, *, max_like: bool, name: str = None):
        self.w = w
        self.k = len(w)
        self.max_like = max_like
        self.name = name

    @classmethod
    def from_function(cls, f, k: int, *, scale: bool = False, max_like: bool,
                      name: str = None):
        """
        Constructor to create an OWA operator from a function f and its length
        k.

        Parameters
        ----------
        f : int -> array shape=(k, )
            Generating function which takes an integer k and returns a valid
            weight vector of length k.

        k : int
            The length of the intended weight vector.

        max_like : bool
            Whether the weights generated by f are to be used to approximate a
            maximum (True) or a minimum (False). The dual operator will then
            automatically be added by inversing the weight vector.

        name : str, default=None
            Name of the OWA operator to be displayed as its string
            representation. If None, the weight array will be displayed
            instead.

        Returns
        -------
        operator : OWAOperator
            OWA operator initialised with the weight vector obtained by
            applying f to k.
        """
        w = f(k)
        if scale:
            w /= np.sum(w)
        name = '{name}({k})'.format(name=name, k=k)
        return cls(w, max_like=max_like, name=name)

    @classmethod
    def family(cls, f, *, scale: bool = False, max_like: bool,
               name: str = None):
        """
        Convenience method for defining OWA operators up to the length k of the
        weight vector.

        Parameters
        ----------
        f : int -> array shape=(k, )
            Generating function which takes an integer k and returns a valid
            weight vector of length k.

        max_like : bool
            Whether the weights generated by f are to be used to approximate a
            maximum (True) or a minimum (False). The dual operator will then
            automatically be added by inversing the weight vector.

        name : str, default=None
            Name of the OWA operator to be displayed as its string
            representation. If None, the weight array will be displayed
            instead.

        Returns
        -------
        constructor : k -> OWAOperator
            Constructor that takes an integer k and creates the OWA operator
            initialised with the weight vector obtained by applying f to k.
        """
        return partial(cls.from_function, f, scale=scale, max_like=max_like,
                       name=name)

    def __eq__(self, other):
        if isinstance(other, OWAOperator):
            return np.array_equal(self.w, other.w) and self.max_like == other.max_like
        return NotImplemented

    def __len__(self):
        return self.k

    def __str__(self):
        if self.name:
            return self.name.format(self.k)
        return str(self.w)

    def _apply(self, v, as_soft_max: bool):
        w = self.w if self.max_like and as_soft_max else np.flip(self.w)
        v = limit_and_sort(v, -self.k, -1) if as_soft_max else np.flip(limit_and_sort(v, self.k, -1))
        return np.sum(v * w, axis=-1)

    def soft_max(self, v):
        """
        Calculates the soft maximum of an array.

        Parameters
        ----------
        v : array shape=(n, )
            Input vector of values.

        Returns
        -------
        y : numeric
            Soft maximum of v.
        """
        return self._apply(v, as_soft_max=True)

    def soft_min(self, v):
        """
        Calculates the soft minimum of an array.

        Parameters
        ----------
        v : array shape=(n, )
            Input vector of values.

        Returns
        -------
        y : numeric
            Soft minimum of v.
        """
        return self._apply(v, as_soft_max=False)


strict = OWAOperator(np.ones(1), max_like=True, name='strict')

additive = OWAOperator.family(
    lambda k: 2 * np.arange(1, k + 1) / (k * (k + 1)),
    max_like=False, name='additive')

exponential = OWAOperator.family(
    lambda k: np.flip(2 ** np.arange(k) / (2 ** k - 1)) if k < 32 else np.cumprod(np.full(k, 0.5)),
    max_like=True, name='exponential')

invadd = OWAOperator.family(
    lambda k: 1 / (np.arange(1, k + 1) * np.sum(1 / np.arange(1, k + 1))),
    max_like=True, name='invadd')

mean = OWAOperator.family(
    lambda k: np.full(k, 1 / k),
    max_like=False, name='mean')

trimmed = OWAOperator.family(
    lambda k: np.append(np.zeros(k - 1), np.ones(1)),
    max_like=False, name='trimmed')
