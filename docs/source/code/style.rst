Style Guide
===========

* PEP8, with a max line length of ~90 (hard max at 100) (4 space indents)
* Split multiple kwargs or lists with multiple elements onto new lines, unless they
  fit compactly into one line. Hang the closing brackets or leave them on the same
  line as the last line in the statement.

  .. code::

    good = {'id': 2, 'username': 'lights'}
    
    bad = {'id': 2, 'username': 'lights', 'email': 'lights@puls.ar', 'userclass_id': 12}

    good = kwargs.update({
        'id': 2,
        'username': 'lights',
        'email': 'lights@puls.ar',
        'userclass_id': 12,
        })

    good_test_example = client.get('/test_api_key', environ_base={
            'HTTP_USER_AGENT': 'pulsar-test-client',
            'REMOTE_ADDR': '127.0.0.1',
        }, headers={
            'Authorization': f'Token a-long-token'})

    also_good_test_example = client.get('/test_api_key', environ_base={
            'HTTP_USER_AGENT': 'pulsar-test-client',
            'REMOTE_ADDR': '127.0.0.1',
        }, headers={
            'Authorization': f'Token a-long-token',
        })

    good_function_call(a_long_variable_name, a_kwarg={
        'active': True,
        'email': 'bright@puls.ar',
        'enabled': 'most-definitely',
        }, final_kwarg=True) 

* Use kwargs to reduce argument confusion.

  .. code::

    bad = func(aba, bcb, cdc, ded, efe)

    good = func(
        esoteric_arg1=aba,
        esoteric_arg2=bcb,
        esoteric_arg3=cdc,
        esoteric_arg4=ded,
        esoteric_arg5=efe,
        )

* Multi-line docstrings should begin on new lines. Sphinx input/output
  documentation should be indented to match the longest parameter.
  If a :thing: is abnormally long, feel free to disregard this.

  .. code::

     def a_function(self, arg1, argument2):
         """
         A pretty long docstring.

         :param arg1:      Blah blah blah!
         :param argument2: Blah blah blah!
         :return:          Blah blah blah!

* Annotate code with python 3 style typing

   .. code::

      def a_function(self, arg1: int, arg2: bool) -> str:
          ...
