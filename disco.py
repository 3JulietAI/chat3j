import inspect
import os
import re

def is_safe_input(input_value):
    """
     Implement logic to check for safe input here
    :param input_value:
    :returns: 
    """
    # check if the input is a string without dangerous characters
    if isinstance(input_value, str) and not re.search(r"[^a-zA-Z0-9 ]", input_value):
        return True
    # check if the input contains characters other than the expected type and len
    # prompt Sentry - need to get call history
    return False

def check_recent_functions(num_functions=2):
    """
    Using inspect to call the most recent (n) calls and args
    :param: number of most recent functions for inspect to pull
    :returns: 
    """
    for frame_record in inspect.stack()[1:num_functions+1]:  # Skip the first record as it's this function itself
        current_file = os.path.abspath(__file__)
        
        for frame_record in inspect.stack()[1:num_functions+1]:  # Skip the first record as it's this function itself
            function_name = frame_record.function
            frame_file = frame_record.filename

            # Filter out functions that are not in the current file
            if os.path.abspath(frame_file) != current_file:
                continue

            args, _, _, values = inspect.getargvalues(frame_record.frame)
            
            print(f"Function: {function_name}, Arguments: {args}")

    return True

# Injection Test Function
def test_function(arg1, arg2):
    # function logic
    pass

# Simulating function calls
test_function("safe_string", "<script>alert('xss')</script>")
result = check_recent_functions()
print("Is the input safe?:", result)
