from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from image_cropping import ImageRatioField
from PIL import Image
import re
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
import json
import uuid
import os
from django.utils.text import slugify
from django.db import models
from django.utils import timezone
from django.utils.timezone import now

class DocumentTemplate(models.Model):
    FILE_TYPE_CHOICES = [ 
        ("agreement", "Umowy"),
        ("document", "Dokumenty"),
        ("certificate", "Zaświadczenia"),
        ('invoice', 'Faktury'),
        ('report', 'Raporty'),
        ("other", "Inne"),
    ]

    name = models.CharField(max_length=255, verbose_name="Nazwa szablonu")
    document_type = models.CharField(max_length=50, choices=FILE_TYPE_CHOICES, verbose_name="Typ dokumentu")
    file = models.FileField(upload_to="document_templates/", verbose_name="Plik szablonu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data ostatniej aktualizacji")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    placeholders = models.JSONField(default=list, blank=True, verbose_name="Lista placeholderów")  # NOWE POLE

   

    def __str__(self):
        return f"{self.name} ({self.get_document_type_display()})"
    
class SubsidyProgram(models.Model):
    """Model dla programu dotacji."""
    name = models.CharField(max_length=255, verbose_name="Nazwa programu dotacyjnego")

    def __str__(self):
        return self.name


class SubsidyOption(models.Model):
    """Opcje dla programu dotacyjnego."""
    program = models.ForeignKey(SubsidyProgram, on_delete=models.CASCADE, related_name="options", verbose_name="Program dotacyjny")
    name = models.CharField(max_length=255, verbose_name="Nazwa opcji dotacyjnej")

    def __str__(self):
        return f"{self.program.name} - {self.name}"







class ProductConfiguration(models.Model):
    product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, related_name="configurations", verbose_name="Produkt"
    )
    attributes = models.TextField(verbose_name="Atrybuty konfiguracji")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena")
    unit = models.CharField(max_length=20, blank=True, null=True, verbose_name="Jednostka (np. zł/szt.)")
    def get_final_price(self):
        """Oblicza końcową cenę na podstawie atrybutów."""
        final_price = self.price
        try:
            attributes_dict = json.loads(self.attributes)  # Wczytanie atrybutów jako słownik
        except json.JSONDecodeError:
            return final_price  # Jeśli JSON jest błędny, zwracamy cenę bazową

        # Pobieramy powiązane atrybuty i sprawdzamy ich ceny
        for attr_name, attr_value in attributes_dict.items():
            attribute = ProductAttribute.objects.filter(product=self.product, name=attr_name).first()
            if attribute and attr_value.lower() == "tak":  # Jeśli atrybut jest aktywny
                final_price += attribute.price  # Dodajemy cenę atrybutu

        return final_price  # Zwracamy obliczoną cenę końcową
    def __str__(self):
        return f"Konfiguracja dla {self.product.name}: {self.attributes} - Cena: {self.price} {self.unit or ''}"

    def get_attributes_as_dict(self):
        """Zwraca atrybuty jako słownik JSON."""
        return json.loads(self.attributes)

    def set_attributes_from_dict(self, attributes_dict):
        """Ustawia atrybuty jako tekst JSON."""
        self.attributes = json.dumps(attributes_dict)


class ProductCategory(models.Model):
    name = models.CharField(max_length=255, verbose_name="Nazwa kategorii")

    def __str__(self):
        return self.name

class Product(models.Model):
    UNIT_CHOICES = [
        ('szt', 'Sztuka'),
        ('m2', 'Metr kwadratowy'),
    ]

    name = models.CharField(max_length=255, verbose_name="Nazwa produktu")
    description = models.TextField(blank=True, null=True, verbose_name="Opis produktu")  # Dodane pole
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name="products", verbose_name="Kategoria")
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, default='szt', verbose_name="Jednostka")  # Dodane pole
    required_fields_offer = models.JSONField(default=dict) # Lista wymaganych pól
    # Nowe pole - lista wymaganych dokumentów
    required_documents = models.ManyToManyField(
        DocumentTemplate,
        blank=True,
        related_name="products",
        verbose_name="Wymagane dokumenty"
    )

    def __str__(self):
        return self.name


class ProductDocumentRequirement(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="document_requirements")
    document = models.ForeignKey(DocumentTemplate, on_delete=models.CASCADE, related_name="product_requirements")
    required_placeholders = models.JSONField(default=list, verbose_name="Wymagane placeholdery")

    class Meta:
        unique_together = ("product", "document")  # Unikalność dla pary produkt-dokument

    def __str__(self):
        return f"{self.product.name} - {self.document.name}"

class SubsidyProductCriteria(models.Model):
    """Model dla kryteriów produktów w ramach opcji dotacyjnej."""
    option = models.ForeignKey(SubsidyOption, on_delete=models.CASCADE, related_name="product_criteria", verbose_name="Opcja dotacyjna")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="subsidy_criteria", verbose_name="Produkt")
    max_subsidy_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Maksymalna kwota dofinansowania", null=True, blank=True)
    max_subsidy_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Maksymalny procent dofinansowania", null=True, blank=True)
    second_max_subsidy_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Maksymalna kwota drugiego dofinansowania", null=True, blank=True)
    second_max_subsidy_percentage = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Maksymalny procent drugiego dofinansowania", null=True, blank=True)

    def __str__(self):
        criteria = []

        # Pierwszy próg dofinansowania
        if self.max_subsidy_amount:
            criteria.append(f"Kwota 1: {self.max_subsidy_amount} zł")
        if self.max_subsidy_percentage:
            criteria.append(f"Nie więcej niż {self.max_subsidy_percentage}%")

        # Drugi próg dofinansowania
        if self.second_max_subsidy_amount:
            criteria.append(f"Kwota 2: {self.second_max_subsidy_amount} zł")
        if self.second_max_subsidy_percentage:
            criteria.append(f"Nie więcej niż {self.second_max_subsidy_percentage}%")

        return f"{self.option.name} - {self.product.name} ({', '.join(criteria)})"


class ProductAttribute(models.Model):
    product = models.ForeignKey(
        "Product",
        related_name="attributes",
        on_delete=models.CASCADE,
        verbose_name="Produkt"
    )
    name = models.CharField(max_length=100, verbose_name="Nazwa atrybutu")
    input_type = models.CharField(
        max_length=20,
        choices=[("text", "Pole tekstowe"), ("dropdown", "Lista rozwijana")],
        default="text",
        verbose_name="Typ wejścia",
    )
    placeholder = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Placeholder"
    )
    options = models.TextField(
        blank=True,
        null=True,
        help_text="Opcje dla listy rozwijanej, oddzielone przecinkami",
        verbose_name="Opcje"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Cena atrybutu"
    )
    def __str__(self):
        return f"{self.name} ({self.input_type})"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        verbose_name="Zdjęcie profilowe"
    )
    first_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Imię"
    )
    last_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Nazwisko"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Numer telefonu"
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name="Adres"
    )
    current_contract_number = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        default="1",  # ✅ Domyślnie "1"
        verbose_name="Aktualny numer umowy"
    )

    def __str__(self):
        return f"Profil użytkownika: {self.user.username}"
    
def validate_land_registry_number(value):
    """
    Waliduje numer księgi wieczystej w formacie PO1S/00012345/4.
    """
    pattern = r'^[A-Z]{2}\d[A-Z]{1}/\d{6,8}/\d$'
    if not re.match(pattern, value):
        raise ValidationError(
            "Numer księgi wieczystej musi być w formacie 'PO1S/00012345/4', gdzie 'PO' to dwie wielkie litery, '1' to cyfra, 'S' to wielka litera, '00012345' to numer, a '4' to cyfra kontrolna."
        )
        
class Client(models.Model):
    # Indywidualne ID
    unique_id = models.UUIDField(
        default=uuid.uuid4,  # Automatyczne generowanie unikalnego ID
        editable=False,      # Nie można edytować w formularzu
        unique=True,         # Gwarancja unikalności
        verbose_name="Indywidualne ID"
    )
    # Dane podstawowe
    first_name = models.CharField(
        max_length=50,
        verbose_name="Imię",
        validators=[
            RegexValidator(r'^[A-Za-z]+$', "Imię może zawierać tylko litery.")
        ],
    )
    last_name = models.CharField(
        max_length=50,
        verbose_name="Nazwisko",
        validators=[
            RegexValidator(r'^[A-Za-z]+$', "Nazwisko może zawierać tylko litery.")
        ],
    )
    phone = models.CharField(
        max_length=15,
        verbose_name="Telefon",
        validators=[
            RegexValidator(r'^\+?[0-9\s-]+$', "Numer telefonu może zawierać tylko cyfry, spacje, myślniki i opcjonalny znak '+'.")
        ],
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="Data urodzenia")  # Nowe pole
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Handlowiec", related_name="clients")
    # Oferta finalna
    final_offer = models.OneToOneField(
        "Offer",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="finalized_by_client",
        verbose_name="Finalna oferta"
    )

    # Wartości finansowe
    contract_value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Wartość umowy", blank=True, null=True)
    margin = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Marża", blank=True, null=True)

    # Adres
    street = models.CharField(max_length=100, verbose_name="Ulica", blank=True, null=True)
    house_number = models.CharField(max_length=20, verbose_name="Numer domu", blank=True, null=True)
    city = models.CharField(max_length=100, verbose_name="Miejscowość", blank=True, null=True)
    postal_code = models.CharField(max_length=10, verbose_name="Kod pocztowy", blank=True, null=True)
    postal = models.CharField(max_length=100, verbose_name="Poczta", blank=True, null=True)
    # Adres inwestycji
    has_different_investment_address = models.BooleanField(
        default=False,
        verbose_name="Czy adres inwestycji różni się od adresu klienta?",
    )
    investment_street = models.CharField(max_length=100, verbose_name="Ulica (adres inwestycji)", blank=True, null=True)
    investment_house_number = models.CharField(max_length=20, verbose_name="Numer domu (adres inwestycji)", blank=True, null=True)
    investment_postal_code = models.CharField(max_length=10, verbose_name="Kod pocztowy (adres inwestycji)", blank=True, null=True)
    # Informacje dodatkowe
    current_heating_source = models.CharField(max_length=100, verbose_name="Aktualne źródło ogrzewania", blank=True, null=True)
    nip = models.CharField(max_length=10, verbose_name="NIP", blank=True, null=True)
    pesel = models.CharField(max_length=11, verbose_name="PESEL", blank=True, null=True)
    id_card_number = models.CharField(max_length=9, verbose_name="Numer dowodu osobistego", blank=True, null=True)
    PERSON_TYPE_CHOICES = [
    ('individual', 'Osoba fizyczna'),
    ('business', 'Firma'),
]

    person_type = models.CharField(
        max_length=20,
        choices=PERSON_TYPE_CHOICES,
        default='individual',
        verbose_name="Typ klienta"
    )

    # Informacje o umowie
    agreement_number = models.CharField(max_length=50, verbose_name="Numer umowy", unique=True, blank=True, null=True)
    agreement_date = models.DateField(verbose_name="Data zawarcia umowy", blank=True, null=True)

    # Program "Czyste Powietrze"
    INCOME_CHOICES = [
        ('basic', 'Podstawowy'),
        ('elevated', 'Podwyższony'),
        ('highest', 'Najwyższy'),
    ]
    income_threshold = models.CharField(
        max_length=10,
        choices=INCOME_CHOICES,
        default='basic',
        verbose_name="Próg dochodowy",
    )
    household_members = models.IntegerField(verbose_name="Ilość osób w gospodarstwie domowym", blank=True, null=True)
    farm_conversion_hectares = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Ilość hektarów przeliczeniowych",
        blank=True,
        null=True,
        validators=[
            MinValueValidator(0, message="Wartość nie może być mniejsza niż 0."),
            MaxValueValidator(200, message="Wartość nie może być większa niż 200."),
        ],
    )
    income_per_person = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Dochód na osobę", blank=True, null=True)

    # Informacje prawne
    marital_status = models.CharField(
        max_length=50,
        choices=[
            ("single", "Kawaler/Panna"),
            ("married", "Żonaty/Zamężna"),
            ("divorced", "Rozwiedziony/Rozwiedziona"),
            ("widowed", "Wdowiec/Wdowa"),
        ],
        verbose_name="Stan cywilny",
        blank=True,
        null=True,
    )
    is_sole_owner = models.BooleanField(default=False, verbose_name="Jedyny właściciel", blank=True, null=True)
    runs_business = models.BooleanField(default=False, verbose_name="Czy prowadzi działalność gospodarczą", blank=True, null=True)
    has_joint_property = models.BooleanField(default=False, verbose_name="Czy posiada wspólność majątkową z żoną", blank=True, null=True)
    business_at_investment_address = models.BooleanField(default=False, verbose_name="Czy działalność prowadzona jest pod adresem inwestycji", blank=True, null=True)

    prefinancing = models.BooleanField(default=False, verbose_name="Prefinansowanie")  # Nowe pole

    STATUS_CHOICES = [
        ('lead', 'Lead'),
        ('offer', 'Oferta'),
        ('client', 'Klient'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='lead',
        verbose_name="Status",
    )
    POTENTIAL_CHOICES = [
        ('low', 'Niski'),
        ('medium', 'Średni'),
        ('high', 'Wysoki'),
        ('very_high', 'Bardzo wysoki'),
    ]
    potential = models.CharField(
        max_length=10,
        choices=POTENTIAL_CHOICES,
        default='low',
        verbose_name="Potencjał",
    )
    construction_permission_year = models.IntegerField(
        verbose_name="Rok pozwolenia na budowę",
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1800, message="Rok nie może być wcześniejszy niż 1800."),
            MaxValueValidator(datetime.now().year, message="Rok nie może być późniejszy niż bieżący rok."),
        ],
    )
    land_registry_number = models.CharField(
        max_length=50,
        verbose_name="Numer księgi wieczystej",
        blank=True,
        null=True,
        validators=[validate_land_registry_number],
    )
    plot_number = models.CharField(
        max_length=50,
        verbose_name="Numer działki",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Data aktualizacji")

    MILESTONE_CHOICES = [
        ("lead", "Lead"),
        ("offer", "Oferta"),
        ("agreement", "Umowa"),
        ("prefinancing_request", "Wniosek o prefinansowanie"),
        ("realization", "Realizacja"),
        ("second_tranche_request", "Wniosek o drugą transzę"),
        ("completed", "Zakończono"),
    ]


    milestone = models.CharField(
        max_length=50,
        choices=MILESTONE_CHOICES,
        default="lead",
        verbose_name="Etap klienta",
    )

    
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    def save(self, *args, **kwargs):
                # Sprawdzamy, czy edytujemy istniejącego klienta
        if self.pk:
            old_client = Client.objects.get(pk=self.pk)
            changes = {}

            # Sprawdzamy, jakie pola zostały zmienione
            for field in ["first_name", "last_name", "email", "phone", "pesel", "birth_date"]:
                old_value = getattr(old_client, field)
                new_value = getattr(self, field)
                if old_value != new_value:
                    changes[field] = {"old": old_value, "new": new_value}

            # Jeśli są zmiany, zapisujemy log
            if changes:
                ActivityLog.objects.create(
                    user=self.modified_by,  # Trzeba przekazać użytkownika w widoku
                    client=self,
                    action_type="edit_client",
                    description=f"Edytowano dane klienta: {changes}"
                )
        # Normalizacja numeru PESEL (usuwa spacje)
        if self.pesel:
            self.pesel = self.pesel.strip()

        # Jeśli nie podano daty urodzenia, spróbuj ją pobrać z PESEL-u
        if not self.birth_date and self.pesel:
            extracted_date = extract_birth_date_from_pesel(self.pesel)
            if extracted_date:
                self.birth_date = extracted_date
            else:
                raise ValidationError("Nie można odczytać daty urodzenia z podanego numeru PESEL.")

        super().save(*args, **kwargs)
    
    

    def clean(self):
        """
        Dodatkowa walidacja w modelu.
        """
        if not self.first_name:
            raise ValidationError({'first_name': "Pole 'Imię' jest wymagane."})
        if not self.last_name:
            raise ValidationError({'last_name': "Pole 'Nazwisko' jest wymagane."})
        if not self.phone:
            raise ValidationError({'phone': "Pole 'Telefon' jest wymagane."})

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.phone}"

# Notatki
class Note(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='notes')
    text = models.TextField(verbose_name="Notatka")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    is_important = models.BooleanField(default=False, verbose_name="Ważna notatka")  # Nowe pole

# ✅ Model Task z zapisem czasu ukończenia zadania
class Task(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='tasks')
    text = models.TextField(verbose_name="Treść zadania")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    due_date = models.DateTimeField(verbose_name="Termin realizacji", blank=True, null=True)
    completed = models.BooleanField(default=False, verbose_name="Czy ukończone")  
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Data ukończenia")  # NOWE POLE

    def is_overdue(self):
        """Sprawdza, czy zadanie jest przeterminowane"""
        return self.due_date and self.due_date < timezone.now() and not self.completed



# ✅ Model Meeting z zapisem czasu dodania notatki
class Meeting(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='meetings')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    description = models.TextField(verbose_name="Opis")
    meeting_date = models.DateTimeField(verbose_name="Data spotkania")
    occurred = models.BooleanField(default=False, verbose_name="Czy spotkanie się odbyło?")
    note = models.TextField(verbose_name="Notatka", blank=True, null=True)  
    note_added_at = models.DateTimeField(blank=True, null=True, verbose_name="Data dodania notatki")  # NOWE POLE

    def save(self, *args, **kwargs):
        """Automatycznie zapisuje czas dodania notatki, jeśli zostanie uzupełniona"""
        if self.note and not self.note_added_at:
            self.note_added_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Spotkanie {self.client} - {self.meeting_date.strftime('%d.%m.%Y %H:%M')}"

class ActivityLog(models.Model):
    ACTION_TYPES = [
        ("edit_client", "Edytował/a dane klienta"),
        ("add_task", "Dodał/a zadanie"),
        ("add_offer", "Dodał/a ofertę"),
        ("add_meeting", "Dodał/a spotkanie"),
        ("add_note", "Dodał/a notatkę"),
        ("add_payment", "Dodał/a płatność"),
        ("add_file", "Dodał/a plik"),
        ("add_post", "Dodał/a post informacyjny"),
        ("update_milestone", "Zaktualizował/a kamień milowy"),
        ("generate_document", "Wygenerował/a dokument"),
        ("generate_offer", "Wygenerował/a ofertę"),
        ("mark_as_paid", "Oznaczył/a jako opłacone"),
        ("add_offer_file", "Dodał/a plik do oferty"),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Użytkownik wykonujący akcję")
    client = models.ForeignKey("Client", on_delete=models.CASCADE, null=True, blank=True, related_name="activities", verbose_name="Powiązany klient")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="Typ akcji")
    description = models.TextField(verbose_name="Opis zmiany")
    timestamp = models.DateTimeField(default=now, verbose_name="Data i czas")

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.user} - {self.timestamp.strftime('%d.%m.%Y %H:%M')}"

# Płatności
class Payment(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='payments')

    PAYMENT_TYPE_CHOICES = [
        ('client', 'Klient'),
        ('bank', 'Bank'),
        ('fund', 'Fundusz'),
    ]
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, verbose_name="Rodzaj płatności")

    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota")
    due_date = models.DateField(verbose_name="Termin płatności")
    payment_date = models.DateField(verbose_name="Data zapłaty", blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Oczekująca'),
        ('paid', 'Opłacona'),
        ('overdue', 'Zaległa'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Status płatności")


    invoice_file = models.ForeignKey(
        "ClientFile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        verbose_name="Faktura"
    )
    note = models.TextField(blank=True, null=True, verbose_name="Notatka")

    def __str__(self):
        return f"{self.client} - {self.amount} zł - {self.get_status_display()}"


# ✅ Model Task z zapisem czasu ukończenia zadania
class Task(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='tasks')
    text = models.TextField(verbose_name="Treść zadania")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    added_date = models.DateTimeField(auto_now_add=True, verbose_name="Data dodania")
    due_date = models.DateTimeField(verbose_name="Termin realizacji", blank=True, null=True)
    completed = models.BooleanField(default=False, verbose_name="Czy ukończone")  
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name="Data ukończenia")  # NOWE POLE

    def is_overdue(self):
        """Sprawdza, czy zadanie jest przeterminowane"""
        return self.due_date and self.due_date < timezone.now() and not self.completed

    def mark_as_completed(self):
        """Ustawia zadanie jako ukończone i zapisuje czas zakończenia"""
        self.completed = True
        self.completed_at = timezone.now()
        self.save()

# ✅ Model Meeting z zapisem czasu dodania notatki
class Meeting(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='meetings')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    description = models.TextField(verbose_name="Opis")
    meeting_date = models.DateTimeField(verbose_name="Data spotkania")
    occurred = models.BooleanField(default=False, verbose_name="Czy spotkanie się odbyło?")
    note = models.TextField(verbose_name="Notatka", blank=True, null=True)  
    note_added_at = models.DateTimeField(blank=True, null=True, verbose_name="Data dodania notatki")  # NOWE POLE

    def save(self, *args, **kwargs):
        """Automatycznie zapisuje czas dodania notatki, jeśli zostanie uzupełniona"""
        if self.note and not self.note_added_at:
            self.note_added_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Spotkanie {self.client} - {self.meeting_date.strftime('%d.%m.%Y %H:%M')}"





def client_file_path(instance, filename):
    """
    Tworzy dynamiczną ścieżkę do przechowywania plików klienta.
    Przykład: client_files/{client_id}/{typ_pliku}/{oryginalna_nazwa_pliku}
    """
    client_id = instance.client.unique_id
    file_type = slugify(instance.file_type)
    return f"client_files/{client_id}/{file_type}/{filename}"


class ClientFile(models.Model):
    FILE_TYPE_CHOICES = [
        ("agreement", "Umowy"),
        ("document", "Dokumenty"),
        ("certificate", "Zaświadczenia"),
        ("photo", "Zdjęcia"),
        ("offer", "Oferty"),
        ('invoice', 'Faktury'),
        ('report', 'Raporty'),
        ("other", "Inne"),
    ]
    file_type = models.CharField(
        max_length=50,
        choices=FILE_TYPE_CHOICES,
        default="other",
        verbose_name="Typ pliku",
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="Klient",
    )

    offer = models.ForeignKey(
        "Offer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="files",
        verbose_name="Powiązana oferta"
    )
    file = models.FileField(
        upload_to=client_file_path,
        verbose_name="Plik",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data przesłania",
    )
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Autor")
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Opis pliku",
    )

    def __str__(self):
        return f"{self.client} - {self.get_file_type_display()} ({os.path.basename(self.file.name)})"


class InformationPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    title = models.CharField(max_length=255, verbose_name="Tytuł")
    content = models.TextField(verbose_name="Treść")
    image = models.ImageField(upload_to='information_posts/', blank=True, null=True, verbose_name="Zdjęcie")
    cropping = ImageRatioField('image', '16x9')  # Definicja pola cropping
    mandatory_to_acknowledge = models.BooleanField(default=False, verbose_name="Wymaga potwierdzenia zapoznania")
    acknowledged_by = models.ManyToManyField(User, blank=True, related_name="acknowledged_posts", verbose_name="Potwierdzono przez")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Utworzono")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Zaktualizowano")
    
    def __str__(self):
        return self.title


    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.cropping and self.image:
            # Współrzędne kadru (x0, y0, x1, y1)
            x0, y0, x1, y1 = map(int, self.cropping.split(','))

            with Image.open(self.image.path) as img:
                cropped_image = img.crop((x0, y0, x1, y1))
                cropped_image.save(self.image.path)

class Offer(models.Model):
    STATUS_CHOICES = [
        ("draft", "Szkic"),
        ("sent", "Wysłana"),
        ("accepted", "Zaakceptowana"),
        ("rejected", "Odrzucona"),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    client = models.ForeignKey("Client", on_delete=models.CASCADE, related_name="offers", verbose_name="Klient")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", verbose_name="Status oferty")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Całkowita kwota", default=0)
    must_payment = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Kwota do zapłaty", default=0)
    total_margin = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Całkowita marża", default=0)  # Nowe pole
    additional_terms = models.TextField(verbose_name="Dodatkowe ustalenia", blank=True, null=True)  # Nowe pole
    
    def __str__(self):
        return f"Oferta {self.id} - {self.client}"

class OfferProduct(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="products", verbose_name="Oferta")
    product = models.ForeignKey("Product", on_delete=models.CASCADE, verbose_name="Produkt")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Ilość")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena jednostkowa")
    vat_rate = models.PositiveIntegerField(default=23, verbose_name="Stawka VAT")
    required_documents = models.ManyToManyField("DocumentTemplate", blank=True, verbose_name="Wymagane dokumenty")

    def __str__(self):
        return f"{self.product.name} ({self.quantity} szt.)"
    
def extract_birth_date_from_pesel(pesel):
    """
    Pobiera datę urodzenia z numeru PESEL, jeśli to możliwe.
    Zwraca obiekt datetime.date lub None, jeśli nie można odczytać.
    """
    if len(pesel) != 11 or not pesel.isdigit():
        return None  # Niepoprawny PESEL

    year = int(pesel[:2])  # Pierwsze dwie cyfry PESEL to rok urodzenia
    month = int(pesel[2:4])  # Kolejne dwie to miesiąc urodzenia
    day = int(pesel[4:6])  # Kolejne dwie to dzień urodzenia

    # Sprawdzenie dekady na podstawie miesiąca urodzenia
    if 1 <= month <= 12:
        year += 1900  # Osoby urodzone w latach 1900-1999
    elif 21 <= month <= 32:
        year += 2000  # Osoby urodzone w latach 2000-2099
        month -= 20
    elif 41 <= month <= 52:
        year += 2100  # Osoby urodzone w latach 2100-2199
        month -= 40
    elif 61 <= month <= 72:
        year += 2200  # Osoby urodzone w latach 2200-2299
        month -= 60
    elif 81 <= month <= 92:
        year += 1800  # Osoby urodzone w latach 1800-1899
        month -= 80
    else:
        return None  # Niepoprawny miesiąc → PESEL błędny

    # Walidacja poprawności daty
    try:
        birth_date = datetime(year, month, day).date()
        return birth_date
    except ValueError:
        return None  # Niepoprawna data (np. 31 lutego)

class Notification(models.Model):
    CRITICAL = 'critical'
    INFO = 'info'
    WARNING = 'warning'

    NOTIFICATION_TYPES = [
        (CRITICAL, 'Krytyczne'),
        (INFO, 'Informacja'),
        (WARNING, 'Ostrzeżenie'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default=INFO)
    is_read = models.BooleanField(default=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")  # Odbiorca powiadomienia
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, null=True)  # Dodaj tytuł powiadomienia
    message = models.TextField()


    def __str__(self):
        return f"[{self.notification_type.upper()}] {self.message[:50]}"

from django.db import models
from django.core.validators import RegexValidator

class Prelead(models.Model):
    # Dane podstawowe
    first_name = models.CharField(
        max_length=50,
        verbose_name="Imię",
        validators=[
            RegexValidator(r'^[A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ\s-]+$', "Imię może zawierać tylko litery.")
        ],
    )

    last_name = models.CharField(
        max_length=50,
        verbose_name="Nazwisko",
        validators=[
            RegexValidator(r'^[A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ\s-]+$', "Nazwisko może zawierać tylko litery.")
        ], blank=True, null=True)
    email = models.EmailField(verbose_name="Email", blank=True, null=True)

    phone = models.CharField(
        max_length=15,
        verbose_name="Telefon",
        validators=[
            RegexValidator(r'^\+?[0-9\s-]+$', "Numer telefonu może zawierać tylko cyfry, spacje, myślniki i opcjonalny znak '+'.")
        ],
    )

    city = models.CharField(max_length=100, verbose_name="Miejscowość", blank=True, null=True)
    postal_code = models.CharField(max_length=10, verbose_name="Kod pocztowy", blank=True, null=True)

    note = models.TextField(verbose_name="Notatka", blank=True, null=True)
    log = models.TextField(blank=True, null=True)  # nowe pole na logi
    POTENTIAL_CHOICES = [
        ('low', 'Niski'),
        ('medium', 'Średni'),
        ('high', 'Wysoki'),
        ('very_high', 'Bardzo wysoki'),
    ]
    potential = models.CharField(
        max_length=10,
        choices=POTENTIAL_CHOICES,
        default='medium',
        verbose_name="Potencjał"
    )
    STATUS_CHOICES = [
        ('ST', 'ST'),
        ('NO1', 'NO1'),
        ('NO2', 'NO2'),
        ('NO3', 'NO3'),
        ('NN', 'NN'),
        ('NN2', 'NN2'),
        ('NUM', 'NUM'),
        ('UM', 'UM'),
        ('PR', 'PR')
    ]
    status = models.CharField(
        max_length=4,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Status"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Handlowiec", related_name='preleads', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Parcel(models.Model):
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    lead = models.ForeignKey(Prelead, related_name='parcels', on_delete=models.CASCADE)
    voivodeship = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    precinct = models.CharField(max_length=100)
    plot_number = models.CharField(max_length=100)
    area = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

