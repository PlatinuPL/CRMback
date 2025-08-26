from django.contrib import admin
from .models import InformationPost, Client, ProductCategory, Product, ProductAttribute, SubsidyProgram, SubsidyOption, ProductCategory, Product, SubsidyProductCriteria, ProductConfiguration, ClientFile, DocumentTemplate, ProductDocumentRequirement, Notification, Prelead, Parcel
from image_cropping import ImageCroppingMixin
import json


class ParcelAdmin(admin.ModelAdmin):
    list_display = ('id', 'lead', 'voivodeship', 'county', 'town', 'plot_number', 'area', 'created_at')

class PreleadAdmin(admin.ModelAdmin):
    list_display = ("first_name", "phone", "city", "postal_code")
    search_fields = ("first_name", "phone", "city")
    list_filter = ("city",)

admin.site.register(Parcel, ParcelAdmin)
admin.site.register(Prelead, PreleadAdmin)  # <-- TO DODAJ




@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    
@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_type', 'created_at']
    search_fields = ['name']
    list_filter = ['document_type']

@admin.register(ProductDocumentRequirement)
class ProductDocumentRequirementAdmin(admin.ModelAdmin):
    list_display = ['product', 'document']
    search_fields = ['product__name', 'document__name']
    list_filter = ['document__document_type']

class ProductDocumentRequirementInline(admin.TabularInline):  
    model = ProductDocumentRequirement
    extra = 1  # Pozwala dodać jeden nowy wiersz domyślnie
    autocomplete_fields = ['document']
    verbose_name = "Wymagany dokument"
    verbose_name_plural = "Wymagane dokumenty"
    fields = ['document', 'required_placeholders']

@admin.register(SubsidyProgram)
class SubsidyProgramAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(SubsidyOption)
class SubsidyOptionAdmin(admin.ModelAdmin):
    list_display = ("name", "program")
    list_filter = ("program",)


@admin.register(SubsidyProductCriteria)
class SubsidyProductCriteriaAdmin(admin.ModelAdmin):
    list_display = ("option", "product", "max_subsidy_amount", "max_subsidy_percentage")
    list_filter = ("option", "product")

@admin.register(ProductConfiguration)
class ProductConfigurationAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_attributes', 'price', 'unit')
    list_filter = ('product', 'unit')
    search_fields = ('product__name', 'attributes')
    readonly_fields = ('get_attributes_as_dict',)
    fieldsets = (
        (None, {
            'fields': ('product', 'price', 'unit', 'get_attributes_as_dict')
        }),
        ('Atrybuty konfiguracji', {
            'fields': ('attributes',),
        }),
    )

    def get_attributes(self, obj):
        """Czytelne wyświetlanie atrybutów w kolumnie."""
        try:
            attributes_dict = obj.get_attributes_as_dict()
            return ", ".join(f"{key}: {value}" for key, value in attributes_dict.items())
        except json.JSONDecodeError:
            return "Błędne dane"
    get_attributes.short_description = "Atrybuty"


class ProductAttributeInline(admin.StackedInline):
    model = ProductAttribute
    extra = 1
    fields = ["name", "input_type", "placeholder", "options"]
    verbose_name = "Atrybut produktu"
    verbose_name_plural = "Atrybuty produktu"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "description","required_fields_offer"]

    inlines = [ProductDocumentRequirementInline]  # Powiązanie z dokumentami
    inlines = [ProductAttributeInline]
    



@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
@admin.register(InformationPost)
class InformationPostAdmin(ImageCroppingMixin, admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'mandatory_to_acknowledge')
    fields = ('author', 'title', 'content', 'image', 'cropping', 'mandatory_to_acknowledge', 'acknowledged_by')
    filter_horizontal = ('acknowledged_by',)  # Wspierane dla ManyToManyFieldpython manage.py makemigrations


class ClientFileInline(admin.TabularInline):
    """
    Umożliwia zarządzanie plikami klienta z poziomu widoku klienta.
    """
    model = ClientFile
    extra = 1  # Liczba pustych formularzy do dodania nowych plików
    fields = ('file_type', 'file', 'description', 'uploaded_at')  # Pola do wyświetlenia
    readonly_fields = ('uploaded_at',)  # Tylko do odczytu
    can_delete = True  # Możliwość usuwania plików


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Zarządzanie klientami.
    """
    list_display = ('first_name', 'last_name', 'phone', 'email', 'status', 'potential')
    search_fields = ('first_name', 'last_name', 'phone', 'email')
    list_filter = ('status', 'potential', 'person_type')
    readonly_fields = ('unique_id',)  # Pola tylko do odczytu
    inlines = [ClientFileInline]  # Dodanie plików jako podformularz w widoku klienta


@admin.register(ClientFile)
class ClientFileAdmin(admin.ModelAdmin):
    """
    Zarządzanie plikami klientów jako osobny model.
    """
    list_display = ('client', 'file_type', 'file', 'uploaded_at')
    search_fields = ('client__first_name', 'client__last_name', 'file_type')
    list_filter = ('file_type', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
