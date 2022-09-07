#!/usr/local/bin/python
# coding=utf-8


import argparse
import json
import os
import shlex
from shutil import copyfile

import config
import pokedex
from config import Config
from pokemon import Pokemon


class Tracker(object):

    @classmethod
    def from_json(cls, filename):
        tracker = cls()
        tracker.filename = filename
        try:
            fp = open(filename, 'r')
            data = json.load(fp)
            for spec in data['pokemon']:
                pokemon = Pokemon.from_dict(spec)
                tracker.track(pokemon)
            if 'team' in data:
                tracker._team = set(data['team'])
        except IOError:
            pass  # Ignore missing tracking file.

        return tracker

    def to_json(self, filename=None):
        filename = self.filename if filename is None else filename
        fp = open(filename, 'w')
        data = {
            'team': sorted(self._team),
            'pokemon': [pokemon.to_dict() for pokemon in self.pokemon.values()]
        }

        json.dump(data, fp)
        fp.close()

    pokemon = {}

    def __init__(self):
        self._team = set()
        self.counter = 1
        self.filename = None

    def add_to_team(self, individual_id):
        self._team.add(individual_id)

    def on_team(self, individual_id):
        return individual_id in self._team

    def remove_from_team(self, individual_id):
        self._team.remove(individual_id)

    def get_team(self):
        return self._team

    def get_pokemon(self, id):
        if id not in self.pokemon:
            raise NoTrackedPokemon(id)
        return self.pokemon[id]

    def unique_id(self):
        while self.counter in self.pokemon:
            self.counter += 1
        return self.counter

    def track(self, pokemon):
        self.pokemon[pokemon.id] = pokemon

    def untrack(self, pokemon):
        del self.pokemon[pokemon.id]
        pokemon.id = None
        if self.on_team(pokemon.id):
            self.remove_from_team(pokemon.id)

    def __str__(self):
        if len(self.pokemon):
            return '\n'.join([pokemon.listing(self._team) for pokemon in self.pokemon.values()])
        else:
            return 'No tracked Pokemon'


class NoActivePokemon(Exception):
    """
    Raised when an operation that assumes the existence of an active Pokemon
    is carried out and the team is empty.
    """
    pass


class NoTrackedPokemon(Exception):
    """
    Raised when an id is requested from a Tracker but the Tracker does not
    have a Pokemon with the provided id.
    """

    def __init__(self, id):
        super(NoTrackedPokemon, self).__init__()
        self.id = id


_tracker = None


def _save_tracker():
    if os.path.exists(_tracker.filename):
        copyfile(_tracker.filename, _tracker.filename + '.bak')  # Create backup
    _tracker.to_json()


def _cmd_ev(args):
    print(pokedex.search(args.species))


def _cmd_list(args):
    print(_tracker)


def _cmd_track(args):
    species = pokedex.search(args.species)
    pokemon = Pokemon(id=_tracker.unique_id(), species=species,
                      name=args.name, item=args.item, pokerus=args.pokerus)
    _tracker.track(pokemon)
    _save_tracker()
    print(pokemon)


def _cmd_team(args):
    detailed_view = args.detailed
    for individual_id in _tracker.get_team():
        pokemon = _tracker.get_pokemon(individual_id)
        print()
        if detailed_view:
            print(pokemon.status())
        else:
            print(pokemon)


def _cmd_box(args):
    detailed_view = args.detailed
    for individual_id in _tracker.pokemon:
        if not _tracker.on_team(individual_id):
            pokemon = _tracker.get_pokemon(individual_id)
            print()
            if detailed_view:
                print(pokemon.status())
            else:
                print(pokemon)


def _cmd_deposit(args):
    individual_id = args.id
    _tracker.remove_from_team(individual_id)
    _save_tracker()
    print(_tracker.get_pokemon(individual_id))


def _cmd_withdraw(args):
    individual_id = args.id
    _tracker.add_to_team(individual_id)
    _save_tracker()
    print(_tracker.get_pokemon(individual_id))


def _cmd_status(args):
    individual_id = args.id
    pokemon = _tracker.get_pokemon(individual_id)
    location = 'Team' if _tracker.on_team(individual_id) else 'Box'
    print(pokemon.status(location))


def _cmd_update(args):
    individual_id = args.id
    pokemon = _tracker.get_pokemon(individual_id)
    if args.pokerus is True:
        pokemon.pokerus = True
    if args.nopokerus is True:
        pokemon.pokerus = False
    if args.species is not None:
        species = pokedex.search(args.species)
        pokemon.species = species
    if args.item is not None:
        pokemon.item = str(args.item)
    if args.noitem is True:
        pokemon.item = None
    if args.name is not None:
        pokemon.name = str(args.name)
    if args.noname is True:
        pokemon.name = None
    if args.deposit is True:
        _tracker.remove_from_team(individual_id)
    if args.withdraw is True:
        _tracker.add_to_team(individual_id)
    _save_tracker()
    location = 'Team' if _tracker.on_team(individual_id) else 'Box'
    print(pokemon.status(location))


def _cmd_vitamin(args):
    individual_id = args.id
    pokemon = _tracker.get_pokemon(individual_id)
    modifier = pokemon.get_vitamin_ev_modifier(args.vitamin)
    pokemon.evs.capped_add(modifier)
    _save_tracker()
    print(f'{pokemon} new EVs:')
    print(pokemon.evs.format(adjustment_amounts=modifier, targets=pokemon.target_evs))


def _cmd_set_effort(args):
    individual_id = args.id
    pokemon = _tracker.get_pokemon(individual_id)
    pokemon.set_effort(hp=args.hp, attack=args.attack, defense=args.defense, special_attack=args.special_attack,
                       special_defense=args.special_defense, speed=args.speed)
    _save_tracker()
    print(f'{pokemon} new EVs:')
    print(pokemon.evs)


def _cmd_set_target(args):
    individual_id = args.id
    pokemon = _tracker.get_pokemon(individual_id)
    pokemon.set_target(hp=args.hp, attack=args.attack, defense=args.defense, special_attack=args.special_attack,
                       special_defense=args.special_defense, speed=args.speed)
    _save_tracker()
    print(f'{pokemon} new target EVs:')
    print(pokemon.evs.format(targets=pokemon.target_evs))


def _cmd_clear_target(args):
    individual_id = args.id
    pokemon = _tracker.get_pokemon(individual_id)
    pokemon.clear_target()
    _save_tracker()
    print(f'{pokemon} target EVs cleared.')
    print(pokemon.evs.format())


def _cmd_battle(args):
    species = pokedex.search(args.species)
    if args.id is None:
        battling_ids = _tracker.get_team()
        if len(battling_ids) == 0:
            raise NoActivePokemon()
    else:
        battling_ids = set(args.id)

    count = 1 if args.count is None else args.count

    print(f'Battled {count} × {species.name} (#{species.id}) '
          + f'which has a base EV reward of {species.evs.as_modifier_string()}')

    for individual_id in battling_ids:
        pokemon = _tracker.get_pokemon(individual_id)
        modifier = pokemon.get_battle_ev_modifier(species, count)
        pokemon.evs.capped_add(modifier)

        print(f'\n{pokemon} new EVs:')
        print(pokemon.evs.format(adjustment_amounts=modifier, targets=pokemon.target_evs))
    _save_tracker()


def _cmd_release(args):
    pokemon = _tracker.get_pokemon(args.id)
    _tracker.untrack(pokemon)
    _save_tracker()
    print('No longer tracking %s' % pokemon)


def _build_parser():
    parser = argparse.ArgumentParser(prog='ev',
                                     description='''
                                                 A small utility for keeping
                                                 track of Effort Values while
                                                 training Pokemon.
                                                 ''')
    parser.add_argument('--infile', '-i',
                        dest='filename',
                        help='''
                             Optional location of the file to save tracking
                             information to. This defaults to %s in your
                             home directory
                             ''' % config.DEFAULT_TRACKER_FILENAME)

    subparsers = parser.add_subparsers()

    ev_parser = subparsers.add_parser('ev', help='List Effort Values for a Pokemon')
    ev_parser.add_argument('species', help='Name or number of Pokemon species to search for')
    ev_parser.set_defaults(func=_cmd_ev)

    list_parser = subparsers.add_parser('list', help='List tracked Pokemon')
    list_parser.set_defaults(func=_cmd_list)

    track_parser = subparsers.add_parser('track', help='Add a Pokemon to track')
    track_parser.add_argument('species', help='Name of number of Pokemon species to track')
    track_parser.add_argument('--name', '-n', help='Nickname of Pokemon')
    track_parser.add_argument('--pokerus', '-p', action='store_true', default=False,
                              help='Indicates the given Pokemon has Pokerus')
    track_parser.add_argument('--item', '-i')
    track_parser.set_defaults(func=_cmd_track)

    team_parser = subparsers.add_parser('team', help='List the active team Pokemon')
    team_parser.add_argument('--detailed', action='store_true', default=False)
    team_parser.set_defaults(func=_cmd_team)

    box_parser = subparsers.add_parser('box', help='List the boxed Pokemon')
    box_parser.add_argument('--detailed', action='store_true', default=False)
    box_parser.set_defaults(func=_cmd_box)

    deposit_parser = subparsers.add_parser('deposit', help='Send a Pokemon from the team to the box')
    deposit_parser.add_argument('id', type=int, help='Pokemon to deposit')
    deposit_parser.set_defaults(func=_cmd_deposit)

    deposit_parser = subparsers.add_parser('withdraw', help='Send a Pokemon from the box to the team')
    deposit_parser.add_argument('id', type=int, help='Pokemon to withdraw')
    deposit_parser.set_defaults(func=_cmd_withdraw)

    status_parser = subparsers.add_parser('status', help='Show the status of the chosen Pokemon')
    status_parser.add_argument('id', type=int)
    status_parser.set_defaults(func=_cmd_status)

    update_parser = subparsers.add_parser('update', help='Update a tracked Pokemon\'s details')
    update_parser.add_argument('id', type=int, help='Pokemon to update')
    update_parser.add_argument('--species', help='Name or number of Pokemon species')
    update_parser.add_argument('--name', '-n', help='Nickname of Pokemon')
    update_parser.add_argument('--noname', '-nn', action='store_true', default=False)
    update_parser.add_argument('--pokerus', '-p', action='store_true', default=False,
                               help='Indicates the given Pokemon has Pokerus')
    update_parser.add_argument('--nopokerus', '-np', action='store_true', default=False,
                               help='Indicates the given Pokemon does not have Pokerus')
    update_parser.add_argument('--item', '-i')
    update_parser.add_argument('--noitem', '-ni', action='store_true', default=False)
    update_parser.add_argument('--deposit', '-d', action='store_true', default=False,
                               help='Take the pokemon off the team')
    update_parser.add_argument('--withdraw', '-w', action='store_true', default=False,
                               help='Add the pokemon to the team')
    update_parser.set_defaults(func=_cmd_update)

    vitamin_parser = subparsers.add_parser('vitamin', help='Apply a consumable item to a Pokemon')
    vitamin_parser.add_argument('id', type=int, help='Pokemon to apply the vitamin to')
    vitamin_parser.add_argument('vitamin', help='Item to apply')
    vitamin_parser.set_defaults(func=_cmd_vitamin)

    set_effort_parser = subparsers.add_parser('set_effort', help='Update a tracked Pokemon\'s effort values')
    set_effort_parser.add_argument('id', type=int, help='Pokemon to update')
    set_effort_parser.add_argument('--hp', type=int, help='HP effort')
    set_effort_parser.add_argument('--attack', type=int, help='Attack effort')
    set_effort_parser.add_argument('--defense', type=int, help='Defense effort')
    set_effort_parser.add_argument('--special_attack', type=int, help='Special Attack effort')
    set_effort_parser.add_argument('--special_defense', type=int, help='Special Defense effort')
    set_effort_parser.add_argument('--speed', type=int, help='Speed effort')
    set_effort_parser.set_defaults(func=_cmd_set_effort)

    set_target_parser = subparsers.add_parser('set_target', help='Update a tracked Pokemon\'s target effort values')
    set_target_parser.add_argument('id', type=int, help='Pokemon to update')
    set_target_parser.add_argument('--hp', type=int, help='HP effort')
    set_target_parser.add_argument('--attack', type=int, help='Attack effort')
    set_target_parser.add_argument('--defense', type=int, help='Defense effort')
    set_target_parser.add_argument('--special_attack', type=int, help='Special Attack effort')
    set_target_parser.add_argument('--special_defense', type=int, help='Special Defense effort')
    set_target_parser.add_argument('--speed', type=int, help='Speed effort')
    set_target_parser.set_defaults(func=_cmd_set_target)

    clear_target_parser = subparsers.add_parser('clear_target', help='Clear a tracked Pokemon\'s target effort values')
    clear_target_parser.add_argument('id', type=int, help='Pokemon to update')
    clear_target_parser.set_defaults(func=_cmd_clear_target)

    battle_parser = subparsers.add_parser('battle', help='Record a battle for a tracked Pokemon')
    battle_parser.add_argument('species', help='Name of number of Pokemon species to battle')
    battle_parser.add_argument('--id', '-i', type=int)
    battle_parser.add_argument('--count', '-c', type=int)
    battle_parser.set_defaults(func=_cmd_battle)

    release_parser = subparsers.add_parser('release', help='Stop tracking a Pokemon')
    release_parser.add_argument('id', type=int)
    release_parser.set_defaults(func=_cmd_release)

    return parser


def execute_command(args):
    global _tracker
    try:
        config_instance = Config.from_json(args.filename)
        config.instance = config_instance
        Config.to_json(config_instance)
        _tracker = Tracker.from_json(config_instance.filename)
        args.func(args)
        print()
    except pokedex.NoSuchSpecies as e:
        print("No match found for '%s'." % e.identifier)
        if isinstance(e, pokedex.AmbiguousSpecies):
            print("Did you mean:")
            for match in e.matches:
                print("  %s" % match)
    except NoActivePokemon:
        print("No tracked Pokemon is on the team.")
        print("Add a pokemon to the team using the 'withdraw <id>' command.")
    except NoTrackedPokemon as e:
        print("No tracked Pokemon with id '%d' was found." % e.id)


def repl() -> None:
    try:
        while True:
            try:
                _in = input(">> ")
                args = _build_parser().parse_args(shlex.split(_in))
                execute_command(args)
            except Exception as e:
                print(f"Error: {e}")
    except KeyboardInterrupt as e:
        print("\nExiting...")


if __name__ == '__main__':
    repl()
