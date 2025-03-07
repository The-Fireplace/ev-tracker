import difflib

import config


def get_power_item_effort():
    return 8 if config.instance.double_power_items_effort() else 4


def get_berry_reduction_amount(current_stat):
    return current_stat - 100 if config.instance.berry_reduction_cuts_to_100() and current_stat > 100 else 10


ITEMS = {
    'Macho Brace': lambda evs: evs * 2,
    'Power Weight': lambda evs: evs + EvSet(hp=get_power_item_effort()),
    'Power Bracer': lambda evs: evs + EvSet(attack=get_power_item_effort()),
    'Power Belt': lambda evs: evs + EvSet(defense=get_power_item_effort()),
    'Power Lens': lambda evs: evs + EvSet(special_attack=get_power_item_effort()),
    'Power Band': lambda evs: evs + EvSet(special_defense=get_power_item_effort()),
    'Power Anklet': lambda evs: evs + EvSet(speed=get_power_item_effort()),
}

VITAMINS = {
    'HP Up': lambda evs: evs + EvSet(hp=10),
    'Protein': lambda evs: evs + EvSet(attack=10),
    'Iron': lambda evs: evs + EvSet(defense=10),
    'Calcium': lambda evs: evs + EvSet(special_attack=10),
    'Zinc': lambda evs: evs + EvSet(special_defense=10),
    'Carbos': lambda evs: evs + EvSet(speed=10),
    'Health Feather': lambda evs: evs + EvSet(hp=1),
    'Muscle Feather': lambda evs: evs + EvSet(attack=1),
    'Resist Feather': lambda evs: evs + EvSet(defense=1),
    'Genius Feather': lambda evs: evs + EvSet(special_attack=1),
    'Clever Feather': lambda evs: evs + EvSet(special_defense=1),
    'Swift Feather': lambda evs: evs + EvSet(speed=1),
    'Pomeg Berry': lambda evs: evs - EvSet(hp=get_berry_reduction_amount(evs.hp)),
    'Kelpsy Berry': lambda evs: evs - EvSet(attack=get_berry_reduction_amount(evs.attack)),
    'Qualot Berry': lambda evs: evs - EvSet(defense=get_berry_reduction_amount(evs.defense)),
    'Hondew Berry': lambda evs: evs - EvSet(special_attack=get_berry_reduction_amount(evs.special_attack)),
    'Grepa Berry': lambda evs: evs - EvSet(special_defense=get_berry_reduction_amount(evs.special_defense)),
    'Tamato Berry': lambda evs: evs - EvSet(speed=get_berry_reduction_amount(evs.speed)),
    'Perilous Soup': lambda evs: evs * 0,
    'Health Mochi': lambda evs: evs + EvSet(hp=10),
    'Muscle Mochi': lambda evs: evs + EvSet(attack=10),
    'Resist Mochi': lambda evs: evs + EvSet(defense=10),
    'Genius Mochi': lambda evs: evs + EvSet(special_attack=10),
    'Clever Mochi': lambda evs: evs + EvSet(special_defense=10),
    'Swift Mochi': lambda evs: evs + EvSet(speed=10),
    'Fresh-Start Mochi': lambda evs: evs * 0,
}


class EvSet(object):
    STATS = ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']
    LABELS = ['HP', 'Attack', 'Defense', 'Special Attack', 'Special Defense', 'Speed']

    @staticmethod
    def label(stat):
        return EvSet.LABELS[EvSet.STATS.index(stat)]

    def __init__(self, hp=0, attack=0, defense=0, special_attack=0,
                 special_defense=0, speed=0):
        self.hp = int(hp)
        self.attack = int(attack)
        self.defense = int(defense)
        self.special_attack = int(special_attack)
        self.special_defense = int(special_defense)
        self.speed = int(speed)

    def __iadd__(self, other):
        for stat in EvSet.STATS:
            self.__dict__[stat] += other.__dict__[stat]
        return self

    def __add__(self, other):
        evs = self.clone()
        evs += other
        return evs

    def __isub__(self, other):
        for stat in EvSet.STATS:
            self.__dict__[stat] -= other.__dict__[stat]
        return self

    def __sub__(self, other):
        evs = self.clone()
        evs -= other
        return evs

    def __imul__(self, integer):
        for stat in EvSet.STATS:
            self.__dict__[stat] *= integer
        return self

    def __mul__(self, integer):
        evs = self.clone()
        evs *= integer
        return evs

    def capped_add(self, other):
        for stat in EvSet.STATS:
            add_amount = other.__dict__[stat]
            total = self.total_effort()
            total_max = self.max_total_effort()
            if total + add_amount > total_max:
                add_amount = total_max - total
            stat_amount = self.__dict__[stat]
            stat_max = self.max_stat_effort()
            if stat_amount + add_amount > stat_max:
                add_amount = stat_max - stat_amount
            elif stat_amount + add_amount < 0:
                add_amount = -stat_amount

            self.__dict__[stat] += add_amount

    def __str__(self):
        return self.format()

    def format(self, adjustment_amounts=None, targets=None):
        if targets is None:
            targets = EvSet()
        targets = targets.to_dict()
        ev_string = []
        for stat, ev in self.to_dict().items():
            if ev > 0 or targets[stat] > 0:
                ev_label = '%s: %d' % (EvSet.label(stat), ev)
                if adjustment_amounts:
                    adjustment = adjustment_amounts.to_dict()[stat]
                    ev_label += ' (%s%d)' % (
                        ('' if adjustment < 0 else '+'),
                        adjustment
                    )
                if targets[stat] > 0:
                    ev_label += f' (Target: {targets[stat]})'
                ev_string.append(ev_label)
        if not len(ev_string):
            return 'No EVs'
        return '\n'.join(ev_string)

    def as_modifier_string(self):
        ev_string = ['+%d %s' % (ev, EvSet.label(stat)) for stat, ev in self.to_dict().items() if ev > 0]
        return ', '.join(ev_string)

    def clone(self):
        return EvSet(**self.to_dict())

    def to_dict(self):
        dict = {}
        for stat in EvSet.STATS:
            dict[stat] = self.__dict__[stat]
        return dict

    def total_effort(self):
        total = 0
        for stat in EvSet.STATS:
            total += self.__dict__[stat]
        return total

    @staticmethod
    def max_stat_effort():
        return 252 if config.instance.smart_iv_cap() else 255

    @staticmethod
    def max_total_effort():
        return 510


class Species(object):

    def __init__(self, id, name, form, evs=None):
        self.id = int(id)
        self.name = name
        self.form = form
        self.evs = EvSet() if evs is None else evs

    def __str__(self):
        formatted_form = ' (' + self.form + ')' if self.form else ''
        return '#%03d %-10s %s' % (self.id, self.name + formatted_form, self.evs.as_modifier_string())


class Pokemon(object):

    @classmethod
    def from_dict(cls, dict):
        import pokedex
        if 'form' in dict:
            form = dict['form']
            dict['species'] = pokedex.search(dict['species'] + f' ({form})')
        else:
            dict['species'] = list(pokedex.fetch_by_id(dict['species']).values())[0]
            dict['form'] = dict['species'].form
        dict['evs'] = EvSet(**dict['evs'])
        if 'target_evs' in dict:
            dict['target_evs'] = EvSet(**dict['target_evs'])
        return cls(**dict)

    def __init__(
            self,
            id: int,
            species: Species,
            form: str = '',
            name: str = None,
            item: str = None,
            pokerus: bool = False,
            evs: EvSet = None,
            target_evs: EvSet = None
    ):
        self.id = int(id)
        self.species = species
        self.form = form
        self._name = None
        self.name = name
        self._itemName = item
        self._item = None
        self.item = item
        self.pokerus = pokerus
        self.evs = EvSet() if evs is None else evs
        self.target_evs = EvSet() if target_evs is None else target_evs

    def get_individual_id(self) -> int:
        return self.id

    def delete(self):
        self.id = None

    def get_name(self):
        return self.species.name if self._name is None else self._name

    def set_name(self, name):
        if name is not None and len(name.strip()) > 0:
            self._name = name.strip()

    name = property(get_name, set_name)

    def set_item(self, item):
        if item is not None and item not in ITEMS:
            raise ValueError("Invalid item '%s'" % item)
        self._item = ITEMS[item] if item is not None else None
        self._itemName = item

    item = property(lambda self: self._item, set_item)

    def set_effort(self, hp=None, attack=None, defense=None, special_attack=None, special_defense=None, speed=None):
        if hp is not None:
            self.evs.hp = hp
        if attack is not None:
            self.evs.attack = attack
        if defense is not None:
            self.evs.defense = defense
        if special_attack is not None:
            self.evs.special_attack = special_attack
        if special_defense is not None:
            self.evs.special_defense = special_defense
        if speed is not None:
            self.evs.speed = speed

    def set_target(self, hp=None, attack=None, defense=None, special_attack=None, special_defense=None, speed=None):
        if hp is not None:
            self.target_evs.hp = hp
        if attack is not None:
            self.target_evs.attack = attack
        if defense is not None:
            self.target_evs.defense = defense
        if special_attack is not None:
            self.target_evs.special_attack = special_attack
        if special_defense is not None:
            self.target_evs.special_defense = special_defense
        if speed is not None:
            self.target_evs.speed = speed

    def clear_target(self):
        self.target_evs = EvSet()

    def __str__(self):
        name = self.name
        if self._name is not None:
            name = '%s (%s)' % (name, self.species.name)
        if self.id is None:
            return name
        else:
            return '%d %s' % (self.id, name)

    def status(self, location=None):
        status = [str(self)]
        if location:
            status.append(f'Location: {location}')
        if self.pokerus:
            status.append('Pokerus')
        if self._itemName:
            status.append(f'Item: {self._itemName}')
        status.append(self.evs.format(targets=self.target_evs))
        return '\n'.join(status)

    def listing(self, team):
        padding = '* ' if self.id in team else '  '
        return '%s%s' % (padding, self)

    def get_battle_ev_modifier(self, species, number=1):
        """
        Alter's a tracked Pokémon's EVs to simulate having battled a Species.
        These values are altered by pokerus and any item held. The EV
        increment can be multiplied by number to simulate multiple battles.
        """
        evs = species.evs.clone()
        if self.item is not None:
            evs = self.item(evs)
        if self.pokerus and not config.instance.ignore_pokerus():
            evs *= 2
        return evs * number

    def get_vitamin_ev_modifier(self, vitamin, number=1):
        if vitamin not in VITAMINS:
            matches = difflib.get_close_matches(vitamin, VITAMINS)
            if len(matches) == 0:
                raise ValueError("Invalid vitamin '%s'" % vitamin)
            elif len(matches) == 1:
                vitamin = matches.pop()
            else:
                raise ValueError("Ambiguous vitamin '%s'" % vitamin)
        evs = self.evs.clone()
        new_evs = VITAMINS[vitamin](evs)
        return (new_evs - evs) * number

    def to_dict(self):
        return {'species': self.species.id, 'name': self._name,
                'pokerus': self.pokerus, 'item': self._itemName,
                'evs': self.evs.to_dict(), 'id': self.id, 'target_evs': self.target_evs.to_dict()}
