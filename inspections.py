import os
import inspect
import importlib.util
import sys
import yaml

root_absolute_path = os.path.abspath(os.path.dirname(__file__))
script_absolute_path = os.path.abspath(__file__)
project_structure = {}

def import_module_from_file(full_path_to_module: str) -> object:
    """
    Imports a Python module from a specified file.

    :param full_path_to_module: The full path to the Python module.
    :returns: The imported Python module.
    """
    module_name = os.path.basename(full_path_to_module).replace('.py', '')
    spec = importlib.util.spec_from_file_location(module_name, full_path_to_module)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def find_py_files(root_dir: str, script_absolute_path: str=script_absolute_path) -> str:
    """
    Finds all Python files in a specified directory, project root is hard-coded in this case.

    :param root_dir: The directory to search for Python files.
    :param script_absolute_path: The absolute path of the script to ignore.
    :returns: Absolute path to found Python modules.
    """
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in [f for f in filenames if f.endswith(".py")]:
            file_absolute_path = os.path.join(dirpath, filename)
            if file_absolute_path == script_absolute_path or file_absolute_path == os.path.join(root_dir, 'tests.py'):
                continue
            yield os.path.join(dirpath, filename)


def get_module_inspections_from_yaml(module_name: str) -> list:
    """
    Loads the function list of a specified module from the inspections YAML file.

    :param module_namew: The module name to load the function list for.
    :returns: The function list for the specified module.
    """
    with open("inspections_map.yaml", 'r') as file:
        data = yaml.safe_load(file)
        module_functions = data.get(module_name, [])
        return module_functions


def update_inspections_map_yaml(yaml_file: str, module_name: str, function_name: str, new_status: str) -> None:
    """
    Updates the inspections YAML file status field for a selected function.

    :param yaml_file: The YAML file to update.
    :param module_name: The module name to update.
    :param function_name: The function name to update.
    :param new_status: The new status to set.
    :returns: None
    """
    with open(yaml_file, 'r') as file:
        data = yaml.safe_load(file)

    if module_name in data:
        for func in data[module_name]:
            if func['name'] == function_name:
                func['status'] = new_status
                break

    with open(yaml_file, 'w') as file:
        yaml.dump(data, file, default_flow_style=False)


def old_main():
    """
    Main function to run the inspections manager from the command line with direct call to the file. Non-loop functions are related to project inspections but called from other modules where necessary.

    :returns: A YAML file containing the project structure and function list (inspections_map.yaml)
    """
    for py_file in find_py_files(root_absolute_path):
        module = import_module_from_file(py_file)
        functions_list = inspect.getmembers(module, inspect.isfunction)
        module_info = []
        for name, func in functions_list:
            function_info = {
                "name": name,
                "module": module.__name__,
                "status": "untested",  # Initialize status; can be updated later
                "docstring": func.__doc__
            }
            module_info.append(function_info)

        project_structure[module.__name__] = module_info

    # Export to a YAML file
    with open('inspections_map.yaml', 'w') as file:
        yaml.dump(project_structure, file, sort_keys=False)


def main():

    for py_file in find_py_files(root_absolute_path):
        module = import_module_from_file(py_file)
        functions_list = inspect.getmembers(module, inspect.isfunction)

        module_info = []
        for name, func in functions_list:
            signature = inspect.signature(func)
            source_lines = inspect.getsourcelines(func)
            function_info = {
                "name": name,
                "module": module.__name__,
                "status": "untested",
                "docstring": func.__doc__,
                "signature": str(signature),
                "line_number": source_lines[1],
                "annotations": func.__annotations__
            }
            module_info.append(function_info)

        project_structure[module.__name__] = module_info

    # Export to a YAML file
    with open('inspections_map_detailed.yaml', 'w') as file:
        yaml.dump(project_structure, file, sort_keys=False)

if __name__ == "__main__":
    main()
