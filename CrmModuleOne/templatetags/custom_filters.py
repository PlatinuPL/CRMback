from django import template
import json  # Dodaj ten import na początku pliku

register = template.Library()

@register.filter
def field_group(form, fields):
    """
    Renderuje wybrane pola formularza jako HTML.
    """
    return ''.join(str(form[field]) for field in fields if field in form.fields)

@register.filter
def get_by_id(queryset, id):
    """
    Filtr zwraca obiekt z querysetu na podstawie ID.
    """
    try:
        return queryset.get(id=id)
    except queryset.model.DoesNotExist:
        return None
    

    
@register.filter
def get_key(dictionary, key):
    try:
        return json.loads(dictionary).get(key, "")
    except (ValueError, TypeError, AttributeError):
        return ""
    

@register.filter
def format_number(value):
    try:
        return "{:,.2f}".format(value).replace(",", " ").replace(".", ",")
    except (ValueError, TypeError):
        return value
    
@register.filter
def get_item(dictionary, key):
    """ Pobiera wartość ze słownika dla danego klucza """
    return dictionary.get(key, [])