Small lib to generate unique codes, useful to identity an object in a short
yet non confusing way.

We use it to generate codes for objects in SMS systems so the user
can quickly refer to something without typing the entire name with
the phone keyboard.

Setup
=====

Drop the directory in your Python PATH



Usage
=====

The main function you want to user is::

    generate_code(get_previous_code_function, 
                      get_next_code_function=increment_base_10, 
                      **kwargs):
                      
It will generate your next code, provided you pass to it:

- get_previous_code_function

  a function that accepts **kwargs and will receive all extra args from 
  'generate_code'. It should return the last code that has been created 
  or at least a default value
  
- get_next_code_function

  a function that accepts the previous code and **kwargs and will receive
   all extra args from 'generate_code' as well as the code produced by
   'get_previous_code_function'. It should return the next code.
 
   
Several functions are available to some common operations::

    increment_base_10(previous_code, min_length=3, prefix='', suffix='', 
                         inc=1, pad_with='0', **kwargs)

It is the basic 'get_next_code_function' and will let you increment, pad
and previous code.

::

    generate_tracking_tag(start='2a2', base_numbers='2345679',
                          base_letters='acdefghjklmnprtuvwxy', **kwargs)
                          
It generates a easy to read / type code on mobile phones.

::

    get_code_from_model(model, field='code', default=None, 
                            order_by='id', qs=None, **kwargs)
                            
Get you the last code from a Django model, while letting you decide what 'last'
means and where it should take it from. You may use it as 
'get_previous_code_function'

e.g., using Django models to provide the code. Starting with an empty DB.

::

    >>> from code_generator import *
    >>> generate_code(get_code_from_model, prefix='L',  default='0', min_length=3, 
    ...               field='username', model=User)
    'L001'
    >>> User.objects.create(username='L001')
    >>> generate_code(get_code_from_model, prefix='L', min_length=4, 
    ...               field='username', model=User), 
    'L0002'
    >>> User.objects.create(username='9a2a')
    >>> generate_code(get_code_from_model, generate_tracking_tag, 
    ...               field='username', model=User)
    '2c2a'


Writting you own functions
===========================

You can of course create your own functions to get custom previous / next code.
They must accept **kwargs and the function to get next code should accept the
previous code as first argument. **kwargs from generate_code will be passed
to both of them.


Django integration
===================

This module is not tied to any framework and you can use it in any Python
project. However, some helpers for Django are available.

::

    get_code_from_model(model, field='code', default='0', 
                        order_by='code', qs=None, **kwargs)
                        
This is a meant to be passed as 'get_previous_code_function' and will 
look for a previous code in the given field for the passed model.

As most of the time you will just want to have a generated code as a
model attribute, we created a model field for that purpore. Just do::

    from code_generator.fields import CodeField
    
    class MyModel(models.Model):
    
        code = CodeField(**options)

Options can be any args of models.CharField (such as the mandatory max_length)
and of 'increment_base_10'

We will try to add a more generic field that accept an function fromt the 
code generator later, for now it is limited to 'increment_base_10'.


Testing
=======

Module is covered by unit tests. However, while the module itself is not
tied to Django (you can completly use it without django installed), tests are
testing django features and therefor require Django to be installed.

Documentation
==============

All function have a long doctest to explain their purpose in detail. You
can see Unit test for a practical use of all the advance features all 
the module.
