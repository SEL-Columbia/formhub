#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8

import os, glob, time
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy
from xml.dom import minidom, Node
from utils.logger_tools import create_instance
from odk_logger.xform_instance_parser import clean_and_parse_xml
from odk_logger.models import Instance
from odk_viewer.models import ParsedInstance, DataDictionary
from ... import models


class Command(BaseCommand):
    help = ugettext_lazy("Ungroup repeat to different instances")

    def handle(self, *args, **kwargs):

    	start = time.time()
    	#we run the commands on all the forms 
    	xforms = models.XForm.objects.all()
    	for xform in xforms:
	    	#each instance is an answer to a survey
	    	instances = xform.surveys.all()
	    	#we get the repeating groups of the survey
	    	repeats = [e.get_abbreviated_xpath() for e in xform.data_dictionary().get_survey_elements_of_type(u"repeat")]
	    	for instance in instances:
	    		#this is the raw xml that contains the answers of the survey
	    		doc = minidom.parseString(instance.xml)
	    		root_doc = doc.firstChild
	    		#the dictionary is just used to find the right repeating group, it's probably possible to remove this
	    		dd = instance.get_dict()
	    		#for each repeating group...
	    		for repeat in repeats:
	    			if repeat in dd:
	    				#we get the node that contains the targeted repeating group
	    				repeat_nodes = doc.getElementsByTagName(repeat)
	    				#we clonde each node insisde the repeating group
	    				#we need to use cloneNode, otherwise we just get a reference to the node (and we'll lose it on deletion)
	    				xml_repeats_clone = [node.cloneNode(True) for node in repeat_nodes if not node.hasAttribute('template') ]
	    				#we remove the repeating group of our document, to get the base
	    				for r in repeat_nodes:
	    					old = doc.firstChild.removeChild(r)
	    					old.unlink()
	    				#we append ecah repeating group to his own document
	    				#and we create an instance of Instance and ParsedInstance with each of these documents
	    				for el in xml_repeats_clone:
	    					new_doc = root_doc.cloneNode(True)
	    					new_doc.appendChild(el)
	    					i = Instance.objects.create(xml=new_doc.toxml(), user=xform.user)
	    					ParsedInstance.objects.get_or_create(instance=i)
    	end = time.time()
    	print end-start
