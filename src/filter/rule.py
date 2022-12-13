import logging
from typing import Dict, List

from src.filter.operator import Operator

logger = logging.getLogger(__name__)


class RuleCollection:
    def __init__(self, match_all=True, active=True):
        self.rules: List[tuple] = []
        self.match_all = match_all
        self.active = active

    # define a __dict__ magic method that returns the data to be serialized to JSON
    def __dict__(self):
        return {
            'rules': self.rules,
            'match_all': self.match_all,
            'active': self.active,
        }

    def add(self, element, operator, value, negate=False, active=True):
        self.rules.append((element, operator, value, negate, active))

    def remove(self, element, operator, value, negate=False, active=True):
        self.rules.remove((element, operator, value, negate, active))

    def check(self, source) -> bool:
        if not self.active:
            return True

        result = True
        for element, operator, value, negate, active in self.rules:
            if not active:
                continue
            result = False

            data = source.get(element, "")
            if isinstance(data, list):
                logger.debug(f"Element {element} is a list. This is not supported yet. Check skipped.\n{source}")
                continue

            try:
                is_satisfied = Operator.get_function(operator)(data, value)
            except Exception as e:
                logger.error(f"Error while checking rule {element} {operator} {value}:\n{e}")
                continue

            if negate:
                is_satisfied = not is_satisfied

            if self.match_all:
                if not is_satisfied:
                    return False
            else:
                if is_satisfied:
                    return True

        if self.match_all:
            return True
        return result


class RuleManager:
    def __init__(self):
        self.collections: Dict[str, RuleCollection] = {}

    def __dict__(self):
        return {
                name: collection.__dict__()
                for name, collection in self.collections.items()
        }

    @classmethod
    def from_json(cls, manager_dict):
        # Create a new RuleManager instance
        new_manager = RuleManager()

        # Iterate over the RuleCollection dictionaries in the manager dictionary
        for collection_name, collection_dict in manager_dict.items():
            # Create a new RuleCollection instance from the dictionary
            collection = RuleCollection()
            collection.rules = collection_dict['rules']
            collection.match_all = collection_dict['match_all']
            collection.active = collection_dict['active']

            # Add the RuleCollection instance to the RuleManager instance
            new_manager.add_collection(collection_name, collection)

        return new_manager

    def add_collection(self, name, collection):
        self.collections[name] = collection

    def remove_collection(self, name):
        try:
            self.collections.pop(name)
        except KeyError:
            logger.info(f"Failed to remove collection {name}")

    def check(self, source):
        for collection in self.collections.values():
            if not collection.active:
                continue

            if not collection.check(source):
                return False

        return True
