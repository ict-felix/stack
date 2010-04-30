from django.db import models
from clearinghouse.extendable.models import Extendable
from clearinghouse.slice.models import Slice
from clearinghouse.project.models import Project
from django.contrib import auth
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

class Aggregate(Extendable):
    '''
    Holds information about an aggregate. Needs to be extended by plugins.
    
    @param name: human-readable name of the Aggregate
    @type name: L{str}
    '''
    
    name = models.CharField(max_length=200, unique=True)
    logo = models.ImageField('Logo', upload_to=settings.AGGREGATE_LOGOS_DIR,
                             blank=True, null=True)
    description = models.TextField()
    location = models.CharField("Location", max_length=200)
    available = models.BooleanField("Available", default=False)
    
    class Extend:
        fields = {
            'admins_info': (
                models.ManyToManyField,
                ("AggregateAdminInfo",),
                {"verbose_name": "Info about users allowed to administer the aggregate"},
                ("admin_info_class",),
                {'through': 'admin_info_through',
                 'verbose_name': "admins_comment",},
            ),
            'users_info': (
                models.ManyToManyField,
                ("AggregateUserInfo",),
                {"verbose_name": "Info about users allowed to use aggregate"},
                ("user_info_class",),
                {'through': 'user_info_through',
                 "verbose_name":  "users_comment"},
            ),
            'slices_info': (
                models.ManyToManyField,
                ("AggregateSliceInfo",),
                {"verbose_name":  "Info on slices using the aggregate"},
                ("slice_info_class",),
                {'through': 'slice_info_through',
                 'verbose_name': "slices_comment"},
            ),
            'projects_info': (
                models.ManyToManyField,
                ("AggregateProjectInfo",),
                {'verbose_name': "Info on projects using the aggregate"},
                ("project_info_class",),
                {'through': 'project_info_through',
                 'verbose_name':  "projects_comment"},
            ),
        }
        
    class Meta:
        verbose_name = "Generic Aggregate"

    def get_logo_url(self):
        try:
            return self.logo.url
        except:
            return ""
        
    def get_edit_url(self):
        ct = ContentType.objects.get_for_model(self.__class__)
        return reverse("%s_aggregate_edit" % ct.app_label,
                       kwargs={'obj_id': self.id})

    @classmethod
    def get_create_url(cls):
        ct = ContentType.objects.get_for_model(cls)
        return reverse("%s_aggregate_create" % ct.app_label)

class AggregateUserInfo(Extendable):
    '''
    Generic additional information about a user to use the aggregate.
    
    @param user: user to which this info relates
    @type user: One-to-one mapping to L{auth.models.User}
    @param aggregates: aggregates which the owner of this info can use
    @type aggregates: L{models.ManyToManyField} to L{Aggregate}
    '''

    class Extend:
        fields = {
            'aggregates': (
                models.ManyToManyField,
                (Aggregate,),
                {'verbose_name': "Aggregates the user is allowed to use"},
                ("aggregate_class",),
                {'through': 'aggregates_through',
                 'verbose_name': "aggregates_comment"},
            ),
            'user': (
                models.OneToOneField,
                (auth.models.User,),
                {"verbose_name": "User to which this info relates"},
                (None,),
                {"verbose_name":  "user_comment"},
            ),
        }
        
    class Meta:
        abstract = True

class AggregateAdminInfo(Extendable):
    
    class Extend:
        fields = {
            'aggregates': (
                models.ManyToManyField,
                (Aggregate,),
                {'verbose_name': "Aggregates the user is allowed to administer"},
                ("aggregate_class",),
                {'through': 'aggregates_through',
                 'verbose_name':  "aggregates_comment"},
            ),
            'user': (
                models.OneToOneField,
                (auth.models.User,),
                {"verbose_name":  "User to which this info relates"},
                (None,),
                {"vebose_name": "user_comment"},
            ),
        }
        
    class Meta:
        abstract = True
        
class AggregateSliceInfo(Extendable):
    
    class Extend:
        fields = {
            'aggregates': (
                models.ManyToManyField,
                (Aggregate,),
                {'verbose_name': "Aggregates the slice is allowed to use"},
                ("aggregate_class",),
                {'through': 'aggregates_through',
                 'verbose_name': "aggregates_comment"},
            ),
            'slice': (
                models.OneToOneField,
                (Slice,),
                {"verbose_name": "Slice to which this info relates"},
                (None,),
                {"verbose_name": "slice_comment"},
            ),
        }
        
    class Meta:
        abstract = True
        
class AggregateProjectInfo(Extendable):
    
    class Extend:
        fields = {
            'aggregates': (
                models.ManyToManyField,
                (Aggregate,),
                {'verbose_name': "Aggregates the project is allowed to use"},
                ("aggregate_class",),
                {'through': 'aggregates_through',
                 'verbose_name': "aggregates_comment"},
            ),
            'project': (
                models.OneToOneField,
                (Project,),
                {"verbose_name":  "Project to which this info relates"},
                (None,),
                {"verbose_name": "project_comment"},
            ),
        }
        
    class Meta:
        abstract = True
        
