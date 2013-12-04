from annoying.decorators import render_to
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from .models import Project, Milestone, Item


class AllProjectsView(TemplateView):
    template_name = 'main/all_projects.html'

    def get_context_data(self, **kwargs):
        return dict(projects=Project.objects.all())


class ProjectView(DetailView):
    template_name = 'main/project.html'
    model = Project
    context_object_name = 'project'


@render_to('main/milestone.html')
def milestone(request, id):
    m = get_object_or_404(Milestone, mid=id)
    return dict(milestone=m)


@render_to('main/item.html')
def item(request, id):
    i = get_object_or_404(Item, iid=id)
    return dict(item=i)
