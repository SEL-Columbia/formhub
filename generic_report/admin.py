#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.contrib import admin
from .models import *
import eav

admin.site.register(Report)
admin.site.register(Record)  

admin.site.register(Parameter)
admin.site.register(ReportView)

admin.site.register(SelectedIndicator)

admin.site.register(Indicator)
admin.site.register(ValueIndicator)
admin.site.register(SumIndicator)
admin.site.register(RatioIndicator)
admin.site.register(RateIndicator)
admin.site.register(AverageIndicator)
admin.site.register(ProductIndicator)
admin.site.register(DifferenceIndicator)
admin.site.register(DateIndicator)
admin.site.register(LocationIndicator)

admin.site.register(Aggregator)
admin.site.register(DateAggregator)
admin.site.register(LocationAggregator)

eav.register(Record)
