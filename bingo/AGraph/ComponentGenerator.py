"""Component Generator for Agraph equations.

This module covers the random generation of components of an Acyclic graph
command stack. It can generate full commands or sub-components such as
operators, terminals, and their associated parameters.
"""
import logging
import numbers
import numpy as np

from ..Util.ProbabilityMassFunction import ProbabilityMassFunction

LOGGER = logging.getLogger(__name__)


class ComponentGenerator:
    """Generates commands or components of a command for an AGraph stack

    Parameters
    ----------
    input_x_dimension : int
                        number of independent variables
    num_initial_load_statements : int
                                  number of commands at the beginning of stack
                                  which are required to be "load" commands
    terminal_probability : float [0.0-1.0]
                           probability that a new node will be a terminal
    constant_probability : float [0.0-1.0]
                           probability that a new terminal will be a constant
    """

    def __init__(self, input_x_dimension, num_initial_load_statements=1,
                 terminal_probability=0.1,
                 constant_probability=None):
        self._check_valid_init_params(constant_probability,
                                      input_x_dimension,
                                      num_initial_load_statements,
                                      terminal_probability)

        self._input_x_dimension = input_x_dimension
        self._num_initial_load_statements = num_initial_load_statements

        self._terminal_pmf = self._make_terminal_pdf(constant_probability)
        self._operator_pmf = ProbabilityMassFunction()
        self._random_command_function_pmf = \
            self._make_random_command_pmf(terminal_probability)

    @staticmethod
    def _check_valid_init_params(constant_probability, input_x_dimension,
                                 num_initial_load_statements,
                                 terminal_probability):
        ComponentGenerator._check_valid_x_dimension(input_x_dimension)
        ComponentGenerator._check_valid_num_loads(num_initial_load_statements)
        ComponentGenerator._check_valid_probability(terminal_probability)
        if constant_probability is not None:
            ComponentGenerator._check_valid_probability(constant_probability)

    @staticmethod
    def _check_valid_x_dimension(x_dimension):
        if not isinstance(x_dimension, int):
            LOGGER.error("Initialization of Agraph.ComponentGenerator with "
                         "non-integer x-dimension")
            LOGGER.error("input_x_dimension = %s", x_dimension)
            raise TypeError
        if x_dimension < 0:
            LOGGER.error("Initialization of Agraph.ComponentGenerator with "
                         "negative x-dimesnion.")
            LOGGER.error("input_x_dimension = %s", x_dimension)
            raise ValueError

    @staticmethod
    def _check_valid_num_loads(num_loads):
        if not isinstance(num_loads, int):
            LOGGER.error("Initialization of Agraph.ComponentGenerator with "
                         "non-integer number of load statements")
            LOGGER.error("num_initial_load_statements = %s", num_loads)
            raise TypeError
        if num_loads < 1:
            LOGGER.error("Initialization of Agraph.ComponentGenerator with "
                         "non-positive load statements, must be >= 1.")
            LOGGER.error("num_initial_load_statements = %s", num_loads)
            raise ValueError

    @staticmethod
    def _check_valid_probability(probability):
        if not isinstance(probability, numbers.Number):
            LOGGER.error("Initialization of Agraph.ComponentGenerator with "
                         "non-numeric probability")
            LOGGER.error("probability = %s", probability)
            raise TypeError
        if probability > 1.0 or probability < 0.0:
            LOGGER.error("Initialization of Agraph.ComponentGenerator with "
                         "invalid probability, must be [0.0 - 1.0].")
            LOGGER.error("probability = %s", probability)
            raise ValueError

    def _make_terminal_pdf(self, constant_probability):
        if constant_probability is None:
            terminal_weight = [1, self._input_x_dimension]
        else:
            terminal_weight = [constant_probability,
                               1.0 - constant_probability]
        return ProbabilityMassFunction(items=[1, 0], weights=terminal_weight)

    def _make_random_command_pmf(self, terminal_probability):
        command_weights = [terminal_probability,
                           1.0 - terminal_probability]
        return ProbabilityMassFunction(items=[self._random_terminal_command,
                                              self._random_operator_command],
                                       weights=command_weights)

    def add_operator(self, operator_number, operator_weight=None):
        """Add an operator number to the set of possible operators

        Parameters
        ----------
        operator_number : int
                          operator code defined in Agraph operator maps
        operator_weight : number
                          relative weight of operator probability
        """
        self._operator_pmf.add_item(operator_number, operator_weight)

    def random_command(self, stack_location):
        """Get a random command

        Parameters
        ----------
        stack_location : int
                         location in the stack for the command

        Returns
        -------
        array of int
            a random command in the form [node, parameter 1, parameter 2]

        """
        if stack_location < self._num_initial_load_statements:
            return self._random_terminal_command(stack_location)
        return self._random_command_function_pmf.draw_sample()(stack_location)

    def _random_operator_command(self, stack_location):
        return np.array([self.random_operator(),
                         self.random_operator_parameter(stack_location),
                         self.random_operator_parameter(stack_location)],
                        dtype=int)

    def random_operator(self):
        """Get a random operator

         Get a random operator from the list of possible operators.

        Returns
        -------
        int
            an operator number
        """
        return self._operator_pmf.draw_sample()

    @staticmethod
    def random_operator_parameter(stack_location):
        """Get random operator parameter

        Parameters
        ----------
        stack_location : int
                         location of command in stack

        Returns
        -------
        int
            parameter to be used in an operator command


        Notes
        -----
        The returned random operator parameter is guranteed to be less than
        stack_location.
        """
        return np.random.randint(stack_location)

    def _random_terminal_command(self, _=None):
        terminal = self.random_terminal()
        return np.array([terminal,
                         self.random_terminal_parameter(terminal),
                         self.random_terminal_parameter(terminal)],
                        dtype=int)

    def random_terminal(self):
        """Get a random terminal

         Get a random load-X or load-C terminal.

        Returns
        -------
        int
            terminal number (0 or 1)
        """
        return self._terminal_pmf.draw_sample()

    def random_terminal_parameter(self, terminal_number):
        """Get random terminal parameter

        Parameters
        ----------
        terminal_number : int
                          terminal number for which random parameter should be
                          generated

        Returns
        -------
        int
            parameter to be used in a terminal command
        """
        if terminal_number == 0:
            param = np.random.randint(self._input_x_dimension)
        else:
            param = -1
        return param
