#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import itertools


"""
    Provides helper to generate unique code usefull for SMS matching with model
    objects.
"""

def get_code_from_model(model, field='code', default='0', 
                        order_by=None, qs=None, **kwargs):
    """
        Get the last code from 'model', where the code is in 'field'.
        You can provide your own qs, otherwise it's going to take all the 
        entries then reverse sort it by 'order_by' and take the first one.
        
        If order_by is unset, it will be equal to the code field name.
        
        If no entry is match, returns the 'default' value.
    """

    if not qs:
        qs = model.objects.all()

    # we have to loop in order to catch-n-skip exceptions
    nqs = []
    for m in qs:
        try:
            nqs.append(int(getattr(m, field).lstrip(kwargs['prefix']).rstrip(kwargs['suffix'])))
        except ValueError:
            continue
    nqs.sort(reverse=True)

    try:
        return "%s%s%s" % (kwargs['prefix'], nqs[0], kwargs['suffix'])
    except IndexError:
        if default is not None:
            return default
        raise ValueError('No existing code, please provide a default value') 
    


def increment_base_10(previous_code, min_length=3, prefix='', suffix='', 
                     inc=1, pad_with='0', **kwargs):
    """
        Increment the the numeric part of the code in base 10.
        
        - previous_code: a string with the previous code to increment
        - min_lenght: the minimum lenght you want the numeric part of the code
          to be
        - prefix: the string that should be before the numeric part
        - suffix: the string that should be after the numeric part
        - inc: the number you want to increment the numeric part with
        - pad_with: the char you want to use to fill the numeric part if
          it's below min_length
        
        e.g.
        
        >>> increment_base_10('1', min_length=5)
        '00002'
        >>> increment_base_10('A099L', prefix='A',suffix='L', 
        ...                   min_length=8, inc=2, pad_with='X')
        'AXXXXX101L'
        
    """

    next_code = str(int(previous_code.lstrip(prefix).rstrip(suffix)) + inc)
    return "%s%s%s" % (prefix, next_code.rjust(min_length, pad_with), suffix)
    
    
def generate_tracking_tag(start='2a2', base_numbers='2345679',
                          base_letters='acdefghjklmnprtuvwxy', **kwargs):
    """
        Generate a unique tag. The format is xyz[...] with x, y and z picked
        from an iterable giving a new set of ordered caracters at each
        call to next. You must pass the previous tag and a patter the tag
        should validate against.
        
        This is espacially usefull to get a unique tag to display on mobile
        device so you can exclude figures and letters that could be 
        confusing or hard to type.
        
        Default values are empirically proven to be easy to read and type
        on old phones.
        
        The code format alternate a char from base_number and base_letters,
        be sure the 'start' argument follows this convention or you'll
        get a ValueError.

        e.g:

        >>> generate_tracking_tag()
        '3a2'
        >>> generate_tracking_tag('3a2')
        '4a2'
        >>> generate_tracking_tag('9y9')
        '2a2a'
        >>> generate_tracking_tag('2a2a')
        '3a2a'
        >>> generate_tracking_tag('9a2a')
        '2c2a'

    """

    next_tag = []

    matrix_generator = itertools.cycle((base_numbers, base_letters))

    for index, c in enumerate(start):

        matrix = matrix_generator.next()
        
        try:
            i = matrix.index(c)
        except ValueError:
            raise ValueError(u"The 'start' argument must be correctly "\
                             u"formated. Check doctstring for more info.")
            
        try:
            next_char = matrix[i+1]
            next_tag.append(next_char)
            try:
                next_tag.extend(start[index+1:])
                break
            except IndexError:
                pass
        except IndexError:
            next_tag.append(matrix[0])
            try:
                start[index+1]
            except IndexError:
                matrix = matrix_generator.next()
                next_tag.append(matrix[0])
                break

    return ''.join(next_tag)
    
#TODO: make generate function generate method of classes
# - inside you define the previous code functin
# - the next code fonction
# - a match for the next code
# - a redo code fonction default ting to next code function if not exists
#   and if exists redo the code if match doesn't work

def generate_code(get_previous_code_function, 
                  get_next_code_function=increment_base_10, 
                  **kwargs):
                  
    """
        Generate a code in the most flexible way possitble. A code can be any
        string that needs to be unique and for which the next value is therefor
        most probably dependant on the previous one.
        
        - get_previous_code_function should be a callable that returns a 
        default value for the code or the last one created. It is passed
        **kwargs in case you want to pass it the previous code manually.
        
        - get_next_code_function: the function applied to the previous value
          to get the next one. It is passed the previous value as well as 
          **kwargs
    """
                  
    code = get_previous_code_function(**kwargs)
    return get_next_code_function(code, **kwargs)
    
