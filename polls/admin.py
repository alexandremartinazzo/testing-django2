from django.contrib import admin
from django.core import serializers
from django.forms.models import model_to_dict
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse_lazy
from django.utils.html import format_html

import json

from .models import Choice, Question
from .forms import QuestionAdminForm


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 3


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['question_text']}),
        ('Date information', {'fields': ['pub_date'],
                              'classes': ['collapse']}),
    ]
    inlines = [ChoiceInline]
    list_display = [
        'question_text',
        'pub_date',
        'was_published_recently',
        # we add button actions for each object also :-)
        'button_actions',
    ]
    list_filter = ['pub_date']
    search_fields = ['question_text']

    # allow editing fields on change_list view!
    list_editable = ['question_text']

    # question_text would be clickable, so we better change that
    list_display_links = ['pub_date', 'was_published_recently']

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('<path:object_id>/action1/',
                 self.admin_site.admin_view(self.view_action1),
                 name='polls_question_action1'),
            path('<path:object_id>/action2/',
                 self.admin_site.admin_view(self.view_action2),
                 name='polls_question_action2'),
        ]

        return my_urls + urls

    def view_action1(self, request, object_id):
        question = get_object_or_404(Question, id=object_id)

        context = dict(
            self.admin_site.each_context(request),
            question=question,
        )

        return TemplateResponse(request,
                                'polls/admin/question_action1.html',
                                context)

    def view_action2(self, request, object_id):
        question = get_object_or_404(Question, id=object_id)
        form = QuestionAdminForm(initial=model_to_dict(question))

        context = self.admin_site.each_context(request)
        context['form'] = form
        # when extending change_form.html one must set 'opts'
        context['opts'] = self.model._meta

        return TemplateResponse(request,
                                'polls/admin/question_action2.html',
                                context)

    def button_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">Action 1</a>&nbsp;' +
            '<a class="button" href="{}">Action 2</a>',
            reverse_lazy('admin:polls_question_action1', args=[obj.pk]),
            reverse_lazy('admin:polls_question_action2', args=[obj.pk]),
        )
    button_actions.short_description = 'Shortcut actions'
    button_actions.allow_tags = True


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    # uses widget Select2 (jquery-enabled select - nice!)
    # requires search_field at the related model admin
    autocomplete_fields = ['question']
    actions = ['view_as_json']

    def test_view(self, request):
        ''' custom view for Choice admin...
        I will use as intermediate page for an action
        '''
        # selected objects are in the URL... request.GET (a dict)
        # remember: you're working with text
        id_list = request.GET.get('ids', [])
        # converts to a list if we received something
        if id_list:
            id_list = id_list.split(',')

        # generate a proper queryset with that
        qs = Choice.objects.filter(id__in=id_list)
        output = serializers.serialize('json', qs)

        context = dict(
            self.admin_site.each_context(request),
            # this allows for some JSON pretty printing
            json_string=json.dumps(json.loads(output), indent=4),
        )

        return TemplateResponse(request,
                                'polls/admin/choice_test.html',
                                context)

    def view_as_json(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)

        # URL should look like: '/admin/polls/choice/json/?ids=1,2,3'
        redirect_url = '{base}?ids={parameters}'.format(
            base=reverse_lazy('admin:polls_choice_json_export'),
            parameters=','.join(selected)
        )

        return HttpResponseRedirect(redirect_url)
    view_as_json.short_description = 'View objects as JSON'

    def get_urls(self):
        ''' we use this to add new URLs to our admin... '''
        urls = super().get_urls()

        my_urls = [
            path('json/',
                 self.admin_site.admin_view(self.test_view),
                 name='polls_choice_json_export')
        ]

        return my_urls + urls


################################################################################
class AdminAction(Question):
    ''' we create this model so we can register something else in the admin
    without a database entry '''

    class Meta:
        proxy = True


@admin.register(AdminAction)
class PollsAdminActions(admin.ModelAdmin):
    ''' I don't want to display anything in this admin;
    When an user clicks the changelist_view link we'll redirect to
    somewhere else '''

    def view1(self, request):
        return HttpResponse('View 1')

    def view2(self, request):
        return HttpResponse('View 2')

    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path('view1/',
                 self.admin_site.admin_view(self.view1),
                 name='polls_adminaction_view1',),
            path('view2/',
                 self.admin_site.admin_view(self.view2),
                 name='polls_adminaction_view2',),
        ]

        return my_urls + urls

    def changelist_view(self, request, extra_context=None):
        ''' overriding the list view... '''
        # when extending change_list.html one must set some context variables...
        context = self.admin_site.each_context(request)
        context['opts'] = self.model._meta
        context['cl'] = self.get_changelist_instance(request)
        context.update(extra_context or {})

        return TemplateResponse(
            request,
            'polls/admin/polls_admin_actions.html',
            context,
        )

    def has_add_permission(self, request):
        ''' disables the Add button on admin '''
        return False

    # every default view will redirect to change_list
    def add_view(self, *args, **kwargs):
        return HttpResponseRedirect(
            reverse_lazy('admin:polls_adminaction_changelist')
        )

    def delete_view(self, *args, **kwargs):
        return HttpResponseRedirect(
            reverse_lazy('admin:polls_adminaction_changelist')
        )

    def history_view(self, *args, **kwargs):
        return HttpResponseRedirect(
            reverse_lazy('admin:polls_adminaction_changelist')
        )

    def change_view(self, *args, **kwargs):
        return HttpResponseRedirect(
            reverse_lazy('admin:polls_adminaction_changelist')
        )
