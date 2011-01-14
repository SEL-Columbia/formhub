#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

from django.test import TestCase
from django.db import models
from django.contrib.auth.models import User
from django.db.models import exceptions

from code_generator import *


class CodeGeneratorTests(TestCase):
    
    def test_increment_base_10(self):
        
        self.assertEqual(increment_base_10('100'), '101')     
        self.assertEqual(increment_base_10('10'), '011') 
        self.assertEqual(increment_base_10('1', min_length=5), '00002')
        self.assertEqual(increment_base_10('999', min_length=1), '1000')
        self.assertEqual(increment_base_10('t22', prefix='t'), 't023')
        self.assertEqual(increment_base_10('bla00001', prefix='bla'), 'bla002')
        self.assertEqual(increment_base_10('010001%', suffix='%', min_length=4), 
                                            '10002%')
        self.assertEqual(increment_base_10('010099atchoum', suffix='atchoum', 
                                            min_length=8, inc=2), 
                                            '00010101atchoum')
        self.assertEqual(increment_base_10('A099L', prefix='A',suffix='L', 
                                            min_length=8, inc=2, pad_with='X'), 
                                            'AXXXXX101L')
                                        
                                            
    def test_get_code_from_model(self):
    
        self.assertEqual(get_code_from_model(User, 'username', default='0'), 
                         '0')
        self.assertEqual(get_code_from_model(User, 'username'), '0')
            
        User.objects.create(username='toto')
        
        try:
            get_code_from_model(User, 'unexistant_field')
            self.fail()
        except exceptions.FieldError:
            pass
        
        # ordering is on the code field by default
        self.assertEqual(get_code_from_model(User, 'username'), 'toto')
        
        User.objects.create(username='bobo')
        
        self.assertEqual(get_code_from_model(User, 'username'), 'toto')
        
        self.assertEqual(get_code_from_model(User, 'username',  order_by='id'), 
                         'bobo')
                                       
        qs = User.objects.exclude(username='bobo')      
        self.assertEqual(get_code_from_model(User, 'username', qs=qs), 'toto')


    def test_generate_code(self):
    
        def start(code, **kwargs):
            return code
        
        self.assertEqual(generate_code(start, code='100'), '101')     
        self.assertEqual(generate_code(start, code='10'), '011') 
        self.assertEqual(generate_code(start, code='1', min_length=5), '00002')
        self.assertEqual(generate_code(start, code='999', min_length=1), '1000')
        self.assertEqual(generate_code(start, code='t22', prefix='t'), 't023')
        self.assertEqual(generate_code(start, code='bla00001', prefix='bla'), 
                         'bla002')
        self.assertEqual(generate_code(start, code='010001%', 
                                       suffix='%', min_length=4), 
                         '10002%')
        self.assertEqual(generate_code(start, code='010099atchoum', 
                                       suffix='atchoum',  min_length=8, inc=2), 
                         '00010101atchoum')
        self.assertEqual(generate_code(start, code='A099L', prefix='A', 
                                       suffix='L',  min_length=8, inc=2, 
                                       pad_with='X'), 
                         'AXXXXX101L')
              
                         
        self.assertEqual(generate_code(get_code_from_model, prefix='L', 
                                        default='0', min_length=3, 
                                        field='username', model=User), 'L001')
                         
        User.objects.create(username='L001')
        
        self.assertEqual(generate_code(get_code_from_model, prefix='L', 
                                        default='0', min_length=3, 
                                        field='username', model=User), 'L002')
        
        User.objects.all().delete()                              
        User.objects.create(username='2a2')
        
        self.assertEqual(generate_code(get_code_from_model, 
                                       generate_tracking_tag, 
                                        field='username', model=User), 
                         '3a2')
