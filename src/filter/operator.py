class Operator:
    """
    This class defines all valid operators that can be used to filter the torrent result
    """

    # Define a dictionary that maps operators to functions
    # The rule value is represented by the variable 'value'
    # The rule element is represented by the variable 'data'
    functions = {
        # String, Tuple operator
        "contains": lambda data, value: value in data,  # data contains value
        "in": lambda data, value: data in value,  # data in value
        # String operator
        "begin_with": lambda data, value: data.startswith(value),  # data begins with value
        "end_with": lambda data, value: data.endswith(value),  # data ends with value
        "equal": lambda data, value: data == value,  # data is equal to value
        # Number operator
        "greater_than": lambda data, value: data > value,  # data is greater than value
        "greater_than_or_equal": lambda data, value: data >= value,  # data is greater than or equal to value
        "less_than": lambda data, value: data < value,  # data is less than value
        "less_than_or_equal": lambda data, value: data <= value,  # data is less than or equal to value
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
