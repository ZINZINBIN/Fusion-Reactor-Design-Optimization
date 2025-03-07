import numpy as np
from itertools import product
from config.search_space_info import search_space
from typing import Optional

class ActionSpace(object):
    def __init__(self, discvars, contexts, n_random:int = 128, buffer_size:int=256):

        # Get the name of the parameters
        self._action_keys = discvars.keys()
        self._context_keys = contexts.keys()

        # action space for random sampling
        self.random_state = np.random.RandomState()
        allActions = {}

        self.n_random = n_random
        self.bounds = np.zeros((len(self._action_keys), 2))

        for idx, param in enumerate(self._action_keys):
            p_min = search_space[param][0]
            p_max = search_space[param][1]
            allActions[param] = [p_min, p_max]

            self.bounds[idx,0] = p_min
            self.bounds[idx,1] = p_max

        self._allActions = allActions        
        self.buffer_size = buffer_size

        # preallocated memory for X and Y points
        self._context = np.empty(shape=(0, self.context_dim))
        self._action = np.empty(shape=(0, self.action_dim))
        self._context_action = np.empty(shape=(0, self.context_dim + self.action_dim))
        self._reward = np.empty(shape=(0))

    def __len__(self):
        assert len(self._action) == len(self._reward)
        assert len(self._action) == len(self._context)
        return len(self._reward)

    @property
    def empty(self):
        return len(self) == 0

    @property
    def context(self):
        return self._context

    @property
    def action(self):
        return self._action

    @property
    def context_action(self):
        return self._context_action

    @property
    def reward(self):
        return self._reward

    @property
    def context_dim(self):
        return len(self._context_keys)

    @property
    def action_dim(self):
        return len(self._action_keys)

    @property
    def context_keys(self):
        return self._context_keys

    @property
    def action_keys(self):
        return self._action_keys

    def action_to_array(self, action):
        try:
            assert set(action) == set(self._action_keys)
        except AssertionError:
            raise ValueError(
                "Parameters' keys ({}) do ".format(sorted(action))
                + "not match the expected set of keys ({}).".format(self._action_keys)
            )
        return np.asarray([action[key] for key in self._action_keys])

    def context_to_array(self, context):
        try:
            assert set(context) == set(self._context_keys)
        except AssertionError:
            raise ValueError(
                "Parameters' keys ({}) do ".format(sorted(context))
                + "not match the expected set of keys ({}).".format(self._context_keys)
            )
        return np.asarray([context[key] for key in self._context_keys])

    def array_to_action(self, x):
        try:
            assert len(x) == len(self._action_keys)
        except AssertionError:
            raise ValueError(
                "Size of array ({}) is different than the ".format(len(x))
                + "expected number of parameters ({}).".format(len(self._action_keys))
            )
        return dict(zip(self._action_keys, x))

    def array_to_context(self, x):
        try:
            assert len(x) == len(self._context_keys)
        except AssertionError:
            raise ValueError(
                "Size of array ({}) is different than the ".format(len(x))
                + "expected number of parameters ({}).".format(len(self._context_keys))
            )
        return dict(zip(self._context_keys, x))

    def register(self, context, action, reward):

        c = self.context_to_array(context)
        a = self.action_to_array(action)
        ca = np.concatenate([c.reshape(1, -1), a.reshape(1, -1)], axis=1)

        self._context = np.concatenate([self._context, c.reshape(1, -1)])
        self._action = np.concatenate([self._action, a.reshape(1, -1)])
        self._reward = np.concatenate([self._reward, [reward]])
        self._context_action = np.concatenate([self._context_action, ca.reshape(1, -1)])
        
        if len(self._context) > self.buffer_size:
            self._context = self._context[-self.buffer_size:]
            self._action = self._action[-self.buffer_size:]
            self._reward = self._reward[-self.buffer_size:]
            self._context_action = self._context_action[-self.buffer_size:]

    def res(self):
        """Get all reward values found and corresponding parametes."""
        context = [dict(zip(self._context_keys, p)) for p in self.context]
        action = [dict(zip(self._action_keys, p)) for p in self.action]

        return [
            {"reward": r, "action": a, "context": c}
            for r, a, c in zip(self.reward, action, context)
        ]
    
    def random_sample(self, n_sample:Optional[int] = None):
                
        if n_sample == None:
            n_sample = self.n_random
        
        return self.random_state.uniform(self.bounds[:,0], self.bounds[:,1], size = (n_sample, self.bounds.shape[0]))