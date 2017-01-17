from django.contrib import admin
from django.apps import apps

app = apps.get_app_config('autolims')
    
class RunAdmin(admin.ModelAdmin):

    #autoprotocol can only be set on creation
    def get_readonly_fields(self, request, obj=None):
        if obj is not None:
            return ['autoprotocol']
        return []    
    
    
for model_name, model in app.models.items():
    
    if model_name=='run':
        admin.site.register(model,RunAdmin)
    else:   
        admin.site.register(model)