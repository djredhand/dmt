from django.forms import ModelForm
from .models import StatusUpdate, Node, User, Project, Milestone, Item


class StatusUpdateForm(ModelForm):
    class Meta:
        model = StatusUpdate
        fields = ['body']


class NodeUpdateForm(ModelForm):
    class Meta:
        model = Node
        fields = ['subject', 'body']


class UserUpdateForm(ModelForm):
    class Meta:
        model = User
        fields = ["fullname", "email", "type", "title", "phone",
                  "bio", "photo_url", "photo_width", "photo_height",
                  "campus", "building", "room"]


class ProjectUpdateForm(ModelForm):
    class Meta:
        model = Project
        exclude = ['pid', ]


class MilestoneUpdateForm(ModelForm):
    class Meta:
        model = Milestone
        exclude = ['mid', 'project', 'status']


class ItemUpdateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ItemUpdateForm, self).__init__(*args, **kwargs)
        item = kwargs['instance']
        milestone = item.milestone
        project_id = milestone.project.pk
        self.fields['milestone'].queryset = Milestone.objects.filter(project=project_id)

    class Meta:
        model = Item
        exclude = ['iid', 'owner',
                   'assigned_to', 'status', 'r_status', 'last_mod',
                   'tags', 'priority']
