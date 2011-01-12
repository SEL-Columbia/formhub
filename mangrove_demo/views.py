#!/usr/bin/env python
# encoding=utf-8
# vim: ai ts=4 sts=4 et sw=4


from datetime import datetime

from django.http import HttpResponse
from django.shortcuts import render_to_response, redirect, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils.translation import check_for_language
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from generic_report.models import Report, ReportView, SelectedIndicator, Indicator

from generic_report_admin.forms import (RecordForm, ViewForm, 
                                        ViewAggregationForm, 
                                        ViewIndicatorsForm, 
                                        IndicatorCreationForm,
                                        IndicatorChooserForm)


@login_required
def display_report(request, id):
    """
        Display the data from the report, with a pagination by views.
        Data is formated will be formated as and HTML table.
        At the bottom, we will put a form to be able to fill the report
        with more data.
        It's just a simple exemple of what we can do, as almost any kind of data
        display can be done.
    """

    # boiler plate to get the report, it's views and order them by creation
    report = Report.objects.get(pk=id)
    report_views = report.views.all().order_by('pk')
    
    if report_views:
        
        # standard django pagination tool, nothing mangrove specific here
        paginator = Paginator(report_views, 1) # Show 1 view per page

        try:
            num_pages = int(request.GET.get('page', '1'))
        except ValueError:
            num_pages = 1

        # If page request (9999) is out of range, deliver last view.
        try:
            page = paginator.page(num_pages)
        except (EmptyPage, InvalidPage):
            page = paginator.page(paginator.num_pages)

        # according to pagination, you get the proper view
        # feel free to choose another way to navigate
        # pagination with django paginator was just the quickes to setup
        view = page.object_list[0]

        # Here is really where all the magic happen
        # each view has two methods to get the data out of the report
        # this is automatic and doesn't need any parameter
        # It ouputs a very simple format for the data so it can be used
        # for an HTML table, a JS Graph or a CSV/XLS file alike.
        
        # this will give you a list or indicators to display as a list of 
        # strings. See the template to see how to use it as a header
        header = view.get_labels()
        
        # this will give you all the data from the report, formated for this 
        # view, as a list of dictionaries. See the template to see how to
        # use it in a table.
        body = view.get_data_grid()
        
        # This part is for the RecordForm, a django form to add data in the report
        # The RecordForm is created dynamically according to a report and you
        # dont' have to care about how it does the work to use it in a 
        # view or a template as it uses standard django form API.
    
        # Standard boilerplate to process form and redirect on success
        # or display the error on failure              
        if request.method == 'POST':
            form = RecordForm(request.POST, report=report)
            
            if form.is_valid():
                form.save()
                url = "%s?page=%s" % (reverse('report-results', 
                                      args=(report.pk,)),
                                      page.number)
                return redirect(url)
        else:
            form = RecordForm(report=report)
    
    # short hand to get all the local variables in a dictionaries
    # we probably don't want that in production, by for our dev it's quicker
    # than creating the context manually
    ctx = locals()

    return render_to_response('display_report.html',  ctx,
                              context_instance=RequestContext(request))





@login_required
def edit_view_indicators(request, id):
    # you can just brutally raise a 404 error if they try to edit a view
    # that doesn't exist. This should not bother a user using the UI,
    # only one messing around with the URL which we don't want to
    # it can as well reveal important bug, so we want it to be an explicit error
    view = get_object_or_404(ReportView, id=id)
   
    url = reverse('edit-view-indicators', args=(id,))
   
    if request.method == 'POST': 
            
            
            create_form = IndicatorCreationForm(data=request.POST,
                                            report_view=view, prefix='create')
                                 
            # use different button names if you have several forms to 
            # separate form processing           
            if "create-button" in request.POST:
                if create_form.is_valid():
                    view.add_indicator(create_form.save())
                    return redirect(url)
                    
            add_form = IndicatorChooserForm(data=request.POST,
                                            report_view=view, prefix='add')
                  
            if "add-button" in request.POST:                          
                if add_form.is_valid():
                    add_form.save()
                    return redirect(url)
                
            edit_form = ViewIndicatorsForm(data=request.POST,
                                           report_view=view)
    
            if "save-button" in request.POST:
                if edit_form.is_valid():
                    edit_form.save()
                    return redirect(url)
                
    else:
        # you can create a separate view for the remove action, I'm just
        # doing it here for my convenience
        # todo: remove dependancies when removing an indicator, part of calculation
        # todo: make a method for deletion to avoid designer to type this code
        to_remove = request.GET.get('remove', 0)
        if to_remove:  
            indicator = get_object_or_404(Indicator, id=to_remove)
            report = view.report
            view.report.indicators.remove(indicator)
            # remove the indicator from the report and all the views
            for view in report.views.all():
                SelectedIndicator.objects.filter(view=view, 
                                                indicator=indicator).delete()
            return redirect(url)
    
        # in django, you should add a prefix to forms if you have several of
        # them on the same page to give a namespace to the forms data
        # forms of edit_form are prefixed dynamically
        create_form = IndicatorCreationForm(report_view=view, prefix='create')
        add_form = IndicatorChooserForm(report_view=view, prefix='add')
        edit_form = ViewIndicatorsForm(report_view=view)
    

    
    return render_to_response('edit_view_indicators.html',  locals(),
                          context_instance=RequestContext(request))


@login_required
def edit_view_aggregators(request, id):
    """
        Let the user choose the indicator he would like it's data to be 
        grouped by.
    """

    view = get_object_or_404(ReportView, id=id)

    if request.method == 'POST':
        form = ViewAggregationForm(request.POST, view=view)
        if form.is_valid():
            form.save()
            url = reverse('edit-view-aggregators', args=(view.pk,))
            return redirect(url)
    else:
        form = ViewAggregationForm(view=view)

    return render_to_response('edit_view_aggregators.html',  locals(),
                          context_instance=RequestContext(request))


@login_required                          
def edit_view_data_display(request, id):
    """
        A view to manage wether an indicator must be displayed or not
        for the current view, and in which order.
    """
    # there is no built in form for this one since it seems overkill
    # but let me know it you feel like needing one to avoid this boiler plate
    # just be sure you don't get confuse between Indicator objects (the data descriptors)
    # and SelectedIndicator objects (they are just a proxy between views and 
    # indicators that allow us to know which indicator is linked to this view
    # and in which order)
    
    view = get_object_or_404(ReportView, id=id)
    url = (reverse('edit-view-data-display', args=(view.pk,)))
    
    # first, try to see if the user requested to move the order of one indicator
    # and do it so in that case
    if request.method == 'GET':
        try:
            # get increase parameter containing an indicator id
            # it it exists and is valid, just use the proper method to decrease the 
            # order (it manages errors itself)
            pk = int(request.GET['decrease-order'])
            si = view.selected_indicators.get(indicator__id=pk)
            si.decrease_order()
            # redirect is important to avoid reordering if you hit F5
            return redirect(url)
        except (KeyError, SelectedIndicator.DoesNotExist, ValueError), e:
            pass
         
        # same with increase
        try:
            pk = int(request.GET['increase-order'])
            si = view.selected_indicators.get(indicator__id=pk)
            si.increase_order()
            return redirect(url)
        except (KeyError, SelectedIndicator.DoesNotExist, ValueError), e:
            pass
    
    # then see if the user changed the indicators to display for this view
    # every checked checkbox is an indicator to display
    if request.method == 'POST':
        # delete all old selected indicators
        view.selected_indicators.all().delete()
        
        # create brand new ones according to user selection
        for pk in request.POST.iterkeys():
            if pk.isdigit(): # get rid of stuff like csrf token
                view.add_indicator(Indicator.objects.get(pk=pk))
                
        return redirect(url)
                
    # Note that in theory this is unsafe because a user could send a post 
    # request with wrong ids, resulting in deleting all indicators and creating
    # none. In practice, only a logged on user with IT skills would be able
    # to do it, so if he does, he should know what he does. The other scenario
    # is an AJAX request you create, in that case be sure that your ids are
    # valid and it will be fine.
    
    return render_to_response('edit_view_data_display.html',  locals(),
                          context_instance=RequestContext(request))
                          
 
@login_required
def edit_default_view(request, id):
    """
        Redirection to the default view editing. Used when we know the report but
        not the view, such as when we created the report.
    """

    report = get_object_or_404(Report, id=id)
    url = reverse('edit-view-indicators', args=(report.default_view.pk,))
    return redirect(url)
    
    
@login_required
def add_view_to_report(request, id):
    """
        Let you create a view and add it to a report then redirect to
        the page to edit the view.
    """

    report = get_object_or_404(Report, id=id)
    blank_view = ReportView(report=report, name='') # to provide sane default
    
    if request.method == 'POST':
        form = ViewForm(request.POST, instance=blank_view)
        if form.is_valid():
            view = form.save()
            url = reverse('edit-view-indicators', args=(view.pk,))
            return redirect(url)
    else:
        form = ViewForm(instance=blank_view)
    
    return render_to_response('add_view_to_report.html',  locals(),
                      context_instance=RequestContext(request))
    
    
# todo: protect default view
@login_required
def delete_view(request, id):
    """
        Delete a ReportView. Because we redirect to the report, we can't use 
        a Django generic_view.
    """
    view = get_object_or_404(ReportView, id=id)
    if request.method == 'POST':    
        view.delete()
        url = reverse('edit-report', args=(view.report_id,))
        return redirect(url)
    return render_to_response('delete_view.html',  locals(),
                          context_instance=RequestContext(request))
