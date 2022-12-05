"""
A module for retrieving data about Pokemon species.
"""

import difflib
import os
import sqlite3

from pokemon import Species, EvSet

__all__ = ['NoSuchSpecies', 'AmbiguousSpecies', 'AmbiguousForm', 'fetch_by_id', 'fetch_by_name', 'search']


_DB_FILE = os.path.join(os.path.dirname(__file__), 'pokedex.db')
_connection = sqlite3.connect(_DB_FILE)
_connection.row_factory = sqlite3.Row


class _SpeciesCache(object):
    """
    A very simple caching mechanism for database species records. There are
    kept in memory until requested again.
    """

    def __init__(self):
        self._cache = {'id': {}, 'name': {}}
        self.names = None

    def contains(self, field, value) -> bool:
        return field in self._cache and value in self._cache[field]

    def get(self, field, value) -> dict[str, Species]:
        return self._cache[field][value]

    def add(self, species: dict[str, Species]):
        first_species = list(species.values())[0]
        self._cache['id'][first_species.id] = species
        self._cache['name'][first_species.name.lower()] = species


_cache = _SpeciesCache()


class NoSuchSpecies(Exception):
    """Raised when a search for a Pokemon species fails."""

    def __init__(self, identifier):
        super(NoSuchSpecies, self).__init__()
        self.identifier = identifier


class AmbiguousSpecies(NoSuchSpecies):
    """Raised when several matches are found for a Pokemon name search."""

    def __init__(self, identifier, matches):
        super(AmbiguousSpecies, self).__init__(identifier)
        self.matches = [list(fetch_by_name(match).values())[0] for match in matches]


class AmbiguousForm(NoSuchSpecies):
    """Raised when several forms are found for a Pokemon name search."""

    def __init__(self, identifier, matches):
        super(AmbiguousForm, self).__init__(identifier)
        self.matches = matches


def _name_list():
    if _cache.names is None:
        _cache.names = [row[0] for row in _connection.execute('SELECT name FROM pokemon')]
    return _cache.names


def _fetch(field, value, sql: str) -> dict[str, Species]:
    # Attempt to retrieve species from the cache.
    if _cache.contains(field, value):
        return _cache.get(field, value)

    # On cache failure, query the database given the provided data.
    rows = _connection.execute(sql, (value,)).fetchall()
    if len(rows) == 0:
        raise NoSuchSpecies(value)
    species_forms: dict[str, Species] = {}
    for row in rows:
        # Build the Species object from the returned data.
        evs = EvSet(hp=row['ev_hp'],
                    attack=row['ev_attack'],
                    defense=row['ev_defense'],
                    special_attack=row['ev_special_attack'],
                    special_defense=row['ev_special_defense'],
                    speed=row['ev_speed'])
        species = Species(id=row['id'], name=row['name'], form=row['form'], evs=evs)

        species_forms[row['form'].lower()] = species
    _cache.add(species_forms)

    return species_forms


def fetch_by_id(species_id: int) -> dict[str, Species]:
    """
    Fetch a list of Species object from the pokedex by it's pokedex id. NoSuchSpecies
    will be raised if no match was found.
    """
    return _fetch('id', species_id,
                  '''SELECT p.id AS id, name, ev_hp, ev_attack, ev_defense,
                     ev_special_attack, ev_special_defense, ev_speed, form
                     FROM pokemon AS p
                     JOIN stats AS s ON p.id = s.pokemon_id
                     WHERE p.id = ?''')


def fetch_by_name(name: str) -> dict[str, Species]:
    """
    Fetch a list of Species object from the pokedex by it's name. The fetch is case
    insensitive. NoSuchSpecies will be raised if no match was found.
    """
    return _fetch('name', name.lower(),
                  '''SELECT p.id AS id, name, ev_hp, ev_attack, ev_defense,
                     ev_special_attack, ev_special_defense, ev_speed, form
                     FROM pokemon AS p
                     JOIN stats AS s ON p.id = s.pokemon_id
                     WHERE lower(name) = ?''')


def search(search_query: str | int):
    """
    Search for a Pokemon species by a string input. The input can be a string
    or integer value corresponding to the name or number of a species. If the
    string is a name, the search will attempt to find close matches as well
    as an exact match.

    Will raise NoSuchSpecies if no match is found, AmbiguousSpecies if
    there are close matches, AmbiguousForm if there are multiple forms if a valid one is not specified.
    """
    original_query = search_query
    form = ''
    if search_query.find('(') > -1:
        form_index = search_query.index('(') + 1
        end_form_index = search_query.index(')', form_index)
        form = search_query[form_index:end_form_index]
        search_query = search_query[0:form_index - 1].strip()

    is_id_query = type(search_query) == int or search_query.isdigit()
    if is_id_query:
        species_list = fetch_by_id(int(search_query))
    else:
        try:
            species_list = fetch_by_name(search_query)
        except NoSuchSpecies as e:
            # No exact match was found, try a fuzzy search.
            matches = difflib.get_close_matches(search_query, _name_list())
            if len(matches) == 0:
                raise e
            else:
                raise AmbiguousSpecies(search_query, matches)

    if len(species_list) == 1:
        return list(species_list.values())[0]
    if form.lower() in species_list:
        return species_list[form.lower()]
    form_list = []
    for form_id, species in species_list.items():
        form_list.append(search_query + ' (' + species.form + ')')

    raise AmbiguousForm(original_query, form_list)
