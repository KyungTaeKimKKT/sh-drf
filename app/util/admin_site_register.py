from django.apps import apps
from django.db import models
from django.contrib import admin

def admin_site_register(app_name:str):
    try:
        app = apps.get_app_config(app_name)  
        for model in app.get_models():
            # 이미 등록되어 있으면 건너뜀
            if model in admin.site._registry:
                continue
            # 모델의 필드 이름들을 리스트_display로 사용 (FK는 'field' 표시)
            field_names = []
            for f in model._meta.get_fields():
                # ManyToMany, reverse relations 제외
                if f.many_to_many or f.one_to_many:
                    continue
                # 표시 가능한 필드만 추가
                if isinstance(f, (models.Field,)):
                    field_names.append(f.name)

            # 기본 ModelAdmin 클래스 생성
            admin_class = type(
                f'{model.__name__}AutoAdmin',
                (admin.ModelAdmin,),
                {
                    'list_display': field_names[:20],  # 너무 길면 최대 20개로 제한
                    'list_filter': [f.name for f in model._meta.fields if isinstance(f, (models.BooleanField, models.ForeignKey, models.DateField, models.DateTimeField))],
                    'search_fields': [f.name for f in model._meta.fields if isinstance(f, (models.CharField, models.TextField))][:5],
                    'ordering': ('-pk',),
                    'list_display_links': (field_names[0],),  # 첫 번째 필드를 클릭하면 상세 페이지(수정)로 이동
                }
            )

            admin.site.register(model, admin_class)
    except Exception as e:
        print(f"Error registering admin site for {app_name}: {e}")




def admin_site_register_external(module_path: str, using: str):
    """
    외부 DB 모델 자동 등록.
    module_path: 예) 'app_name.models_외부'
    using: DATABASES alias 이름
    """
    try:
        module = __import__(module_path, fromlist=['*'])
        for name in dir(module):
            model = getattr(module, name)
            if not isinstance(model, type) or not issubclass(model, models.Model):
                continue
            if model in admin.site._registry:
                continue

            field_names = [
                f.name for f in model._meta.fields
                if not f.many_to_many and not f.one_to_many
            ]

            # DB alias를 강제로 지정하는 ModelAdmin 클래스 생성
            admin_class = type(
                f'{model.__name__}ExternalAdmin',
                (admin.ModelAdmin,),
                {
                    'using': using,
                    'list_display': field_names[:20],
                    'get_queryset': lambda self, req: super(
                        admin.ModelAdmin, self
                    ).get_queryset(req).using(self.using),
                    'save_model': lambda self, req, obj, form, ch: obj.save(using=self.using),
                    'delete_model': lambda self, req, obj: obj.delete(using=self.using),
                }
            )

            admin.site.register(model, admin_class)
    except Exception as e:
        print(f"[Admin register error] {module_path}: {e}")