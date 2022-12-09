class Operator:
    """
    This class defines all valid operators that can be used to filter the torrent result
    """

    # Define a dictionary that maps operators to functions
    functions = {
        # String, Tuple operator
        "contains": lambda x, y: y in x,
        "in": lambda x, y: x in y,
        # String operator
        "begin_with": lambda x, y: x.startswith(y),
        "end_with": lambda x, y: x.endswith(y),
        "equal": lambda x, y: x == y,
        # Number operator
        "greater_than": lambda x, y: x > y,
        "greater_than_or_equal": lambda x, y: x >= y,
        "less_than": lambda x, y: x < y,
        "less_than_or_equal": lambda x, y: x <= y,
    }

    @classmethod
    def get_function(cls, operator):
        """
        This method returns the function for a given operator
        :param operator: The operator to use
        :return: The function to use
        """
        # Get the function for the operator
        return cls.functions.get(operator, lambda *args: True)
