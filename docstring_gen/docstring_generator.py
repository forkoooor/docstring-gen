# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/Docstring_Generator.ipynb.

# %% auto 0
__all__ = ['add_docstring_to_notebook']

# %% ../nbs/Docstring_Generator.ipynb 2
import ast
import tokenize
from typing import *
from pathlib import Path
from io import BytesIO

import nbformat

# %% ../nbs/Docstring_Generator.ipynb 5
def _generate_docstring_using_codex(code: str) -> str:
    return """Sample docstring

    Args:
        s: sample args

    Returns:
        sample return
"""

# %% ../nbs/Docstring_Generator.ipynb 6
def _inject_docstring_to_source(
    source: str, docstring: str, lineno: int, node_col_offset: int
) -> str:
    """Inject a docstring into the source code at a specified line number.

    Args:
        source: the source code
        docstring: the docstring to be added
        lineno: the line number at which the docstring will be inserted
        node_col_offset: the number of spaces to indent the docstring

    Returns:
        The updated source code with the docstring injected
    """
    lines = source.split("\n")
    indented_docstring = "\n".join(
        [
            line
            if i == 0 or i == len(docstring.split("\n")) - 1
            else f"{' ' * node_col_offset}{line}"
            for i, line in enumerate(docstring.split("\n"))
        ]
    )
    indent = node_col_offset + 4
    lines.insert(lineno, f'{" " * indent}"""{indented_docstring}{" " * indent}"""')
    return "\n".join(lines)

# %% ../nbs/Docstring_Generator.ipynb 8
def _get_code_from_source(source: str, start_line_no: int, end_line_no: int) -> str:
    """Get a block of lines from a given source string.

    Args:
        source: The source string.
        start_line_no: The line number of the start of the block of lines.
        end_line_no: The line number of the end of the block of lines.

    Returns:
        The extracted block of lines from the source
    """
    source_lines = source.split("\n")
    extracted_lines = source_lines[start_line_no - 1 : end_line_no]
    return "\n".join(extracted_lines)

# %% ../nbs/Docstring_Generator.ipynb 10
def _calculate_end_lineno(source: str, start_line_no: int) -> int:
    """Calculate the end line number of a function in a Python source code.

    Args:
        source: The source code string.
        start_line_no: The line number of the start of the function.

    Returns:
        The end line number of the function.
    """
    lines = source.split("\n")[start_line_no - 1 :]
    first_indent = len(lines[0]) - len(lines[0].lstrip())
    end_line_in_source = 0

    for i, line in enumerate(lines[1:]):
        if len(line) - len(line.lstrip()) == first_indent and line.strip() != "":
            end_line_in_source = i
            break

    ret_val = (
        len(source.split("\n"))
        if end_line_in_source == 0
        else end_line_in_source + start_line_no
    )
    return ret_val - 1

# %% ../nbs/Docstring_Generator.ipynb 12
def _line_has_class_or_method(source: str, lineno: int) -> bool:
    """Check if a line in the source code contains a class or method definition.

    Args:
        source: The source code as a string.
        lineno: The line number to check.

    Returns:
        True if the line contains a class or method definition, False otherwise.
    """
    line = "".join(source.split("\n")[lineno - 1])
    tokens = list(tokenize.tokenize(BytesIO(line.encode("utf-8")).readline))
    return tokens[1].type == tokenize.NAME and tokens[1].string in {
        "class",
        "def",
        "async",
    }


def _get_start_line_for_class_or_func(source: str, lineno: int) -> int:
    """Get the line number of the first line containing a class or function definition.

    Args:
        source: The source code as a string.
        lineno: The line number to start from.

    Returns:
        The line number of the first line containing a class or function definition,
        or the original line number if no such line is found.
    """
    if _line_has_class_or_method(source, lineno):
        return lineno

    original_lineno = lineno
    total_lines = source.split("\n")[lineno - 1 :]

    for i in total_lines:
        lineno += 1
        if lineno > len(total_lines):
            break
        if _line_has_class_or_method(source, lineno):
            return lineno
    return original_lineno

# %% ../nbs/Docstring_Generator.ipynb 14
def _add_docstring(
    source: str,
    node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef],
    line_offset: int,
) -> Tuple[str, int]:
    """Add a docstring to the given node and update the source code.

    Args:
        source: the source code from the notebook cell
        node: the AST node representing a class definition, function definition,
            or async function definition
        line_offset: the number of lines added before the current
            node in the source

    Returns:
        A tuple containing the updated source code and the new line number offset
    """
    line_no = node.lineno + line_offset

    # Fix for ast's node.lineno giving line number of decorator
    # instead of function/class definition in Python 3.7
    line_no = _get_start_line_for_class_or_func(source, line_no)

    if hasattr(node, "end_lineno") and node.end_lineno is not None:
        end_line_no = node.end_lineno + line_offset
    else:
        end_line_no = _calculate_end_lineno(source, line_no)

    code = _get_code_from_source(source, line_no, end_line_no)
    docstring = _generate_docstring_using_codex(code)

    source = _inject_docstring_to_source(source, docstring, line_no, node.col_offset)
    line_offset += len(docstring.split("\n"))
    return source, line_offset

# %% ../nbs/Docstring_Generator.ipynb 16
def _check_and_add_docstrings_to_source(source: str) -> str:
    """Check for missing docstrings in the source code and add them if necessary.

    Args:
        source: the source code from the notebook cell

    Returns:
        The updated source code with added docstrings
    """

    tree = ast.parse(source)
    line_offset = 0

    for node in tree.body:
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if ast.get_docstring(node) is not None:
            continue

        # A class or a function without docstring
        source, line_offset = _add_docstring(source, node, line_offset)
        if not isinstance(node, ast.ClassDef):
            continue

        # Is a class and we need to check the functions inside
        # 29 - 36 make it as a recursive function
        for f in node.body:
            if not isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if ast.get_docstring(f) is not None:
                continue

            # should be a function inside the class for which there is no docstring
            source, line_offset = _add_docstring(source, f, line_offset)

    return source

# %% ../nbs/Docstring_Generator.ipynb 17
def add_docstring_to_notebook(nb_path: Union[str, Path], version: int = 4):
    """Add docstrings to the source

    This function reads through a Jupyter notebook cell by cell and
    adds docstrings for classes and methods that do not have them.

    Args:
        nb_path: The notebook file path
        version: The version of the Jupyter notebook format
    """
    nb_path = Path(nb_path)
    nb = nbformat.read(nb_path, as_version=version)

    for cell in nb.cells:
        if cell.cell_type == "code":
            cell["source"] = _check_and_add_docstrings_to_source(cell["source"])

    nbformat.write(nb, nb_path)
