from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Safely retrieve a value from a dictionary in Django templates.

    Args:
        dictionary (dict): Dictionary object passed from the view
        key (str): Key to retrieve

    Returns:
        Any: Value corresponding to the key, or None if not found
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter(name="zip_lists")
def zip_lists(a, b):
    """
    Zip two iterables together for parallel iteration in templates.

    Args:
        a (iterable): First list
        b (iterable): Second list

    Returns:
        zip: Iterator of paired elements
    """
    try:
        return zip(a, b)
    except TypeError:
        return []