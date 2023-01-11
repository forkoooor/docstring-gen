# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/Docstring_Generator.ipynb.

# %% auto 0
__all__ = ['AUTO_GEN_PERFIX', 'AUTO_GEN_BODY', 'AUTO_GEN_SUFFIX', 'AUTO_GEN_TXT', 'DOCSTRING_RETRY_ATTEMPTS', 'PROMPT_TEMPLATE',
           'DEFAULT_PROMPT', 'add_docstring_to_source']

# %% ../nbs/Docstring_Generator.ipynb 2
import time
import random
import ast
import tokenize
import os
import re
from typing import *
from pathlib import Path
from io import BytesIO
from configparser import ConfigParser

import nbformat
import openai
import typer

# %% ../nbs/Docstring_Generator.ipynb 4
def _get_code_from_source(source: str, start_line_no: int, end_line_no: int) -> str:
    """This function takes in a source code, start line number and end line number and returns the code between the start and end line numbers.

    Args:
        source (str): The source code to be extracted from
        start_line_no (int): The start line number
        end_line_no (int): The end line number

    Returns:
        str: The code between the start and end line numbers

    Raises:
        IndexError: If the start or end line numbers are out of range


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    source_lines = source.split("\n")
    extracted_lines = source_lines[start_line_no - 1 : end_line_no]
    return "\n".join(extracted_lines)

# %% ../nbs/Docstring_Generator.ipynb 6
def _calculate_end_lineno(source: str, start_line_no: int) -> int:
    """Calculates the end line number of a function in a python file.
        Args:
            source: The source code of the python file.
            start_line_no: The line number of the start of the function.
        Returns:
            The line number of the end of the function.
        Raises:
            ValueError: If the start_line_no is not the start of a function.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
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

# %% ../nbs/Docstring_Generator.ipynb 8
def _line_has_decorator(source: str, lineno: int) -> bool:
    """This function checks if a line has a decorator in it.
        Args:
            source: The source code of the file
            lineno: The line number to check
        Returns:
            True if the line has a decorator, False otherwise
        Raises:
            None


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    line = "".join(source.split("\n")[lineno - 1])
    return line.startswith("@") or line.strip() == ""


def _get_start_line_for_class_or_func(source: str, lineno: int) -> int:
    """This function returns the line number of the start of a class or function.

    Args:
        source: The source code of the file.
        lineno: The line number of the class or function.

    Returns:
        The line number of the start of the class or function.

    Raises:
        None


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    if not _line_has_decorator(source, lineno):
        return lineno

    original_lineno = lineno
    total_lines = source.split("\n")
    for i in total_lines:
        lineno += 1
        if lineno > len(total_lines):
            break
        if not _line_has_decorator(source, lineno):
            return lineno
    return original_lineno

# %% ../nbs/Docstring_Generator.ipynb 11
def _get_lineno_to_append_docstring(source: str, lineno: int) -> int:
    """This function takes in the source code of a python file and the line number of the function definition
        and returns the line number where the docstring should be appended.

        Args:
            source: The source code of the python file
            lineno: The line number of the function definition

        Returns:
            The line number where the docstring should be appended

        Raises:
            TokenError: If the source code is not tokenized


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    line_offset = 0
    is_src_tokenized = False
    lines = source.split("\n")[lineno - 1 :]

    for i in range(len(lines)):
        line = "".join(source.split("\n")[lineno - 1 :][: i + 1])
        if line != "":
            try:
                list(tokenize.tokenize(BytesIO(line.encode("utf-8")).readline))
                is_src_tokenized = True
                break
            except tokenize.TokenError as e:
                line_offset += 1
                continue
    if not is_src_tokenized:
        raise tokenize.TokenError(f"TokenError: {source}")

    ret_val = line_offset + lineno
    return ret_val

# %% ../nbs/Docstring_Generator.ipynb 14
AUTO_GEN_PERFIX = """!!! note

"""

# AUTO_GEN_BODY will be used in the {} function for replacing the autogenerated docstring from the previous run
AUTO_GEN_BODY = "The above docstring is autogenerated by docstring-gen library"

AUTO_GEN_SUFFIX = "(https://github.com/airtai/docstring-gen)"

AUTO_GEN_TXT = AUTO_GEN_PERFIX + " " * 4 + AUTO_GEN_BODY + " " + AUTO_GEN_SUFFIX

# %% ../nbs/Docstring_Generator.ipynb 16
def _inject_docstring_to_source(
    source: str,
    docstring: str,
    lineno: int,
    node_col_offset: int,
    include_auto_gen_txt: bool,
) -> str:
    """Injects a docstring into the source code of a function.

    Args:
        source: The source code of the function.
        docstring: The docstring to be injected.
        lineno: The line number of the function definition.
        node_col_offset: The column offset of the function definition.
        include_auto_gen_txt: Whether to include the auto-generated text.

    Returns:
        The source code of the function with the docstring injected.

    Raises:
        ValueError: If the docstring cannot be injected.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    lineno = _get_lineno_to_append_docstring(source, lineno)
    lines = source.split("\n")
    indented_docstring = "\n".join(
        [
            line
            if i == 0 or i == len(docstring.split("\n")) - 1
            else f"{' ' * (node_col_offset + 4)}{line}"
            for i, line in enumerate(docstring.split("\n"))
        ]
    )
    indent = node_col_offset + 4
    nl = "\n"
    auto_gen_txt = f'{nl + nl + (nl.join((" " * indent + i) for i in AUTO_GEN_TXT.split(nl))) + nl if include_auto_gen_txt else ""}'
    lines.insert(
        lineno,
        f'{" " * indent}"""{indented_docstring}{auto_gen_txt}{" " * indent}"""',
    )
    return "\n".join(lines)

# %% ../nbs/Docstring_Generator.ipynb 19
# Reference: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_handle_rate_limits.ipynb


def _retry_with_exponential_backoff(
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 20,
    max_wait: float = 60,
    errors: tuple = (
        openai.error.RateLimitError,
        openai.error.ServiceUnavailableError,
        openai.error.APIError,
    ),
) -> Callable:
    """Retry a function with exponential backoff."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            num_retries = 0
            delay = initial_delay

            while True:
                try:
                    return func(*args, **kwargs)

                except errors as e:
                    num_retries += 1
                    if num_retries > max_retries:
                        raise Exception(
                            f"Maximum number of retries ({max_retries}) exceeded."
                        )
                    delay = min(
                        delay
                        * exponential_base
                        * (1 + jitter * random.random()),  # nosec
                        max_wait,
                    )
                    typer.secho(
                        f"Note: OpenAI's API rate limit reached. Command will automatically retry in {int(delay)} seconds. For more information visit: https://help.openai.com/en/articles/5955598-is-api-usage-subject-to-any-rate-limits",
                        fg=typer.colors.BLUE,
                    )
                    time.sleep(delay)

                except Exception as e:
                    raise e

        return wrapper

    return decorator


@_retry_with_exponential_backoff()
def _completions_with_backoff(**kwargs):
    """This function takes in a dictionary of keyword arguments and returns a completion object.

    Args:
        **kwargs: A dictionary of keyword arguments to be passed to the openai.Completion.create() function

    Returns:
        A completion object

    Raises:
        N/A


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    return openai.Completion.create(**kwargs)

# %% ../nbs/Docstring_Generator.ipynb 24
def _get_best_docstring(docstrings: List[str]) -> Optional[str]:
    """_get_best_docstring(docstrings: List[str]) -> Optional[str]

        Returns the best docstring from a list of docstrings.

        Args:
            docstrings: A list of docstrings.

        Returns:
            The best docstring.

        Raises:
            ValueError: If the list of docstrings is empty.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    docstrings = [d for d in docstrings if "Args:" in d]
    docstrings = [d for d in docstrings if "~~~~" not in d]
    return docstrings[0] if len(docstrings) > 0 else None

# %% ../nbs/Docstring_Generator.ipynb 27
DOCSTRING_RETRY_ATTEMPTS = 5

PROMPT_TEMPLATE = '''
# Python 3.7

{source}

{prompt}
"""
'''

# Having multi-line prompts works the best with the codex model
# Note: The prompt must start with the # symbol
DEFAULT_PROMPT = """
# An elaborate, high quality docstring for the above function adhering to the Google python docstring format:
# Any deviation from the Google python docstring format will not be accepted
# Include one line description, args, returns and raises
"""


def _get_response(**kwargs: Union[int, float, Optional[str], List[str]]) -> Any:
    """This function returns the completions for the given prompt.
        Args:
            prompt: The prompt for which completions are to be generated.
            max_tokens: The maximum number of tokens to be generated.
            temperature: The temperature for sampling.
            top_p: The top_p for sampling.
            n: The number of completions to return.
            stream: The stream for sampling.
            logprobs: The logprobs for sampling.
            stop: The stop for sampling.
            frequency_penalty: The frequency_penalty for sampling.
            presence_penalty: The presence_penalty for sampling.
            best_of: The best_of for sampling.
            frequency_reward: The frequency_reward for sampling.
            presence_reward: The presence_reward for sampling.
            no_repeat_ngram_size: The no_repeat_ngram_size for sampling.
            bad_words_ids: The bad_words_ids for sampling.
            stop_token: The stop_token for sampling.
        repetition_penalty: The repetition

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    try:
        response = _completions_with_backoff(**kwargs)
    except openai.error.AuthenticationError as e:
        raise openai.error.AuthenticationError(
            "No API key provided. Please set the API key in the environment variable OPENAI_API_KEY=<API-KEY>. You can generate API keys in the OpenAI web interface. See https://onboard.openai.com for details."
        )
    return response.choices


def _generate_docstring_using_codex(
    source: str, **kwargs: Union[int, float, Optional[str], List[str]]
) -> str:
    """Generate a docstring for a given source code using codex.

    Args:
        source (str): The source code for which the docstring is to be generated.
        prompt (str): The prompt to be used for the docstring.
        language (str): The language of the source code.
        max_length (int): The maximum length of the docstring.
        max_tokens (int): The maximum number of tokens in the docstring.
        max_sentences (int): The maximum number of sentences in the docstring.
        max_paragraphs (int): The maximum number of paragraphs in the docstring.
        max_docstrings (int): The maximum number of docstrings to be returned.
        max_docstring_length (int): The maximum length of each docstring.
        max_docstring_tokens (int): The maximum number of tokens in each docstring.
        max_docstring_sentences (int): The maximum number of sentences in each docstring.
        max_docstring_paragraphs (int): The maximum number of paragraphs in each docstring.
    max_

    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    prompt: str = DEFAULT_PROMPT if kwargs["prompt"] is None else kwargs["prompt"]  # type: ignore
    prompt = f"# {prompt}" if not prompt.startswith("#") else prompt
    kwargs["prompt"] = PROMPT_TEMPLATE.format(source=source, prompt=prompt)

    for i in range(DOCSTRING_RETRY_ATTEMPTS):
        res = _get_response(**kwargs)
        ret_val = _get_best_docstring([d.text for d in res])

        if ret_val is not None:
            return ret_val

    return """!!! note
    
    Failed to generate docs"""

# %% ../nbs/Docstring_Generator.ipynb 31
def _add_docstring(
    source: str,
    node: Union[ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef],
    line_offset: int,
    include_auto_gen_txt: bool,
    **kwargs: Union[int, float, Optional[str], List[str]],
) -> Tuple[str, int]:
    """Adds a docstring to a class or function.

    Args:
        source: The source code of the file as a string.
        node: The class or function node.
        line_offset: The number of lines to offset the docstring.
        include_auto_gen_txt: Whether to include the auto-generated text.
        kwargs: The keyword arguments to pass to the docstring generator.

    Returns:
        A tuple of the new source and the new line offset.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    line_no = node.lineno + line_offset

    # Fix for  Python 3.7
    # Delete the below line once support for Python 3.7 is dropped
    line_no = _get_start_line_for_class_or_func(source, line_no)

    if hasattr(node, "end_lineno") and node.end_lineno is not None:
        end_line_no = node.end_lineno + line_offset
    else:
        end_line_no = _calculate_end_lineno(source, line_no)

    code = _get_code_from_source(source, line_no, end_line_no)
    docstring = _generate_docstring_using_codex(code, **kwargs)

    source = _inject_docstring_to_source(
        source, docstring, line_no, node.col_offset, include_auto_gen_txt
    )
    line_offset += (
        len(docstring.split("\n"))
        if not include_auto_gen_txt
        else len(docstring.split("\n"))
        + len(AUTO_GEN_TXT.split("\n"))
        + 2  # the 2 is for the \n characters at the beginning
    )
    return source, line_offset

# %% ../nbs/Docstring_Generator.ipynb 33
def _remove_auto_generated_docstring(source: str) -> str:
    """Removes the auto generated docstring from the source code.

    Args:
        source (str): The source code.

    Returns:
        str: The source code without the auto generated docstring.

    Raises:
        ValueError: If the source code is not a string.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    return re.sub(
        f'"""((?!""").)*?({AUTO_GEN_BODY}).*?"""', "", source, flags=re.DOTALL
    )

# %% ../nbs/Docstring_Generator.ipynb 35
def _check_and_add_docstrings_to_source(
    source: str,
    include_auto_gen_txt: bool,
    recreate_auto_gen_docs: bool,
    **kwargs: Union[int, float, Optional[str], List[str]]
) -> str:
    """This function checks and adds docstrings to the source code.
        Args:
            source: The source code as a string.
            include_auto_gen_txt: A boolean value to indicate if the auto generated text should be included.
            recreate_auto_gen_docs: A boolean value to indicate if the auto generated docstring should be recreated.
            **kwargs: The keyword arguments.
        Returns:
            The source code as a string.
        Raises:
            ValueError: If the source code is not a string.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    if recreate_auto_gen_docs:
        source = _remove_auto_generated_docstring(source)

    tree = ast.parse(source)
    line_offset = 0

    for node in tree.body:
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue

        if ast.get_docstring(node) is not None:
            continue

        source, line_offset = _add_docstring(
            source, node, line_offset, include_auto_gen_txt, **kwargs
        )
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
            source, line_offset = _add_docstring(
                source, f, line_offset, include_auto_gen_txt, **kwargs
            )

    return source

# %% ../nbs/Docstring_Generator.ipynb 37
def _get_files(nb_path: Path) -> List[Path]:
    """Get all files in a directory.

        Args:
            nb_path (Path): Path to the directory.

        Returns:
            List[Path]: List of all files in the directory.

        Raises:
            ValueError: If the directory does not contain any Python files or notebooks.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    exts = [".ipynb", ".py"]
    files = [
        f
        for f in nb_path.rglob("*")
        if f.suffix in exts
        and not any(p.startswith(".") for p in f.parts)
        and not f.name.startswith("_")
    ]

    if len(files) == 0:
        raise ValueError(
            f"The directory {nb_path.resolve()} does not contain any Python files or notebooks"
        )

    return files

# %% ../nbs/Docstring_Generator.ipynb 40
def _add_docstring_to_nb(
    file: Path,
    version: int,
    include_auto_gen_txt: bool,
    recreate_auto_gen_docs: bool,
    **kwargs: Union[int, float, Optional[str], List[str]]
) -> None:
    """This function adds docstrings to the source code of a jupyter notebook.
        Args:
            file: Path to the jupyter notebook
            version: Version of the jupyter notebook
            include_auto_gen_txt: Whether to include the text "Auto-generated from notebook" in the docstring
            recreate_auto_gen_docs: Whether to recreate the docstrings even if they already exist
            **kwargs:
                - int_param: An integer parameter
                - float_param: A floating point parameter
                - str_param: A string parameter
                - list_param: A list parameter
        Returns:
            None
        Raises:
            ValueError: If the file is not a jupyter notebook


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    _f = nbformat.read(file, as_version=version)
    for cell in _f.cells:
        if cell.cell_type == "code":
            cell["source"] = _check_and_add_docstrings_to_source(
                cell["source"], include_auto_gen_txt, recreate_auto_gen_docs, **kwargs
            )
    nbformat.write(_f, file)


def _add_docstring_to_py(
    file: Path,
    include_auto_gen_txt: bool,
    recreate_auto_gen_docs: bool,
    **kwargs: Union[int, float, Optional[str], List[str]]
) -> None:
    """Adds docstrings to a python file

    Args:
        file: Path to the file
        include_auto_gen_txt: If True, include the text "Auto generated docstring" in the docstring
        recreate_auto_gen_docs: If True, recreate the docstrings even if they already exist
        kwargs: Additional arguments to be passed to the function

    Returns:
        None

    Raises:
        ValueError: If the file is not a python file


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    with file.open("r") as f:
        source = f.read()
    source = _check_and_add_docstrings_to_source(
        source, include_auto_gen_txt, recreate_auto_gen_docs, **kwargs
    )
    with file.open("w") as f:
        f.write(source)


def add_docstring_to_source(
    path: Union[str, Path],
    version: int = 4,
    include_auto_gen_txt: bool = True,
    recreate_auto_gen_docs: bool = False,
    model: str = "code-davinci-002",
    temperature: float = 0.2,
    max_tokens: int = 250,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    stop: List[str] = ["#", '"""'],
    n: int = 3,
    prompt: Optional[str] = None,
) -> None:
    """Adds docstrings to all functions in a python file or all python files in a directory.

    Args:
        path: Path to a python file or directory containing python files.
        version: Docstring version to use.
        include_auto_gen_txt: Whether to include the text "Auto generated by code-davinci" in the docstring.
        recreate_auto_gen_docs: Whether to recreate the docstrings even if they already exist.
        model: GPT-2 model to use.
        temperature: Temperature to use.
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling parameter.
        frequency_penalty: Frequency penalty parameter.
        presence_penalty: Presence penalty parameter.
        stop: List of strings to stop generating text on.
        n: Number of samples to generate.
        prompt: Prompt to use.

    Raises:
        ValueError: If the path is not a valid file or directory.


    !!! note

        The above docstring is autogenerated by docstring-gen library (https://github.com/airtai/docstring-gen)
    """

    path = Path(path)
    files = _get_files(path) if path.is_dir() else [path]

    for file in files:
        if file.suffix == ".ipynb":
            _add_docstring_to_nb(
                file=file,
                version=version,
                include_auto_gen_txt=include_auto_gen_txt,
                recreate_auto_gen_docs=recreate_auto_gen_docs,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                n=n,
                prompt=prompt,
            )
        else:
            _add_docstring_to_py(
                file=file,
                include_auto_gen_txt=include_auto_gen_txt,
                recreate_auto_gen_docs=recreate_auto_gen_docs,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                n=n,
                prompt=prompt,
            )
