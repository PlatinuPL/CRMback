from django import forms
from .models import Task, Client, ProductConfiguration, ClientFile,Meeting, Note, Payment, DocumentTemplate, Prelead
from django import forms

class PreleadForm(forms.ModelForm):
    class Meta:
        model = Prelead
        fields = ["first_name", "phone", "city", "postal_code"]
        widgets = {
            "first_name": forms.TextInput(attrs={"placeholder": "Imię"}),
            "phone": forms.TextInput(attrs={"placeholder": "Telefon"}),
            "city": forms.TextInput(attrs={"placeholder": "Miejscowość"}),
            "postal_code": forms.TextInput(attrs={"placeholder": "Kod pocztowy"}),
        }



class DocumentTemplateForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = ["name", "document_type", "file", "description"]


class PaymentForm(forms.ModelForm):
    invoice = forms.FileField(
        required=False,
        label="Faktura",
        help_text="Opcjonalnie, dodaj fakturę do tej płatności."
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Termin płatności"
    )
    class Meta:
        model = Payment
        fields = ["payment_type", "amount", "due_date", "status"]

class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["text", "is_important"]
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Wpisz treść notatki..."
            }),
            "is_important": forms.CheckboxInput(attrs={
                "class": "form-check-input",
                "id": "id_is_important"
            }),
        }
    labels = {
        "is_important": "Ważna notatka"
    }

class MeetingForm(forms.ModelForm):
    class Meta:
        model = Meeting
        fields = ["description", "meeting_date"]
        widgets = {
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Wprowadź opis spotkania"}),
            "meeting_date": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
        }

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["text", "due_date"]
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Wprowadź treść zadania",
                "required": "required"  # Dodajemy wymaganie dla pola text
            }),
            "due_date": forms.DateInput(attrs={
                "type": "datetime-local",  # Tylko data
                "class": "form-control",
                "required": "required"  # Dodajemy wymaganie dla pola due_date
            }),
        }

class ClientFileForm(forms.ModelForm):
    class Meta:
        model = ClientFile
        fields = ["file_type", "file", "description"]
        widgets = {
            "file_type": forms.Select(attrs={"class": "form-control"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({'multiple': True})


class ProductConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = ["attributes", "price", "unit"]
        widgets = {
            "attributes": forms.Textarea(attrs={"rows": 3, "placeholder": "Wpisz atrybuty w formacie JSON"}),
            "price": forms.NumberInput(attrs={"placeholder": "Cena"}),
        }

class ClientForm(forms.ModelForm):
    has_different_investment_address = forms.BooleanField(
        required=False,
        label="Czy adres inwestycji różni się od adresu klienta?"
    )

    class Meta:
        model = Client
        exclude = ['status', 'user', 'created_at', 'updated_at']  # Wyklucza pola, które nie powinny być edytowalne

    # Dodanie bardziej przejrzystego podziału na sekcje formularza
    def personal_data_fields(self):
        return [
            'first_name', 'last_name', 'phone', 'email', 'street', 'house_number',
            'city', 'postal_code', 'postal', 'pesel', 'id_card_number', "birth_date"
        ]

    def investment_fields(self):
        return [
            'has_different_investment_address', 'investment_street', 'investment_house_number', 'investment_postal_code',
            'current_heating_source', 'construction_permission_year', 'land_registry_number',
            'business_at_investment_address', 'potential'
        ]

    def application_fields(self):
        return [
            'income_threshold', 'household_members', 'farm_conversion_hectares',
            'income_per_person', 'marital_status', 'is_sole_owner', 'runs_business', 'has_joint_property'
        ]

    def agreement_fields(self):
        return [
            'agreement_number', 'agreement_date', 'prefinancing'
        ]

    def validate_required_fields(self, cleaned_data, required_fields):
        """
        Pomocnicza funkcja do walidacji wymaganych pól.
        """
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f"Pole '{self.fields[field].label}' jest wymagane.")

    def clean(self):
        cleaned_data = super().clean()
        # Jeśli milestone nie jest ustawione, ustaw na "lead"
        if not cleaned_data.get("milestone"):
            cleaned_data["milestone"] = "lead"
        # Walidacja wymaganych pól
        required_fields = ['first_name', 'last_name', 'phone']
        self.validate_required_fields(cleaned_data, required_fields)

        return cleaned_data
