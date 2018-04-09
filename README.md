# pulsar
A silly dragon's playtime attempt at creating a BitTorrent indexer API in flask

## Installation
* An explanation of configuration options is available in `config.py.example`.
  All configurations are located in `instance/`.

## Development
* All permission checks should be abstracted to a utility function or the user object,
  such as `require_permission`, `require_auth`, or `choose_user`.

## Style Guide
* PEP8, with a max line length of 90.
* Split multiple kwargs or lists with multiple elements onto new lines, unless they
  compactly fit into one line. Closing brackets* should be indented on new lines.
  Multi-line dicts/lists/kwargs should have a comma after the last element, unless
  they are the last line before a line break or end of function.
    ```
    good = {'id': 2, 'username': 'lights'}
    
    bad = {'id': 2, 'username': 'lights', 'email': 'lights@puls.ar', 'userclass_id': 12}

    good = kwargs.update({
        'id': 2,
        'username': 'lights',
        'email': 'lights@puls.ar',
        'userclass_id': 12,
        })
    another_function_call(...)

    good_test_example = client.get('/test_api_key', environ_base={
            'HTTP_USER_AGENT': 'pulsar-test-client',
            'REMOTE_ADDR': '127.0.0.1',
        }, headers={
            'Authorization': f'Token a-long-token', })

    good_function_call(a_long_variable_name, a_kwarg={
        'active': True,
        'email': 'bright@puls.ar',
        'enabled': 'most-definitely',
        }, final_kwarg=True) 

    # *Function calls split over two lines do not need the closing bracket to be on a new line.
    a_long_function_name(
         'You have permission to do things with this codebase.')
    ```

* Use kwargs to reduce argument confusion.
    ```
    bad = func(aba, bcb, cdc, ded, efe)

    good = func(
        esoteric_arg1=aba,
        esoteric_arg2=bcb,
        esoteric_arg3=cdc,
        esoteric_arg4=ded,
        esoteric_arg5=efe,
        )
    ```  

* Surround assignments of boolean statements with parentheses.
    ```
      bad_bool = a == b and c is d

      good_bool = (a == b and c is d)
    ```

* For single line docstrings, use single quotes. For multi-line docstrings, use triple quotes
  and start the body of the docstring after a newline.
    ```
    a_function():
         "A single-line docstring."

    another_function():
         """
         A multi-line docstring with more content.
         Lauren impson.
         """
    ```
